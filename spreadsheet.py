import os.path
import urllib.parse
import re
import requests
import csv
import gspread
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

SCOPES = ['https://www.googleapis.com/auth/drive']

creds = None
service = None
client = None
SPREADSHEET_ID = '1vI_ho-gpw4xq_VTRyTMB3DdNAytWdckrDANbJ1BEcMU'

def init_service():
    global creds
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    global service
    service = build('sheets', 'v4', credentials=creds)
    
    global client
    client = gspread.authorize(creds)

    print('Done initializing service')

# Download the spreadsheet from Google Drive
def fetch_spreadsheet():
    result = service.spreadsheets().get(spreadsheetId = SPREADSHEET_ID).execute()
    urlParts = urllib.parse.urlparse(result['spreadsheetUrl'])
    path = re.sub("\/edit$", '/export', urlParts.path)
    urlParts = urlParts._replace(path=path)
    headers = {
    'Authorization': 'Bearer ' + creds.token,
    }
    for sheet in result['sheets']:

        if not sheet['properties']['sheetId'] == 78752082:
            continue

        params = {
            'id': SPREADSHEET_ID,
            'format': 'tsv',
            'gid': sheet['properties']['sheetId'],
        }

        queryParams = urllib.parse.urlencode(params)
        urlParts = urlParts._replace(query=queryParams)
        url = urllib.parse.urlunparse(urlParts)
        response = requests.get(url, headers = headers)

        filePath = './table.tsv'

        if (os.path.exists(filePath)):
            os.remove(filePath)

        with open(filePath, 'wb') as csvFile:
            csvFile.write(response.content)
        
    print('Done fetching spreadsheet')

# Insert the sheet into the existing spreadsheet
def insert_sheet(path):
    sh = client.open_by_key(SPREADSHEET_ID)
    sh.values_update(
        "MAST Data",
        params={'valueInputOption': 'USER_ENTERED'},
        body={
            'values': list(csv.reader(open(path), delimiter='\t'))
        })
    
    print('Inserted sheet under "MAST Data"')

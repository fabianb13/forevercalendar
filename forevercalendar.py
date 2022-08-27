import calendar
from itertools import count
import os, sys
import datetime
import pathlib

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']

def google_calendar(argv):
    """Shows basic usage of the Google Calendar API.
    Prints the start and name of the next 10 events on the user's calendar.
    """
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file(pathlib.Path(__file__).parent / 'token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                pathlib.Path(__file__).parent / 'client_secrets.json', SCOPES)
            creds = flow.run_local_server(access_type='offline', include_granted_scopes='true')
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    try:
        service = build('calendar', 'v3', credentials=creds)

        # Call the Calendar API
        now = datetime.datetime.utcnow().isoformat() + 'Z'  # 'Z' indicates UTC time
        print('Getting the upcoming 10 events')
        #events_result = service.events().list(calendarId='primary', timeMin=now,
        #                                      maxResults=20, singleEvents=True,
        #                                      orderBy='startTime').execute()
        events_result = service.events().list(calendarId='ada7nqlvq2fogdu58ffg2k9h2o@group.calendar.google.com', timeMin=now,
                                                maxResults=20, singleEvents=True,
                                                orderBy='startTime').execute()
        events = events_result.get('items', [])

        if not events:
            print('No upcoming events found.')
            return

        # Prints the start and name of the next 10 events
        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            print(start, event['summary'])

    except HttpError as error:
        print('An error occurred: %s' % error)

def generate_html():
    template = None
    with open(os.path.join(sys.path[0],"calendar_template.html"), 'r') as file:
        template = file.read()

    cal = calendar.Calendar()

    currentMonth = datetime.datetime.now().month
    currentYear = datetime.datetime.now().year
    month_list = [month % 13 for month in range(currentMonth, currentMonth+13)]
    html_string = ""
    for month in month_list:
        count = 0
        if month == 0:
            # 0 indicates that the calendar has rolled over to the next yer
            currentYear += 1
            continue
        month_abbr = calendar.month_abbr[month]
        print(month_abbr, end=" ")
        html_string += "<tr>\n"
        html_string += f"<th class='calendar-header'>{month_abbr}</th>"
        for day in cal.itermonthdays(currentYear, month):
            if day == 0:
                continue
            print(day, end=" ")
            html_string += f"<td>{day}</td>"
            count += 1
        for i in range(count, 31):
            print("-", end=" ")
            html_string += f"<td>-</td>"
        print("\n", end="")
        html_string += "</tr>\n"

    html_out = template.replace("<!--{calendar_body}-->", html_string)

    with open(os.path.join(sys.path[0],"calendar.html"), 'w') as html_file:
        html_file.write(html_out)


def main(argv):
    google_calendar(argv)
    generate_html()

if __name__ == '__main__':
    main(sys.argv)
import calendar
import os, sys
import datetime
import pathlib
import json

# 3rd Party Imports
# pip install google-api-python-client
# pip install google-auth-oauthlib
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']

def google_calendar_events(startDate : datetime.datetime):
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
        #timeMin = now
        timeMin = startDate.isoformat() + 'Z'
        events_result = service.events().list(calendarId='ada7nqlvq2fogdu58ffg2k9h2o@group.calendar.google.com', timeMin=timeMin,
                                                maxResults=20, singleEvents=True,
                                                orderBy='startTime').execute()
        events = events_result.get('items', [])

        if not events:
            print('No upcoming events found.')
            return

        # Prints the start and name of the next 10 events
        #for event in events:
        #    start = event['start'].get('dateTime', event['start'].get('date'))
        #    print(start, event['summary'])
        return events

    except HttpError as error:
        print('An error occurred: %s' % error)

def isEventActive(event : dict, dt : datetime.datetime):
    startDate = datetime.datetime.strptime(event['start']['date'], '%Y-%m-%d').date()
    endDate = datetime.datetime.strptime(event['end']['date'], '%Y-%m-%d').date()
    return startDate <= dt.date() and endDate >= dt.date()

def generate_html():
    template = None
    with open(os.path.join(sys.path[0],"calendar_template.html"), 'r') as file:
        template = file.read()

    cal = calendar.Calendar()

    currentMonth = datetime.datetime.now().month
    currentYear = datetime.datetime.now().year
    month_list = [month % 13 for month in range(currentMonth, currentMonth+13)]
    html_string = ""
    dt = datetime.datetime(currentYear, currentMonth, 1)
    dtnow = datetime.datetime.now()
    try:
        events = google_calendar_events(dt)
        # cache the events for offline debug
        with open("event_cache.json", "w") as file:
            events_string = json.dumps(events, indent=4)
            file.write(events_string)
    except:
        print("google_calendar_events failed, using cache")
        # load the event cache if online fetch failed
        with open("event_cache.json", "r") as file:
            events = json.load(file)

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
            dayStr = ''
            dt = datetime.datetime(currentYear, month, day)
            if (dt.date() == dtnow.date()):
                print(' *', end=" ")
            else:
                print(f"{day:2}", end=" ")
            for event in events:
                if isEventActive(event, dt):
                    dayStr = f"<div>{event['summary']}</div>"
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
    generate_html()

if __name__ == '__main__':
    main(sys.argv)
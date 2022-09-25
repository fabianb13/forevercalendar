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
SCOPES = [
    'https://www.googleapis.com/auth/calendar.readonly',
    'https://www.googleapis.com/auth/calendar']

def fetchColors(service):
    try:
        colors = service.colors().get().execute()
        # cache the events for offline debug
        with open("colors_cache.json", "w") as file:
            colors_string = json.dumps(colors, indent=4)
            file.write(colors_string)
    except:
        print("fetchColors failed, using cache")
        # load the event cache if online fetch failed
        with open("colors_cache.json", "r") as file:
            colors = json.load(file)
    return colors

def fetchEvents(service, startDate : datetime.datetime, calendarId):
    try:
        # Call the Calendar API
        now = datetime.datetime.utcnow().isoformat() + 'Z'  # 'Z' indicates UTC time
        print('Getting the upcoming 10 events')
        #events_result = service.events().list(calendarId='primary', timeMin=now,
        #                                      maxResults=20, singleEvents=True,
        #                                      orderBy='startTime').execute()
        #timeMin = now
        timeMin = startDate.isoformat() + 'Z'
        events_result = service.events().list(calendarId=calendarId, timeMin=timeMin,
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


def google_auth():
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
    service = build('calendar', 'v3', credentials=creds)
    return service


def isEventActive(event : dict, dt : datetime.datetime):
    startDate = datetime.datetime.strptime(event['start']['date'], '%Y-%m-%d').date()
    endDate = datetime.datetime.strptime(event['end']['date'], '%Y-%m-%d').date()
    if startDate == dt.date():
        return True
    elif startDate <= dt.date() and endDate >= dt.date() and dt.date().day == 1:
        return True

def getEventNumDays(event : dict, dt : datetime.datetime):
    """
    Get the number of days to display for this event on the current month.
    """
    startDate = datetime.datetime.strptime(event['start']['date'], '%Y-%m-%d').date()
    endDate = datetime.datetime.strptime(event['end']['date'], '%Y-%m-%d').date()
    cal = calendar.Calendar()
    monthdays = [day for day in cal.itermonthdays(dt.year, dt.month) if day != 0]
    if startDate.month == endDate.month:
        # Event is entirely withing the current month
        return (endDate - startDate).days
    elif startDate == dt.date():
        # Event spans across months, but current request is for the first month
        return (datetime.date(startDate.year, startDate.month, monthdays[-1]) - startDate).days + 1
    elif endDate.month != dt.date().month:
        return monthdays[-1]
    else:
        return endDate.day

def getEventSlot(events : list, dt : datetime.datetime):
    slots = [0, 1, 2]
    for event in events:
        startDate = datetime.datetime.strptime(event['start']['date'], '%Y-%m-%d').date()
        endDate = datetime.datetime.strptime(event['end']['date'], '%Y-%m-%d').date()
        if startDate <= dt.date() and endDate >= dt.date() and 'slot' in event:
            slot = event['slot']
            slots.remove(slot)
    if len(slots) != 0:
        return slots[0]
    else:
        return None

def generate_html():
    template = None
    with open(os.path.join(sys.path[0],"calendar_template.html"), 'r') as file:
        template = file.read()

    cal = calendar.Calendar()

    currentMonth = datetime.datetime.now().month
    currentYear = datetime.datetime.now().year
    month_list = [month % 13 for month in range(currentMonth, currentMonth+13)]
    cal_body = ""
    cal_overlay = ""
    dt = datetime.datetime(currentYear, currentMonth, 1)
    dtnow = datetime.datetime.now()
    try:
        service = google_auth()
        colors = fetchColors(service)
        events = fetchEvents(service, dt, 'ada7nqlvq2fogdu58ffg2k9h2o@group.calendar.google.com')
        # cache the events for offline debug
        with open("event_cache.json", "w") as file:
            events_string = json.dumps(events, indent=4)
            file.write(events_string)
    except Exception as e:
        print("google_calendar_events failed, using cache")
        # load the event cache if online fetch failed
        with open("event_cache.json", "r") as file:
            events = json.load(file)
    # Generate the calendar date header
    cal_body += "<tr>\n"
    cal_body += "<th class='calendar-header'>-</th>\n"
    for i in range(1, 32):
        attrib = ""
        try:
            # Highlight the current date on the header
            dt = datetime.datetime(currentYear, currentMonth, i)
            if (dt.date() == dtnow.date()):
                attrib = f" style='background: lightsteelblue;'"
        except:
            pass
        cal_body += f"<th class='calendar-header'{attrib}>{i}</th>\n"
    cal_body += "</tr>\n"

    # Generate the calendar body
    for month in month_list:
        count = 0
        if month == 0:
            # 0 indicates that the calendar has rolled over to the next year
            currentYear += 1
            continue
        month_abbr = calendar.month_abbr[month]
        print(month_abbr, end=" ")
        cal_body += "<tr>\n"
        cal_body += f"<th class='calendar-header'>{month_abbr}</th>"
        cal_overlay += "<div class='overlay-row'>\n"
        cal_overlay += "<div class='overlay-cell'></div>"
        for day in cal.itermonthdays(currentYear, month):
            if day == 0:
                continue
            day_content = ''
            dt = datetime.datetime(currentYear, month, day)
            if (dt.date() == dtnow.date()):
                print(' *', end=" ")
            else:
                print(f"{day:2}", end=" ")
            for event in events:
                if isEventActive(event, dt):
                    numDays = getEventNumDays(event, dt)
                    div_width = 100 * numDays
                    if 'slot' not in event:
                        slot = getEventSlot(events, dt)
                        event['slot'] = slot
                    else:
                        slot = event['slot']
                    if 'colorId' in event:
                        foreground = colors['event'][event['colorId']]['foreground']
                        background = colors['event'][event['colorId']]['background']
                    else:
                        foreground = "black"
                        background = "rgba(26, 4, 222, .75)"

                    if slot is not None:
                        vert_pos = slot * 33.3333
                        day_content += f"<div class='overlay-cell-content' style='width: {div_width}%; top: {vert_pos}%; color: {foreground}; background: {background};'>{event['summary']}</div>"
            cal_body += f"<td></td>"
            cal_overlay += f"<div class='overlay-cell'>{day_content}</div>"
            count += 1
        for i in range(count, 31):
            print("-", end=" ")
            cal_body += f"<td style='background: dimgrey'></td>"
            cal_overlay += "<div class='overlay-cell'></div>"
        print("\n", end="")
        cal_body += "</tr>\n"
        cal_overlay += "</div>\n"

    html_out = template.replace("<!--{calendar_body}-->", cal_body)
    html_out = html_out.replace("<!--{calendar_overlay}-->", cal_overlay)

    with open(os.path.join(sys.path[0],"calendar.html"), 'w') as html_file:
        html_file.write(html_out)


def main(argv):
    generate_html()

if __name__ == '__main__':
    main(sys.argv)
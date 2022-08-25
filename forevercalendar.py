import calendar
from itertools import count
import os, sys
from datetime import datetime


template = None
with open(os.path.join(sys.path[0],"calendar_template.html"), 'r') as file:
    template = file.read()

cal = calendar.Calendar()

currentMonth = datetime.now().month
currentYear = datetime.now().year
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


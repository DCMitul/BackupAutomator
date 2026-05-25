import shutil
import os
import logging
import datetime
import json

from pathlib import Path

try:
    import send2trash
except:
    print("The 'send2trash' module is not installed. Please install it using 'pip install send2trash' and try again. If issue still persists, try reinstalling the module.")
    exit()


# Breaking the input into seperate elements
def break_input(inp):
    global mainfile, backupfile, time

    parts = inp.split(";")

    if len(parts) != 3:
        print("Invalid format.")
        return False

    mainfile = parts[0]
    backupfile = parts[1]
    time = parts[2]


# Verifying if the inputs are valid
def check_inputs(mainfile, backupfile, time):
    mainfile = Path(mainfile)
    backupfile = Path(backupfile)
    if not Path(mainfile).exists():
        print("The file path you specified does not exist. Please check the path and try again.")
        mainfile = ""
    elif not Path(backupfile).exists():
        print("The backup file path you specified does not exist. Please check the path and try again.")
        backupfile = ""
    elif not time.endswith(('mm', 'm', 'h', 'd', 's')):
        print("The time period you specified is not in the correct format. Please check the format and try again.")
        time = ""
    else:
        return 'ok'
    

# Converting the time period into seconds for easier calculations
def convert_duration(time1):
    if time1.endswith('s'):
        return int(time1[:-1])
    elif time1.endswith('mm'):
        return int(time1[:-1]) * 2592000
    elif time1.endswith('h'):
        return int(time1[:-1]) * 3600
    elif time1.endswith('d'):
        return int(time1[:-1]) * 86400
    elif time1.endswith('m'):
        return int(time1[:-2]) * 60
    else:
        return "err"

# Stating the variables
pth = ""
global mainfile, backupfile, time
mainfile = ""
backupfile = ""
time = ""

print("Below, enter the path of the file(s) or folder(s) you want to keep backup up, the place where you want to back them up to(leave empty for default), and the time period of each backup(s for seconds, m for minutes, h for hours, d for days and mm for months(months are considered as 30 days)). Seperate each element with a semi-colon.")
print("Example format: C:/Users/JohnDoe/Documents;D:/Backups;5d")
print("The above format is case-sensitive, make sure the paths and the indicator for the time(s/m/h/d/mm) are correct and strictly according to the format. DO NOT PUT SPACES AFTER THE SEMI-COLONS. When you are done, type 'done' to exit.")
print("Tip: Keeping the time intervals very differnet from each other can result in increased usage of resources; try to keep them all in whole hours/days at least to prevent the system performance loss.")

while pth.lower() != 'done':
    pth = input(">>>> ")
    if pth.lower() == 'done':
        break
    else:
        break_input(pth)
        if check_inputs(mainfile, backupfile, time) == 'ok':
            duration = convert_duration(time)
            if duration == "err":
                print("There is a problem with the time period you specified. Please check the format and other details before trying again. If the problem persists, raise an issue on the GitHub repository.")
                continue
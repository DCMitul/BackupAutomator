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
    global mainfile, backupfile, time, exclusion, exclusions

    parts = inp.split(";")

    if len(parts) == 4:
        exclusion = True
        exclusions = parts[3].split(",")
    elif len(parts) != 3:
        print("Invalid format.")
        return False

    mainfile = parts[0]
    backupfile = parts[1]
    time = parts[2]


# Verifying if the inputs are valid
def check_inputs(mainfile, backupfile, time, exclusion, exclusions):
    mainfile = Path(mainfile)
    backupfile = Path(backupfile)
    if exclusion:
        for i in exclusions:
            if not Path(i).exists():
                print("The exclusion file/folder path", i, "does not exist. Please check the path and try again.")
                exclusions = []
                return False
    if not Path(mainfile).exists():
        print("The file path you specified does not exist. Please check the path and try again.")
        mainfile = ""
    elif not Path(backupfile).exists():
        print("The backup file path you specified does not exist. Please check the path and try again.")
        backupfile = ""
    elif not time.endswith(('mm', 'm', 'h', 'd', 's')):
        print(time)                  #Debug code, remove later
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
global mainfile, backupfile, time, exclusion, exclusions
mainfile = ""
backupfile = ""
time = ""
exclusion = False
exclusions = []

# The actual program that gets the inputs

print("""
# ···················································································
# :.................................................................................:
# :..╦.╦┌─┐┬..┌─┐┌─┐┌┬┐┌─┐..┌┬┐┌─┐..╔╗.┌─┐┌─┐┬┌─┬.┬┌─┐╔═╗┬.┬┌┬┐┌─┐┌┬┐┌─┐┌┬┐┌─┐┬─┐┬..:
# :..║║║├┤.│..│..│.││││├┤....│.│.│..╠╩╗├─┤│..├┴┐│.│├─┘╠═╣│.│.│.│.││││├─┤.│.│.│├┬┘│..:
# :..╚╩╝└─┘┴─┘└─┘└─┘┴.┴└─┘...┴.└─┘..╚═╝┴.┴└─┘┴.┴└─┘┴..╩.╩└─┘.┴.└─┘┴.┴┴.┴.┴.└─┘┴└─o..:
# :.................................................................................:
# ···················································································
""")
print("Art made using ASCII Art Archive(https://www.asciiart.eu/)")
print("Welcome to BackupAutomator! This program allows you to automate the process of backing up your files and folders at specified intervals. You can specify the file(s) or folder(s) you want to back up, the location where you want to back them up to, and the time period for each backup. The program will then automatically create backups at the specified intervals, ensuring that your important data is always safe and up-to-date.")
print("")
print("Below, enter the path of the file(s) or folder(s) you want to keep backup up, the place where you want to back them up to(leave empty for default), and the time period of each backup(s for seconds, m for minutes, h for hours, d for days and mm for months(months are considered as 30 days)). If the selected source is a folder and you want to exclude any files/folders that are within the source folder, add the paths for the exclusions, seperated by ',', after the time period. Seperate each element with a semi-colon.")
print("Example format: C:/Users/JohnDoe/Documents;D:/Backups;5d;C:/Users/JohnDoe/Documents/SecretFolder,C:/Users/JohnDoe/Documents/SecretFile.txt")
print("The above format is case-sensitive, make sure the paths and the indicator for the time(s/m/h/d/mm) are correct and strictly according to the format. DO NOT PUT SPACES AFTER THE SEMI-COLONS. When you are done, type 'done' to exit.")
print("Tip: Keeping the time intervals very differnet from each other can result in increased usage of resources; try to keep them all in whole hours/days at least to prevent the system performance loss.")


while pth.lower() != 'done':
    pth = input(">>>> ")
    if pth.lower() == 'done':
        print("Thank you for using BackupAutomator! If there were any issues please raise an issue on the GitHub repository or contact me. Have a great day(or night, perhaps!)!")
        break
    else:
        break_input(pth)
        print("before check inputs", mainfile, backupfile, time, exclusion, exclusions)                          #Debug code, remove later
        if check_inputs(mainfile, backupfile, time, exclusion, exclusions) == 'ok':
            duration = convert_duration(time)
            if duration == "err":
                print("There is a problem with the time period you specified. Please check the format and other details before trying again. If the problem persists, raise an issue on the GitHub repository.")
                continue
            else:
                print("As per the recieved input, the folder/file at", mainfile, "will be backed up to", backupfile, "every", time, "that is, every", duration, "seconds.")
                print("If this is correct, please confirm by typing 'yes' or 'y'. If there are any mistakes, please type 'no' or 'n'.")
                while True:
                    verify = input(">>>> ")
                    if verify.lower() in ['yes', 'y']:
                        print("Confirmed")
                        break
                    elif verify.lower() in ['no', 'n']:
                        print("Please renter the details correctly =).")
                        break
                    else:
                        print("Invalid input. Please type 'yes' or 'y' to confirm, or 'no' or 'n' to reject.")
                if verify.lower() in ['no', 'n']:
                    continue
                
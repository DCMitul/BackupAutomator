# The libraries
import json
import os
import sys
from pathlib import Path
import time
import sqlite3

try:
    from InquirerPy import inquirer
except:
    print("The library 'InquirerPy' is not present, install it using 'pip install InquirerPy' to proceed.")
    sys.exit()

try:
    from tabulate import tabulate
except:
    print("The library 'tabulate' is not present, install it using 'pip install tabulate' to proceed.")
    sys.exit()


def check_config():
    if not os.path.exists("config.json"):
        temp = {
            "first": True,
            "backuploc": "",
            "timeperiod": "",
            "logging": False,
            "DB": "jobs.db"
        }

        with open("config.json", "w") as f:
            json.dump(temp, f, indent=4)
        
        return(True)
    else:
        return(True)


# For reading from/updating the config. Don't ask me why 'h'config
def hconfig(action,key,value=None):
    if check_config():
        with open("config.json", "r") as f:
            temp = json.load(f)

        if action == 'read':
            return temp.get(key)
        elif action == 'change':
            temp[key] = value
            with open("config.json", "w") as f:
                json.dump(temp, f, indent=4)
        else:
            print("invalid input for action", action)


def check_base():
    conn = sqlite3.connect(hconfig("read","DB"))
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            job_id INTEGER PRIMARY KEY AUTOINCREMENT,
            source TEXT NOT NULL,
            destination TEXT NOT NULL,
            time TEXT NOT NULL,
            duration INTEGER NOT NULL,
            exceptions TEXT
        )
    """)

    conn.commit()
    conn.close()


def addtodb(source,destination,time,duration,exeption):
    conn = sqlite3.connect(hconfig("read","DB"))
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO jobs (source, destination, time, duration, exceptions)
        VALUES (?, ?, ?, ?, ?)
    """, (source, destination, time, duration, exeption)
    )

    cursor = cursor.lastrowid
    
    conn.commit()
    conn.close()

    return cursor


def editdb(row,source,destination,time,duration,exeption):
    conn = sqlite3.connect(hconfig('read','DB'))
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE jobs
        SET source = ?, destination = ?, time = ?, duration = ?, exceptions = ?
        WHERE job_id = ?
    """, (
        source,
        destination,
        time,
        duration,
        exeption,
        row
    ))

    conn.commit()
    conn.close()


def getfromdb(action,row=None):
    conn = sqlite3.connect(hconfig("read","DB"))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    if action.lower() == 'all':
        cursor.execute("SELECT * FROM jobs")
        result = cursor.fetchall()
    elif action.lower() == 'one':
        cursor.execute("SELECT * FROM jobs WHERE job_id = ?", (row,))
        result = cursor.fetchone()
    elif action.lower() == "last":
        cursor.execute("""
            SELECT * FROM jobs
            ORDER BY job_id DESC
            LIMIT 1
        """)
        result = cursor.fetchone()
    else:
        result = ""
        print("action shoudl be either all or one")
        sys.exit()

    conn.close()
    if result is None:
        return None
    elif action.lower() == "all":
        return [dict(row) for row in result]
    else:
        return dict(result)


def printjob(rows):

    if isinstance(rows, dict):

        table = [{
            "Job ID": rows["job_id"],
            "Source": rows["source"],
            "Destination": rows["destination"],
            "Time": rows["time"],
            "Excluded": "\n".join(json.loads(rows["exceptions"]))
                         if json.loads(rows["exceptions"])
                         else "None"
        }]

    elif isinstance(rows, list):

        table = []

        for job in rows:
            table.append({
                "Job ID": job["job_id"],
                "Source": job["source"],
                "Destination": job["destination"],
                "Time": job["time"],
                "Excluded": len(json.loads(job["exceptions"]))
            })

    else:
        print("No jobs found.")
        return

    print(tabulate(table, headers="keys", tablefmt="rounded_grid"))


def inquircnfrm(message,defau):
    return inquirer.confirm(
        message=message,
        default=defau
    ).execute()

def inquirinp(message,defau):
    return inquirer.text(
        message=message,
        default=defau
    ).execute()


def checkdef(key,value):
    if hconfig("read",key) == value:
        print("Done!")
        return True
    else:
        print("There was some error, please try again. If the error persists, raise an issue on github or message me directly.")
        return False


def convert_time(input):
    if input.endswith('mm'):
        return float(input[:-2]) * (2592000/60)
    elif input.endswith('h'):
        return float(input[:-1]) * 60
    elif input.endswith('d'):
        return float(input[:-1]) * (86400/60)
    elif input.endswith('m'):
        return float(input[:-1]) * 1
    else:
        return False


def first():
    if hconfig("read","first"):
        print("Oh so it's your first time using this program? Well lets start with the deafults then!")
        firstdefault()
        print("Now lets take you to the main menu you will see everytime you run this program. There you will pick what you want to do next :)")

    hconfig("change","first",False)


def firstdefault():
    print("Let's first set the default backup location! Keep in mind that the defaults are just for the sake of convinience, and you can use any other values(eg the value for the backup path) in palce of the preset defaults anytime!")
    defbackuploc()
    print("Now, lets set up the default time period that each backup will happen after!")
    deftimeperiod()
    print("Now lets confirm the logging options.")
    deflogging()
    print("That is all the defaults set! If you ever want to change these, pick the 'edit defaults' option from the main menu.")


def defbackuploc():
    print("Please specify the full path and keep in mind that paths are case-sensitive.")
    while True:
        temp = str(inquirinp("Please enter the default backup path",hconfig("read","backuploc")))
        if not Path(temp).exists():
            print("Oops, the path you specified does not exist. Please recheck and try again.")
            continue
        else:
            print("The path you specified is", temp)
            if inquircnfrm("Is the given path correct?",True):
                print("The provided path is being set as the default...")
                hconfig('change',"backuploc",temp)
                if not checkdef('backuploc',temp):
                    continue
                else:
                    break
            else:
                print("Please retry")
                continue


def deftimeperiod():
    print("Please enter the defautl time period you want for any backup. Use 'm' for minutes, 'h' for hours, 'd' for days, 'mm' for months(one month is considered as 30days); the given units are case-sensitive.")
    print("For example, '5d' will be 5 days, '1mm' will be 30 days, etc.")
    while True:
        temp = inquirinp("Please enter the time period","")
        if convert_time(temp) == False:
            print("The time period you entered is invalid. Please try again")
            continue
        else:
            print("The time period you entered is", temp, "or", convert_time(temp), "minutes.")
            if inquircnfrm("Is the gievn time period correct?",True):
                print("The default time period is being saved...")
                hconfig("change",'timeperiod',temp)
                if not checkdef('timeperiod',temp):
                    continue
                else:
                    break

            else:
                print("Please try again")
                continue


def deflogging():
    while True:
        templ = inquircnfrm("Do you want logging enabaled?",True)
        if templ:
            hconfig("change",'logging',True)
            if not checkdef('logging',True):
                continue
            else:
                break
        else:
            hconfig("change",'logging',False)
            if not checkdef('logging',False):
                continue
            else:
                break

    
def mmenu():
    action = inquirer.select(
        message="Main Menu",
        choices=[        
        {"name": "Add backup job", "value": "add"},
        {"name": "View/Edit jobs", "value": "view"},
        {"name": "Settings", "value": "sett"},
        {"name": "Exit", "value": "exit"}]
    ).execute()
    
    if action == "exit":
        print("Exiting now...")
        time.sleep(3)
        sys.exit()
    elif action == "sett":
        settings()
    elif action == "add":
        addjb()
        mmenu()
    elif action == "view":
        viewjb()


def settings():
    sett = inquirer.select(
        message="Settings",
        choices=[
            {"name": "Edit defaults", "value": "defa"},
            {"name": "Back", "value": "bck"}
        ]
    ).execute()
    
    if sett == "bck":
        mmenu()
    elif sett == "defa":
        defa = inquirer.select(
            message="Which default do you want to change?",
            choices=[
                {"name": "Backup Path", "value": "backuploc"},
                {"name": "Time Period", "value": "time"},
                {"name": "Logging", "value": "logg"},
                {"name": "Back", "value": "bck"}
            ]
        ).execute()

        if defa == "bck":
            defa = ""
        elif defa == "backuploc":
            defbackuploc()
        elif defa == "time":
            deftimeperiod()
        elif defa == "logg":
            deflogging()

        settings()

                
def addjb():
    while True:
        flpth = inquirinp("First, enter the path of the file/folder you want to keep backed up","")
        if Path(flpth).exists():
            print("The path you provided is", flpth)
            if inquircnfrm("Is the given path correct?",True):
                print("The path has been recorded.")
                break
            else:
                print("Please try again")
                continue
        else:    
            print("The given path does not exist, please try again.")
            continue

    while True:
        bkpth = inquirinp("Now, enter the location of the place you want to keep the backup in",hconfig("read","backuploc"))
        if Path(bkpth).exists():
            print("The path you provided is", bkpth)
            if inquircnfrm("Is the given path correct?",True):
                    print("The path has been recorded.")
                    break
            else:
                print("Please try again")
                continue
        else:    
            print("The given path does not exist, please try again.")
            continue

    while True:
        tim = inquirinp("Now enter the time period you want between each backup. Use 'm' for minutes, 'h' for hours, 'd' for days, 'mm' for months(one month is considered as 30days); the given units are case-sensitive.",hconfig('read','timeperiod'))
        if convert_time(tim) == False:
            print("The time period you entered is invalid. Please try again")
            continue
        else:
            print("The time period you entered is", tim, "or", convert_time(tim), "minutes.")
            if inquircnfrm("Is the gievn time period correct?",True):
                print("The time period has been recorded")
                break

            else:
                print("Please try again")
                continue

    if inquircnfrm("Do you have any files/folders within the given folder that you want to exclude from the backup?(Pick no if the thing you want to backup is a file)",False):
        exceptions = []
        print("Please enter the path(s) of the exception(s). Type 'done' once you're finished")
        while True:
            temp = inquirinp('>>',"")
            if temp.lower() == 'done':
                break
            elif Path(temp).exists():
                if temp in exceptions:
                    print("The item given is already once provided.")
                else:
                    exceptions.append(temp)
            else:
                print("The path you entered does not exist, try again.")

            continue
        
        print("The exeptions have been recorded.")
    else:
        exceptions = []
        pass
    
    exceptions = json.dumps(exceptions)

    print("That was all! Adding the job to the database :)")
    temp = addtodb(flpth,bkpth,tim,convert_time(tim),exceptions)
    print("The job was added with the jobid as", temp, ". Also printing the job row...")
    printjob(getfromdb("one",temp))


def editjb(row):
    while True:
        flpth = inquirinp("First, enter the path of the file/folder you want to keep backed up",row['source'])
        if Path(flpth).exists():
            print("The path you provided is", flpth)
            if inquircnfrm("Is the given path correct?",True):
                print("The path has been recorded.")
                break
            else:
                print("Please try again")
                continue
        else:    
            print("The given path does not exist, please try again.")
            continue

    while True:
        bkpth = inquirinp("Now, enter the location of the place you want to keep the backup in",row['destination'])
        if Path(bkpth).exists():
            print("The path you provided is", bkpth)
            if inquircnfrm("Is the given path correct?",True):
                    print("The path has been recorded.")
                    break
            else:
                print("Please try again")
                continue
        else:    
            print("The given path does not exist, please try again.")
            continue

    while True:
        tim = inquirinp("Now enter the time period you want between each backup. Use 'm' for minutes, 'h' for hours, 'd' for days, 'mm' for months(one month is considered as 30days); the given units are case-sensitive.",row['time'])
        if convert_time(tim) == False:
            print("The time period you entered is invalid. Please try again")
            continue
        else:
            print("The time period you entered is", tim, "or", convert_time(tim), "minutes.")
            if inquircnfrm("Is the gievn time period correct?",True):
                print("The time period has been recorded")
                break

            else:
                print("Please try again")
                continue

    if inquircnfrm("Do you have any files/folders within the given folder that you want to exclude from the backup?(Pick no if the thing you want to backup is a file)",False):
        exceptions = []
        print("Please enter the path(s) of the exception(s). Type 'done' once you're finished")
        while True:
            temp = inquirinp('>>',"")
            if temp.lower() == 'done':
                break
            elif Path(temp).exists():
                if temp in exceptions:
                    print("The item given is already once provided.")
                else:
                    exceptions.append(temp)
            else:
                print("The path you entered does not exist, try again.")

            continue
        
        print("The exeptions have been recorded.")
    else:
        exceptions = []
        pass
    
    exceptions = json.dumps(exceptions)

    print("That was all! Adding the job to the database :)")
    editdb(row,flpth,bkpth,tim,convert_time(tim),exceptions)
    print("The job was succesfully updated!")
    printjob(getfromdb("one",row))


def viewjb():
    opt = inquirer.select(
        message="View/Edit Jobs",
        choices=[
            {"name": "View All Jobs", "value": "all"},
            {"name": "View One Job(You need to have the job id of the job you want to view)", "value": "one"},
            {"name": "View last job entery", "value": "last"},
            {"name": "Edit One(job id needed)", "value": "edit"},
            {"name": "Delete One Job", "value": "delone"},
            {"name": "Delete All Jobs", "value": "delall"},
            {"name": "Back", "value": "bck"}
        ]
    ).execute()

    if opt == 'bck':
        mmenu()
    elif opt == 'all':
        if getfromdb('last') == None:
            print("The database is empty")
            mmenu()
        else:
            printjob(getfromdb('all'))
            viewjb()
    elif opt == 'one':
        if getfromdb('last') == None:
            print("The database is empty")
            mmenu()
        else:
            one = getfromdb('one',inquirinp("Please enter the job id of the job you want to view",""))
            if one == None:
                print("The job with the given job id does not exist")
            else:
                printjob(one)

            viewjb()
    elif opt == 'last':
        if getfromdb('last') == None:
            print("The database is empty")
            mmenu()
        else:
            printjob(getfromdb('last'))
            viewjb()
    elif opt == 'edit':
        if getfromdb('last') == None:
            print("The database is empty")
            mmenu()
        else:
            row = inquirinp("Please enter the job id of the job you want to edit","")
            one = getfromdb('one',row)
            if one == None:
                print("The job with the given job id does not exist")
            else:
                print("The job you will be editing is -")
                printjob(one)
                editjb(one)

            viewjb()           
    elif opt == 'delone':
        if getfromdb('last') == None:
            print("The database is empty")
            mmenu()
        else:
            row = inquirinp("Please enter the job id of the job you want to delete","")
            printjob(getfromdb('one',row))
            if inquirinp('Please confirm job deletion by typing YES(case sensitive)','') == 'YES':
                editdb(row,"DELETED","DELETED","DELETED",0,json.dumps([]))
                print("The job has been deleted. Any other job ids have not been affected.")
            else:
                print("Canceled")

            viewjb()

    elif opt == 'delall':
        if getfromdb('last') == None:
            print("The database is empty")
            mmenu()
        else:
            if inquirinp('Please confirm the deletion by typing DELETE ALL JOBS(case sensitive)',''):
                Path(hconfig("read", "DB")).unlink()
                check_base()
                print("All the jobs were deleted.")
            else:
                print("Canceled")

            viewjb()




# The starting greetings
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
print("Welcome to BackupAutomator! This program allows you to automate the process of backing up your files and folders at specified intervals.")
print("")

check_config()
check_base()
first()
mmenu()




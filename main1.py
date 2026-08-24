# The libraries
import json
import os
import time
import sys
from pathlib import Path
import time
from contextlib import redirect_stdout
import sqlite3
import subprocess
from math import gcd
from functools import reduce
import fnmatch


try:
    from InquirerPy import inquirer
except ImportError:
    print("The library 'InquirerPy' is not present, install it using 'pip install InquirerPy' to proceed.")
    sys.exit()

try:
    from tabulate import tabulate
except ImportError:
    print("The library 'tabulate' is not present, install it using 'pip install tabulate' to proceed.")
    sys.exit()


def delete_task_if_exists(name):
    result = subprocess.run(
        ["schtasks", "/query", "/tn", name],
        capture_output=True,
        text=True
    )
    if result.returncode == 0:
        subprocess.run(["schtasks", "/delete", "/tn", name, "/f"], check=True)


def taskschedule():
    name = hconfig('read', 'taskname')

    if not hconfig('read', 'autorun'):
        delete_task_if_exists(name)
        return

    conn = sqlite3.connect(hconfig('read', 'DB'))
    cursor = conn.cursor()
    cursor.execute("SELECT duration FROM jobs WHERE duration != 0")
    dur = [row[0] for row in cursor.fetchall()]
    conn.close()

    if not dur:
        delete_task_if_exists(name)
        return

    MAX_INTERVAL = 120
    a = reduce(gcd, dur)
    if a > MAX_INTERVAL:
        for i in range(MAX_INTERVAL, 0, -1):
            if a % i == 0:
                a = i
                break

    python_exe = Path(sys.executable).with_name("pythonw.exe")
    script = Path(hconfig("read", "script"))

    delete_task_if_exists(name)
    subprocess.run([
        "schtasks", "/create", "/tn", name, "/sc", "minute",
        "/mo", str(a), "/tr", f'"{python_exe}" "{script}"', "/f"
    ], check=True)

    # print(a)
    
def check_config():
    if not os.path.exists(CONFIGPATH):
        temp = {
            "first": True,
            "backuploc": "",
            "timeperiod": "",
            "logging": False,
            "DB": str(BASEDIR / "jobs.db"),
            "script": str(BASEDIR / "runn.py"),
            "autorun": True,
            "taskname": "BackupAutomator",
            "zip": False,
            "log": "",
            "bkper": str(BASEDIR / "script.py"),
            "version": "1.0"
        }

        with open(CONFIGPATH, "w") as f:
            json.dump(temp, f, indent=4)
        
        return(True)
    else:
        return(True)


# For reading from/updating the config. Don't ask me why 'h'config
def hconfig(action,key,value=None):
    if check_config():
        with open(CONFIGPATH, "r") as f:
            temp = json.load(f)

        if action == 'read':
            return temp.get(key)
        elif action == 'change':
            temp[key] = value
            with open(CONFIGPATH, "w") as f:
                json.dump(temp, f, indent=4)
        else:
            print("invalid input for action", action)


def check_base():
    conn = sqlite3.connect(hconfig("read","DB"))
    conn.execute("PRAGMA foreign_keys = ON")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            job_id INTEGER PRIMARY KEY AUTOINCREMENT,
            source TEXT NOT NULL,
            destination TEXT NOT NULL,
            time TEXT NOT NULL,
            duration INTEGER NOT NULL,
            exceptions TEXT,
            zip TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS schedule (
            job_id INTEGER PRIMARY KEY,
            last INTEGER,
            next INTEGER,
            FOREIGN KEY (job_id) REFERENCES jobs(job_id)
        )
    """)

    conn.commit()
    conn.close()


def addtodb(source,destination,times,duration,exeption,zip):
    conn = sqlite3.connect(hconfig("read","DB"))
    conn.execute("PRAGMA foreign_keys = ON")    
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO jobs (source, destination, time, duration, exceptions, zip)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (source, destination, times, duration, exeption, zip)
    )
    lst = int(time.time() // 60 * 60)
    nxt = lst + (duration * 60)
    rowid = cursor.lastrowid
    cursor.execute("""
        INSERT INTO schedule (job_id, last, next)
        VALUES (?, ?, ?)
    """, (rowid, lst, nxt)
    )

    
    
    conn.commit()
    conn.close()
    hconfig('change','autorun',True)
    if getfromdb('last') == None:
        pass
    else:
        with open(os.devnull, "w") as f:
            with redirect_stdout(f):
                taskschedule()
    return rowid


def editdb(row,source,destination,timea,duration,exeption,zip):
    conn = sqlite3.connect(hconfig('read','DB'))
    conn.execute("PRAGMA foreign_keys = ON")
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE jobs
        SET source = ?, destination = ?, time = ?, duration = ?, exceptions = ?, zip = ?
        WHERE job_id = ?
    """, (
        source,
        destination,
        timea,
        duration,
        exeption,
        zip,
        row
    ))

    lst = int(time.time() // 60 * 60)
    if duration == 0:
        nxt = 0
    else:
        nxt = lst + (duration * 60)
    cursor.execute("""
        UPDATE schedule
        SET next = ?
        WHERE job_id = ?
    """, (nxt, row)
    )

    if getfromdb('last') == None:
        pass
    else:
        with open(os.devnull, "w") as f:
            with redirect_stdout(f):
                taskschedule()
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
            "Archive": rows["zip"],
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
                "Archive": job["zip"],
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
    try:
        if input.endswith('mm'):
            return int(float(input[:-2]) * (2592000/60))
        elif input.endswith('h'):
            return int(float(input[:-1]) * 60)
        elif input.endswith('d'):
            return int(float(input[:-1]) * (86400/60))
        elif input.endswith('m'):
            return int(float(input[:-1]) * 1)
        else:
            return False
    except ValueError:
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
    print("Now let's confirm about archiving.")
    defzip()
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
            temp2 = inquirinp("Where do you want the logs to be kept? (Must be a folder)",hconfig('read','log'))
            if Path(temp2).exists() and not temp2 == '' and Path(temp2).is_dir():
                hconfig("change",'logging',True)
                hconfig('change','log',temp2)
            else:
                print("There was an error, please try again.")
                continue

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


def defzip():
    while True:
        temp = inquircnfrm("Do you want your backups archived? (Only works for directories, and the archives are saved as .zip)",False)
        if temp:
            hconfig("change","zip",True)
            if not checkdef('zip',True):
                continue
            else:
                break
        else:
            hconfig("change","zip",False)
            if not checkdef('zip',False):
                continue
            else:
                break


# The extra 'm' is for main as in main menu xD
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
        time.sleep(1)
        if getfromdb('last') == None:
            pass
        else:
            taskschedule()
            # with open(os.devnull, "w") as f:
            #     with redirect_stdout(f):
            #         taskschedule()

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
            {"name": "Stop/Start Backup Script Autorun", "value":"stobak"},   #Reading this function after a few days, I have no clue why I gave it the value 'stobak'
            {"name": "Back", "value": "bck"}
        ]
    ).execute()
    
    if sett == "bck":
        mmenu()
    elif sett == 'stobak':
        if hconfig('read','autorun'):
            hconfig('change','autorun',False)
            taskschedule()
            print("Autorun has been stopped. Note: It will be started again when a new job is added(not edited).")
        else:
            hconfig('change','autorun',True)
            taskschedule()
            print("Autorun has been started.")
        settings()
    elif sett == "defa":
        defa = inquirer.select(
            message="Which default do you want to change?",
            choices=[
                {"name": "Backup Path", "value": "backuploc"},
                {"name": "Time Period", "value": "time"},
                {"name": "Logging", "value": "logg"},
                {"name": "Archive", "value": "zip"},
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
        elif defa == "zip":
            defzip()

        settings()

                
def addjb():
    while True:
        flpth = inquirinp("First, enter the path of the file/folder you want to keep backed up","")
        if Path(flpth).exists() and not flpth == '':
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
        if Path(bkpth).exists() and not Path(bkpth).resolve().is_relative_to(Path(flpth).resolve()):
            print("The path you provided is", bkpth)
            if inquircnfrm("Is the given path correct?",True):
                    print("The path has been recorded.")
                    break
            else:
                print("The path you provided has some problems. Please try again.")
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
            print("The time period you entered is", tim, "or", convert_time(tim), "minutes.(Decimal values are removed if the original time was in minutes)")
            if inquircnfrm("Is the gievn time period correct?",True):
                print("The time period has been recorded")
                break

            else:
                print("Please try again")
                continue
    if Path(flpth).is_dir():
        if inquircnfrm("Do you want to archive the backups?",hconfig('read','zip')):
            zip = 'Yes'
            print("Archiving for this backup is now on.")
        else:
            zip = 'No'
            print("Archiving for this backup is now off.")


        if inquircnfrm("Do you have any files/folders within the given folder that you want to exclude from the backup?",False):
            exceptions = []
            print("Please enter the path(s) of the exception(s). Don't use the full path, only enter the path from after the path of the backup obect(Eg - path of backup/source object - 'abc/xyz', then the path of the exception will be 'pqr' or 'mno/abc', not 'abc/xyz/pqr' or 'abc/xyz/mno/abc'). You may use wild card charectors, but they must follow standard shell wildcard patterns and must be without path slashes.")
            print("Type 'done' once you're finished")
            while True:
                temp = inquirinp('>>',"")
                if temp == "":
                    print("Please enter a path/pattern or type 'done'.")
                    continue
                if temp.lower() == 'done':
                    break
                
                elif '*' in temp:
                    if Path(temp).name == temp:
                        if temp in exceptions:
                            print("The item given is already once provided.")
                        else:
                            exceptions.append(temp)
                    else:
                        print("The path you entered does not exist or has some issues, try again.")
                
                elif (Path(flpth) / temp).exists() and not Path(temp).is_absolute():
                    if temp in exceptions:
                        print("The item given is already once provided.")
                    else:
                        exceptions.append(temp)
                
                else:
                    print("The path you entered does not exist or has some issues, try again.")

                continue
            
            print("The exeptions have been recorded.")
        else:
            exceptions = []
            pass
        
        exceptions = json.dumps(exceptions)

    elif Path(flpth).is_file():
        zip = 'No'
        exceptions = json.dumps([])

    print("That was all! Adding the job to the database :)")
    temp = addtodb(flpth,bkpth,tim,convert_time(tim),exceptions,zip)
    print("The job was added with the jobid as", temp, ". Also printing the job row...")
    printjob(getfromdb("one",temp))


def editjb(row):
    while True:
        flpth = inquirinp("First, enter the path of the file/folder you want to keep backed up",row['source'])
        if Path(flpth).exists() and not flpth == '':
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
        if Path(bkpth).exists() and not Path(bkpth).resolve().is_relative_to(Path(flpth).resolve()):
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

    if Path(flpth).is_dir():
        if inquircnfrm("Do you want to archive the backups?",row['zip'] == 'Yes'):
            zip = 'Yes'
            print("Archiving for this backup is now on.")
        else:
            zip = 'No'
            print("Archiving for this backup is now off.")


        if inquircnfrm("Do you have any files/folders within the given folder that you want to exclude from the backup?",False):
            exceptions = []
            print("Please enter the path(s) of the exception(s). Don't use the full path, only enter the path from after the path of the backup obect(Eg - path of backup/source object - 'abc/xyz', then the path of the exception will be 'pqr' or 'mno/abc', not 'abc/xyz/pqr' or 'abc/xyz/mno/abc'). You may use wild card charectors, but they must follow standard shell wildcard patterns and must be without path slashes.")
            print("Type 'done' once you're finished")
            while True:
                temp = inquirinp('>>',"")
                if temp == "":
                    print("Please enter a path/pattern or type 'done'.")
                    continue
                if temp.lower() == 'done':
                    break
                
                elif '*' in temp:
                    if Path(temp).name == temp:
                        if temp in exceptions:
                            print("The item given is already once provided.")
                        else:
                            exceptions.append(temp)
                    else:
                        print("The path you entered does not exist or has some issues, try again.")
                
                elif (Path(flpth) / temp).exists() and not Path(temp).is_absolute():
                    if temp in exceptions:
                        print("The item given is already once provided.")
                    else:
                        exceptions.append(temp)
                
                else:
                    print("The path you entered does not exist or has some issues, try again.")

                continue
            
            print("The exeptions have been recorded.")
        else:
            exceptions = []
            pass
        
        exceptions = json.dumps(exceptions)

    elif Path(flpth).is_file():
        zip = 'No'
        exceptions = json.dumps([])

    print("That was all! Adding the job to the database :)")
    editdb(row['job_id'],flpth,bkpth,tim,convert_time(tim),exceptions,zip)
    print("The job was succesfully updated!")
    printjob(getfromdb("one",row['job_id']))


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
                editdb(row,"DELETED","DELETED","DELETED",0,json.dumps([]),'DELETED')
                print("The job has been deleted. Any other job ids have not been affected.")
            else:
                print("Canceled")

            viewjb()

    elif opt == 'delall':
        if getfromdb('last') == None:
            print("The database is empty")
            mmenu()
        else:
            if inquirinp('Please confirm the deletion by typing DELETE ALL JOBS(case sensitive)','') == 'DELETE ALL JOBS':
                hconfig('change','autorun',False)
                taskschedule()
                Path(hconfig("read", "DB")).unlink()
                check_base()
                hconfig('change','autorun',False)
                print("All the jobs were deleted.")
            else:
                print("Canceled")

            viewjb()



BASEDIR = Path(__file__).resolve().parent
CONFIGPATH = BASEDIR / "config.json"

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





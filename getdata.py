import json
from pathlib import Path
import sqlite3
import shutil


def checkconfig():
    if Path(CNFPATH).exists():
        pass
        return True
    else:
        return False

def hconfig(action,key,value=None):
    if checkconfig():
        with open(CNFPATH, "r") as f:
            temp = json.load(f)

        if action == 'read':
            return temp.get(key)
        elif action == 'change':
            temp[key] = value
            with open(CNFPATH, "w") as f:
                json.dump(temp, f, indent=4)
        else:
            print("invalid input for action", action)

def getstore():
    total, used, free = shutil.disk_usage(hconfig('read','backuploc'))
    return((used/total) * 100)


def getfromdb(a,row=None):
    conn = sqlite3.connect(hconfig('read','DB'))
    cursor = conn.cursor()

    if a.lower() == 'one':
        cursor.execute("SELECT * FROM jobs WHERE job_id = ?", (row, ))
        cursor = cursor.fetchone()
    elif a.lower() == 'all':
        cursor.execute("SELECT * FROM jobs")
        cursor = cursor.fetchall()
    else:
        return ValueError



BASEDIR = Path(__file__).resolve().parent
CNFPATH = Path(BASEDIR / "config.json")



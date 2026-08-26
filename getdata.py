import json
from pathlib import Path
import sqlite3
import shutil


# This script won't work if there was no config
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
    return round((used/total) * 100, 1)


def getfromdb(a,row=None):
    conn = sqlite3.connect(hconfig('read','DB'))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    if a.lower() == 'one':
        cursor.execute("SELECT * FROM jobs WHERE job_id = ?", (row, ))
        cursor = cursor.fetchone()
    elif a.lower() == 'all':
        cursor.execute("SELECT * FROM jobs")
        cursor = cursor.fetchall()
    else:
        conn.close()
        raise ValueError("Invalid Action Specified.")

    conn.close()
    if cursor is None:
        return None

    if a.lower() == 'all':
        return [dict(item) for item in cursor]
    else:
        return dict(cursor)


def getinitialdata():
    return {
        "version": hconfig('read','version'),
        "storage": getstore(),
        "jobs": getfromdb("all")
    }


BASEDIR = Path(__file__).resolve().parent
CNFPATH = Path(BASEDIR / "config.json")


getinitialdata()
import json
from pathlib import Path
import sqlite3
import shutil
import time
import subprocess
from math import gcd
from functools import reduce
import sys



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

    MAXINTERVAL = 120
    a = reduce(gcd, dur)
    if a > MAXINTERVAL:
        for i in range(MAXINTERVAL, 0, -1):
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


def setautorun(value):

    if not isinstance(value, bool):
        raise ValueError("Autorun value must be a boolean.")

    hconfig("change", "autorun", value)
    taskschedule()

    return value


def getstore():
    path = Path(hconfig('read', 'backuploc'))

    try:
        usagepath = path if path.exists() else path.anchor

        total, used, free = shutil.disk_usage(usagepath)

        return round((used / total) * 100, 1)

    except (FileNotFoundError, OSError):
        return None


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


def getdef():
    return {
        "backuploc": hconfig("read", "backuploc"),
        "time": hconfig("read", "timeperiod"),
        "zip": hconfig("read", "zip"),
        "logging": hconfig("read", "logging"),
        "autorun": hconfig("read", "autorun")
    }


def changedef(new):
    for key, value in new.items():
        hconfig("change", key, value)


def getinitialdata():
    return {
        "version": hconfig('read','version'),
        "storage": getstore(),
        "jobs": getfromdb("all")
    }


def addtodb(source, destination, times, duration, exceptions, wildcards, zip):

    exception = json.dumps(exceptions + wildcards)

    conn = sqlite3.connect(hconfig("read", "DB"))
    conn.execute("PRAGMA foreign_keys = ON")
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO jobs (source, destination, time, duration, exceptions, zip)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        source,
        destination,
        times,
        duration,
        exception,
        zip
    ))

    lst = int(time.time() // 60 * 60)
    nxt = lst + (duration * 60)

    rowid = cursor.lastrowid

    cursor.execute("""
        INSERT INTO schedule (job_id, last, next)
        VALUES (?, ?, ?)
    """, (
        rowid,
        lst,
        nxt
    ))

    conn.commit()
    conn.close()

    hconfig("change", "autorun", True)

    return rowid


def editdb(job_id,source, destination, times, duration, exceptions, wildcards, zip):

    exception = json.dumps(exceptions + wildcards)

    conn = sqlite3.connect(hconfig("read", "DB"))

    conn.execute("PRAGMA foreign_keys = ON")

    cursor = conn.cursor()

    cursor.execute("""
        UPDATE jobs
        SET source = ?,
            destination = ?,
            time = ?,
            duration = ?,
            exceptions = ?,
            zip = ?
        WHERE job_id = ?
    """, (
        source,
        destination,
        times,
        duration,
        exception,
        zip,
        job_id
    ))

    lst = int(time.time() // 60 * 60)

    nxt = lst + (duration * 60)

    cursor.execute("""
        UPDATE schedule
        SET next = ?
        WHERE job_id = ?
    """, (
        nxt,
        job_id
    ))

    conn.commit()

    conn.close()

    return job_id

BASEDIR = Path(__file__).resolve().parent
CNFPATH = Path(BASEDIR / "config.json")


getinitialdata()
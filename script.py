import json
import os
import sqlite3
import sys
import time
from pathlib import Path
import shutil
import fnmatch


def check_config():
    if not os.path.exists(CNFPTH):
        sys.exit()
    else:
        return(True)


def check_base():
    if not os.path.exists(hconfig('read','DB')):
        sys.exit()
    else:
        conn = sqlite3.connect(hconfig('read','DB'))
        cursor = conn.cursor()
        name = 'schedule'
        cursor.execute("""
        SELECT name FROM sqlite_master WHERE type='table' AND name=?
        """, (name,))

        if cursor.fetchone() is not None:
            return(True)
        else:
            sys.exit()

        conn.close()


def hconfig(action,key,value=None):
    if check_config():
        with open(CNFPTH, "r") as f:
            temp = json.load(f)

        if action == 'read':
            return temp.get(key)
        elif action == 'change':
            temp[key] = value
            with open(CNFPTH, "w") as f:
                json.dump(temp, f, indent=4)
        else:
            print("invalid input for action", action)


def updttime(id,dur):
    lst = int(time.time() // 60 * 60)
    nxt = lst + (dur * 60)
    conn = sqlite3.connect(hconfig('read','DB'))
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE schedule
        SET last = ?, next = ?
        WHERE job_id = ?
    """,(
        lst,
        nxt,
        id
    ))

    conn.commit()
    conn.close()

def checktable(row):
    conn = sqlite3.connect(hconfig('read','DB'))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM schedule WHERE job_id = ?", (row,))
    cursor = cursor.fetchone()
    conn.close()
    if cursor is None:
        return None
    else:
        return dict(cursor)
    

def getmainrow(row):
    conn = sqlite3.connect(hconfig('read','DB'))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM jobs WHERE job_id = ?", (row,))
    cursor = cursor.fetchone()
    conn.close()
    if cursor is None:
        print("ERROR: Tables mismatch. Aborting.")
        sys.exit()
    else:
        return dict(cursor)


def checkrow(row):
    temp = False
    if row is None or row['next'] == 0:
        temp = False
    else:
        if (time.time() // 60*60) >= row['next']:
            temp = True
        else:
            temp = False

    return(temp)


def checkjobs():
    rows = []
    conn = sqlite3.connect(hconfig('read','DB'))
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM schedule")
    n = cursor.fetchone()[0]
    if not n == 0:
        for i in range(1,n+1):
            # print(checkrow(checktable(i)))
            if checkrow(checktable(i)):
                rows.append(i)
            else:
                pass
    if rows == []:
        return None
    else:
        return rows
            

def copyfolder(s,d,e):
    s, d = Path(s), Path(d)
    d = d / (s.stem + "_backup")
    we = []
    ee = []
    if e == []:
        print("No exceptions found, backing up without them.")
        shutil.copytree(s,d)
        print("Folder copied.")
    else:
        print("Exceptions found. Excluding them from the backup.")
        for i in e:
            if '*' in i:
                we.append(i)
            else:
                ee.append(i)
        exc = {Path(x) for x in ee}

        def ignoreexcep(direc,names):
            direc = Path(direc)
            ignr = []
            for name in names:
                rel = Path(direc / name).relative_to(s)

                if rel in exc:
                    ignr.append(name)
                    continue

                for wild in we:
                    if fnmatch.fnmatch(rel.name, wild):
                        ignr.append(name)
                        break
            return ignr

        shutil.copytree(
            s,
            d,
            ignore=ignoreexcep,
            dirs_exist_ok=False
        )
        print("Folder Copied.")
    

def backup(row):
    src = row['source']
    des = row['destination']
    excep = json.loads(row['exceptions'])  
    # I know I could have written the above in one line but I like it this way :>
    if Path(src).is_file():
        shutil.copy2(Path(src),Path(Path(des) / (Path(src).stem + "_Backup" + Path(src).suffix)))
    elif Path(src).is_dir():
        if row['zip'].lower() == 'yes':
            if (Path(des) / Path(str(Path(src).name) + "_backup.zip")).exists():
                print("Previous backup found, removing. Name of prev backup:", str(Path(src).name) + "_backup.zip")

                os.remove(Path(des) / Path(str(Path(src).name) + "_backup.zip"))

                if (Path(des) / Path(str(Path(src).name) + "_backup.zip")).exists():
                    print("There was some error in deleting the file. Exiting")
                    sys.exit()
                else:
                    print("Previous backup removed succesfully.")
                
            else:
                print("No previous backup found. Continuing.")

            temp = Path(des) / (Path(src).name + "_backup")
            if temp.exists():
                shutil.rmtree(temp)

            copyfolder(src,des,excep)

            print("Making the archive.")
            zip_path = temp.with_name(temp.name + ".zip")
            shutil.make_archive(base_name=str(temp), format="zip", root_dir=temp)
            
            if zip_path.exists():
                print("Archiving complete. Removing the copied folder.")
                shutil.rmtree(temp)
                if not temp.exists():
                    print("Removal of the copied folder complete. Backup Complete.")
                else:
                    print("There was a problem in removing the folder. Backup left Incomplete.")
            else:
                print("There was a problem in archiving. Backup Incomplete.")


        elif row['zip'].lower() == 'no':
            if (Path(des) / Path(str(Path(src).name) + "_backup")).exists():
                print("Previous backup found, removing. Name of prev backup:", str(Path(src).name) + "_backup")

                shutil.rmtree(Path(des) / Path(str(Path(src).name) + "_backup"))

                if not (Path(des) / Path(str(Path(src).name) + "_backup")).exists():
                    print("Previous backup deleted succesfully.")
                else:
                    print("There was some error in deleting previous backup. Exiting.")
                    sys.exit()

            else:
                print("No previous backup found. Continuing.")

            copyfolder(src,des,excep)
            print("Backup complete.")


#The actual thing
BASEDIR = Path(__file__).resolve().parent
CNFPTH = BASEDIR / "config.json"
check_config()
check_base()
rows = checkjobs()
if rows is None:
    print("No jobs due. Exiting...")
    sys.exit()
else:
    for i in range(0, len(rows)):
        print('Current job_id -')
        print(rows[i])
        print('Current row -')
        row = getmainrow(rows[i])
        print(row)
        if row['duration'] == 0:
            print("Skipping deleted row.")
            continue
        else:
            backup(row)
        print('Row complete. Updating the schedule table.')
        updttime(row['job_id'],row['duration'])
        print("Schedule updated.")
        print('')
        print('')


print("All rows done. Exiting.")




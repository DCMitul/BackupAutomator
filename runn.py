import json
import subprocess
import sys
from pathlib import Path
from datetime import datetime


BASEDIR = Path(__file__).resolve().parent
CONFIGPATH = BASEDIR / "config.json"

if CONFIGPATH.exists():
    with open(CONFIGPATH, "r") as f:
        temp = json.load(f)
        SCRIPTPATH = Path(temp.get("bkper"))
        LOGPATH = Path(temp.get('log'))
else:
    print("THE CONFIG DOES NOT EXIST. EXITING.")
    sys.exit()

LOGPATH.mkdir(parents=True, exist_ok=True)
timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
logfile = LOGPATH / f"backup_{timestamp}.txt"

with open(logfile, "w", encoding="utf-8") as log:
    log.write(f"Logger started: {datetime.now()}\n")

    result = subprocess.run(
        [sys.executable, "-u", str(SCRIPTPATH)],
        stdout=log,
        stderr=subprocess.STDOUT,
        text=True,
        cwd=Path(__file__).parent
    )

    log.write(f"\nBackup script exited with code: {result.returncode}\n")
    
 
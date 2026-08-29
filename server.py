from flask import Flask
from flask import send_from_directory
from flask import jsonify
from flask import request
from pathlib import Path
from getdata import getdef, changedef, hconfig, addtodb, editdb, taskschedule, setautorun
import sqlite3
from tkinter import Tk
from tkinter.filedialog import askdirectory, askopenfilename, askopenfilenames
import re
import fnmatch



BASEDIR = Path(__file__).resolve().parent
GUIDIR = BASEDIR / "gui"
CNFGPATH = BASEDIR / "config.json"
app = Flask(__name__)

@app.route("/")
def home():
    if not CNFGPATH.exists():
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <title>BackupAutomator</title>
        </head>
        <body>
            <h1>Please do the first-time setup from the CLI tool.</h1>
        </body>
        </html>
        """
    else:
        return send_from_directory(BASEDIR, "index.html")


@app.route("/gui/<path:path>")
def gui_files(path):
    return send_from_directory(GUIDIR, path)


@app.route("/api/initial-data")
def initial_data():
    if not CNFGPATH.exists():
        return {
            "error": "first_setup_required"
        }, 503
    else:
        from getdata import getinitialdata

        return jsonify(getinitialdata())

@app.route("/api/settings", methods=["GET"])
def settings_get():
    return jsonify(getdef())

@app.route("/api/settings", methods=["PUT"])
def settings_put():

    settings = request.get_json()

    if not isinstance(settings, dict):
        return jsonify({"error": "Invalid settings data"}), 400

    changedef(settings)

    return jsonify({
        "success": True
    })


@app.route("/api/jobs/<int:job_id>", methods=["DELETE"])
def delete_job(job_id):

    conn = sqlite3.connect(
        hconfig("read", "DB")
    )

    cursor = conn.cursor()

    cursor.execute(
        "SELECT job_id FROM jobs WHERE job_id = ?",
        (job_id,)
    )

    job = cursor.fetchone()

    conn.close()

    if job is None:
        return jsonify({
            "success": False,
            "error": "Job not found."
        }), 404


    editdb(
        job_id,
        "DELETED",
        "DELETED",
        "DELETED",
        0,
        [],
        [],
        "DELETED"
    )

    taskschedule()
    return jsonify({
        "success": True
    })


@app.route("/api/jobs", methods=["DELETE"])
def delete_all_jobs():

    conn = sqlite3.connect(
        hconfig("read", "DB")
    )

    cursor = conn.cursor()

    cursor.execute("DELETE FROM schedule")
    cursor.execute("DELETE FROM jobs")

    cursor.execute(
        "DELETE FROM sqlite_sequence WHERE name = 'jobs'"
    )

    conn.commit()
    conn.close()

    hconfig('change','autorun',False)
    taskschedule()

    return jsonify({
        "success": True
    })



def pickfolder():
    root = Tk()
    root.withdraw()
    root.attributes("-topmost", True)

    fold = askdirectory(title="Select Folder")

    root.destroy()

    return fold

def pickpath(mode):

    root = Tk()
    root.withdraw()
    root.attributes("-topmost", True)

    if mode == "folder":
        result = askdirectory(
            parent=root,
            title="Select Folder"
        )

    elif mode == "file":
        result = askopenfilename(
            parent=root,
            title="Select File"
        )

    elif mode == "files":
        result = askopenfilenames(
            parent=root,
            title="Select Files"
        )

    elif mode == "source":

        result = {"path": ""}

        from tkinter import Toplevel, Label, Button

        dialog = Toplevel(root)
        dialog.title("Select Source Type")
        dialog.geometry("300x120")
        dialog.resizable(False, False)
        dialog.attributes("-topmost", True)

        def select_file():
            result["path"] = askopenfilename(
                parent=dialog,
                title="Select File"
            )
            dialog.destroy()

        def select_folder():
            result["path"] = askdirectory(
                parent=dialog,
                title="Select Folder"
            )
            dialog.destroy()

        Label(
            dialog,
            text="Select Source Type"
        ).pack(pady=10)

        Button(
            dialog,
            text="File",
            width=10,
            command=select_file
        ).pack(side="left", padx=35)

        Button(
            dialog,
            text="Folder",
            width=10,
            command=select_folder
        ).pack(side="right", padx=35)

        root.wait_window(dialog)

        result = result["path"]

    else:
        result = ""

    root.destroy()

    return result


@app.route("/api/browse", methods=["POST"])
def browse():

    data = request.get_json()
    mode = data.get("mode")

    result = pickpath(mode)

    return jsonify({
        "path": result
    })


@app.route("/api/jobs", methods=["POST"])
def create_job():

    data = request.get_json()

    if not isinstance(data, dict):
        return jsonify({
            "success": False,
            "error": "Invalid job data."
        }), 400

    source = data.get("source", "").strip()
    destination = data.get("destination", "").strip()
    time_period = data.get("time", "").strip()
    exceptions = data.get("exceptions", [])
    wildcards = data.get("wildcards", [])
    zip_value = data.get("zip", False)

    if not source:
        return jsonify({
            "success": False,
            "error": "Please select a source."
        }), 400

    if not destination:
        return jsonify({
            "success": False,
            "error": "Please select a destination."
        }), 400

    if not time_period:
        return jsonify({
            "success": False,
            "error": "Please enter a time period."
        }), 400

    source_path = Path(source)
    destination_path = Path(destination)

    if not source_path.exists():
        return jsonify({
            "success": False,
            "error": "The selected source does not exist."
        }), 400

    if not destination_path.exists():
        return jsonify({
            "success": False,
            "error": "The selected destination does not exist."
        }), 400

    if not destination_path.is_dir():
        return jsonify({
            "success": False,
            "error": "The destination must be a folder."
        }), 400

    source_path = source_path.resolve()
    destination_path = destination_path.resolve()

    if source_path.is_dir():

        if (
            destination_path == source_path
            or source_path in destination_path.parents
        ):
            return jsonify({
                "success": False,
                "error": "The destination cannot be inside the source."
            }), 400

    time_match = re.fullmatch(
        r"(\d+(?:\.\d+)?)(mm|m|h|d)",
        time_period
    )

    if not time_match:
        return jsonify({
            "success": False,
            "error": "Invalid time period."
        }), 400

    time_value = float(time_match.group(1))
    time_unit = time_match.group(2)

    if time_value <= 0:
        return jsonify({
            "success": False,
            "error": "The time period must be greater than zero."
        }), 400

    if time_unit == "m":
        duration = int(time_value)

    elif time_unit == "h":
        duration = int(time_value * 60)

    elif time_unit == "d":
        duration = int(time_value * 1440)

    elif time_unit == "mm":
        duration = int(time_value * 43200)

    else:
        return jsonify({
            "success": False,
            "error": "Invalid time unit."
        }), 400

    if duration <= 0:
        return jsonify({
            "success": False,
            "error": "The resulting time period is invalid."
        }), 400

    if not isinstance(exceptions, list):
        return jsonify({
            "success": False,
            "error": "Invalid exception data."
        }), 400

    if not isinstance(wildcards, list):
        return jsonify({
            "success": False,
            "error": "Invalid wildcard data."
        }), 400

    relative_exceptions = []

    if source_path.is_dir():

        for exception in exceptions:

            if not isinstance(exception, str):
                return jsonify({
                    "success": False,
                    "error": "Invalid exception path."
                }), 400

            exception_path = Path(exception)

            if not exception_path.exists():
                return jsonify({
                    "success": False,
                    "error": f"Exception does not exist: {exception}"
                }), 400

            exception_path = exception_path.resolve()

            try:
                relative = exception_path.relative_to(source_path)

            except ValueError:
                return jsonify({
                    "success": False,
                    "error":
                        f"Exception is not inside the source: {exception}"
                }), 400

            if relative == Path("."):
                return jsonify({
                    "success": False,
                    "error":
                        "The source itself cannot be an exception."
                }), 400

            relative_exceptions.append(str(relative))

    elif exceptions:
        return jsonify({
            "success": False,
            "error":
                "Exceptions cannot be used when the source is a file."
        }), 400

    for wildcard in wildcards:

        if not isinstance(wildcard, str):
            return jsonify({
                "success": False,
                "error": "Invalid wildcard."
            }), 400

        wildcard = wildcard.strip()

        if not wildcard:
            return jsonify({
                "success": False,
                "error": "Wildcard cannot be empty."
            }), 400

        try:
            fnmatch.translate(wildcard)
        except Exception:
            return jsonify({
                "success": False,
                "error": f"Invalid wildcard: {wildcard}"
            }), 400

    zip_value = "Yes" if zip_value else "No"

    if source_path.is_file():
        zip_value = "No"

    rowid = addtodb(
        str(source_path),
        str(destination_path),
        time_period,
        duration,
        relative_exceptions,
        wildcards,
        zip_value
    )

    hconfig('change','autorun',True)
    taskschedule()
    return jsonify({
        "success": True,
        "job_id": rowid
    })

@app.route("/api/jobs/<int:job_id>", methods=["PUT"])
def edit_job(job_id):

    data = request.get_json()

    if not isinstance(data, dict):
        return jsonify({
            "success": False,
            "error": "Invalid job data."
        }), 400

    source = data.get("source", "")
    destination = data.get("destination", "")
    time_period = data.get("time", "")
    exceptions = data.get("exceptions", [])
    wildcards = data.get("wildcards", [])
    zip_value = data.get("zip", False)

    if not isinstance(source, str):
        return jsonify({
            "success": False,
            "error": "Invalid source."
        }), 400

    if not isinstance(destination, str):
        return jsonify({
            "success": False,
            "error": "Invalid destination."
        }), 400

    if not isinstance(time_period, str):
        return jsonify({
            "success": False,
            "error": "Invalid time period."
        }), 400

    if not isinstance(exceptions, list):
        return jsonify({
            "success": False,
            "error": "Invalid exception data."
        }), 400

    if not isinstance(wildcards, list):
        return jsonify({
            "success": False,
            "error": "Invalid wildcard data."
        }), 400

    source = source.strip()
    destination = destination.strip()
    time_period = time_period.strip()

    if not source:
        return jsonify({
            "success": False,
            "error": "Please select a source."
        }), 400

    if not destination:
        return jsonify({
            "success": False,
            "error": "Please select a destination."
        }), 400

    if not time_period:
        return jsonify({
            "success": False,
            "error": "Please enter a time period."
        }), 400

    conn = sqlite3.connect(
        hconfig("read", "DB")
    )

    cursor = conn.cursor()

    cursor.execute(
        "SELECT job_id FROM jobs WHERE job_id = ?",
        (job_id,)
    )

    if cursor.fetchone() is None:
        conn.close()

        return jsonify({
            "success": False,
            "error": "Job not found."
        }), 404

    conn.close()

    source_path = Path(source)
    destination_path = Path(destination)

    if not source_path.exists():
        return jsonify({
            "success": False,
            "error": "The selected source does not exist."
        }), 400

    if not destination_path.exists():
        return jsonify({
            "success": False,
            "error": "The selected destination does not exist."
        }), 400

    if not destination_path.is_dir():
        return jsonify({
            "success": False,
            "error": "The destination must be a folder."
        }), 400

    source_path = source_path.resolve()
    destination_path = destination_path.resolve()

    if source_path.is_dir():

        if (
            destination_path == source_path
            or source_path in destination_path.parents
        ):
            return jsonify({
                "success": False,
                "error": "The destination cannot be inside the source."
            }), 400

    time_match = re.fullmatch(
        r"(\d+(?:\.\d+)?)(mm|m|h|d)",
        time_period
    )

    if not time_match:
        return jsonify({
            "success": False,
            "error": "Invalid time period."
        }), 400

    time_value = float(time_match.group(1))
    time_unit = time_match.group(2)

    if time_value <= 0:
        return jsonify({
            "success": False,
            "error": "The time period must be greater than zero."
        }), 400

    if time_unit == "m":
        duration = int(time_value)

    elif time_unit == "h":
        duration = int(time_value * 60)

    elif time_unit == "d":
        duration = int(time_value * 1440)

    elif time_unit == "mm":
        duration = int(time_value * 43200)

    else:
        return jsonify({
            "success": False,
            "error": "Invalid time unit."
        }), 400

    if duration <= 0:
        return jsonify({
            "success": False,
            "error": "The resulting time period is invalid."
        }), 400

    relative_exceptions = []

    if source_path.is_dir():

        for exception in exceptions:

            if not isinstance(exception, str):
                return jsonify({
                    "success": False,
                    "error": "Invalid exception path."
                }), 400

            exception_path = Path(exception)

            if not exception_path.exists():
                return jsonify({
                    "success": False,
                    "error":
                        f"Exception does not exist: {exception}"
                }), 400

            exception_path = exception_path.resolve()

            try:
                relative = exception_path.relative_to(
                    source_path
                )

            except ValueError:
                return jsonify({
                    "success": False,
                    "error":
                        f"Exception is not inside the source: {exception}"
                }), 400

            if relative == Path("."):
                return jsonify({
                    "success": False,
                    "error":
                        "The source itself cannot be an exception."
                }), 400

            relative_exceptions.append(
                str(relative)
            )

    elif exceptions:

        return jsonify({
            "success": False,
            "error":
                "Exceptions cannot be used when the source is a file."
        }), 400

    for wildcard in wildcards:

        if not isinstance(wildcard, str):
            return jsonify({
                "success": False,
                "error": "Invalid wildcard."
            }), 400

        wildcard = wildcard.strip()

        if not wildcard:
            return jsonify({
                "success": False,
                "error": "Wildcard cannot be empty."
            }), 400

        try:
            fnmatch.translate(wildcard)
        except Exception:
            return jsonify({
                "success": False,
                "error":
                    f"Invalid wildcard: {wildcard}"
            }), 400

    zip_value = "Yes" if zip_value else "No"

    if source_path.is_file():
        zip_value = "No"

    editdb(
        job_id,
        str(source_path),
        str(destination_path),
        time_period,
        duration,
        relative_exceptions,
        wildcards,
        zip_value
    )

    return jsonify({
        "success": True,
        "job_id": job_id
    })


@app.route("/api/autorun", methods=["PUT"])
def autorun_put():

    data = request.get_json()

    if not isinstance(data, dict):
        return jsonify({
            "success": False,
            "error": "Invalid autorun data."
        }), 400

    value = data.get("autorun")

    if not isinstance(value, bool):
        return jsonify({
            "success": False,
            "error": "Autorun value must be true or false."
        }), 400

    try:
        result = setautorun(value)

    except Exception as error:
        return jsonify({
            "success": False,
            "error": str(error)
        }), 500

    return jsonify({
        "success": True,
        "autorun": result
    })


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000)

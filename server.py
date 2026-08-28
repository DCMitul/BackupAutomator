from flask import Flask
from flask import send_from_directory
from flask import jsonify
from flask import request
from pathlib import Path
from getdata import getdef,changedef,hconfig
import sqlite3
from tkinter import Tk
from tkinter.filedialog import askdirectory, askopenfilename, askopenfilenames



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

@app.route("/api/jobs", methods=["DELETE"])
def delete_all_jobs():

    conn = sqlite3.connect(
        hconfig("read", "DB")
    )

    cursor = conn.cursor()

    cursor.execute("DELETE FROM schedule")
    cursor.execute("DELETE FROM jobs")

    conn.commit()
    conn.close()

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


    source = data.get("source")
    destination = data.get("destination")
    time = data.get("time")
    exceptions = data.get("exceptions", [])
    wildcards = data.get("wildcards", "")
    zip_value = data.get("zip")


    if not source:
        return jsonify({
            "success": False,
            "error": "A source must be selected."
        }), 400


    if not destination:
        return jsonify({
            "success": False,
            "error": "A destination must be selected."
        }), 400


    if not time:
        return jsonify({
            "success": False,
            "error": "A time period must be provided."
        }), 400


    source_path = Path(source)

    if not source_path.exists():
        return jsonify({
            "success": False,
            "error": "The selected source does not exist."
        }), 400


    destination_path = Path(destination)

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


    source_resolved = source_path.resolve()
    destination_resolved = destination_path.resolve()

    if source_resolved.is_dir():

        if (
            destination_resolved == source_resolved
            or source_resolved in destination_resolved.parents
        ):
            return jsonify({
                "success": False,
                "error": "The destination cannot be inside the source."
            }), 400

    import re

    if not re.fullmatch(
        r"\d+(mm|m|h|d)",
        time
    ):
        return jsonify({
            "success": False,
            "error": "Invalid time period."
        }), 400

    import fnmatch

    wildcard_list = []

    if wildcards.strip():

        wildcard_list = [
            item.strip()
            for item in wildcards.split(",")
            if item.strip()
        ]

        for pattern in wildcard_list:

            if "/" in pattern or "\\" in pattern:
                return jsonify({
                    "success": False,
                    "error":
                        f"Invalid wildcard: {pattern}"
                }), 400

            try:
                fnmatch.translate(pattern)
            except Exception:
                return jsonify({
                    "success": False,
                    "error":
                        f"Invalid wildcard: {pattern}"
                }), 400

    return jsonify({
        "success": True
    })



if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000)
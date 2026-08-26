from flask import Flask
from flask import send_from_directory
from flask import jsonify
from pathlib import Path



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


if __name__ == "__main__":
    app.run(host = "127.0.0.1", port = 5000)



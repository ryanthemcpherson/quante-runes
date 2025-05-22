import os
import sys
import shutil
import subprocess
import glob

def ensure_dependencies():
    """Ensure all required dependencies for building are installed"""
    required_packages = [
        "pyinstaller", 
        "pillow",
        "gspread",
        "qasync",
        "google-auth",
        "google-auth-oauthlib"
    ]
    
    for package in required_packages:
        try:
            if package == "pillow":
                __import__("PIL")
            elif package == "google-auth":
                __import__("google.auth")
            elif package == "google-auth-oauthlib":
                __import__("google_auth_oauthlib")
            else:
                __import__(package)
        except ImportError:
            print(f"{package} not found. Installing...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])

def find_data_files():
    """Find all data files that need to be included"""
    data_files = []
    
    # Check for icon file
    icon_path = "urgot_icon.png"
    if os.path.exists(icon_path):
        data_files.append(f"--add-data={icon_path};.")
    
    # Check for Google authentication files
    auth_files = ["client_secrets.json", "token.json", "credentials.json"]
    for auth_file in auth_files:
        if os.path.exists(auth_file):
            data_files.append(f"--add-data={auth_file};.")
            print(f"Including auth file: {auth_file}")
    
    # Look for any JSON files that might contain matchup data
    json_files = glob.glob("*.json")
    for json_file in json_files:
        if json_file not in auth_files:  # Don't add auth files twice
            data_files.append(f"--add-data={json_file};.")
            print(f"Including data file: {json_file}")
    
    # Look for any CSV files that might contain matchup data
    csv_files = glob.glob("*.csv")
    for csv_file in csv_files:
        data_files.append(f"--add-data={csv_file};.")
        print(f"Including data file: {csv_file}")
    
    # Look for any data directories
    data_dirs = ["data", "matchups", "champions", "src"]
    for data_dir in data_dirs:
        if os.path.exists(data_dir) and os.path.isdir(data_dir):
            data_files.append(f"--add-data={data_dir};{data_dir}")
            print(f"Including directory: {data_dir}")
    
    # Explicitly include img_url_hack.html
    img_hack_path = os.path.join("src", "data", "img_url_hack.html")
    if os.path.exists(img_hack_path):
        data_files.append(f"--add-data={img_hack_path};src/data")
        print(f"Including image hack file: {img_hack_path}")
    else:
        print(f"Warning: {img_hack_path} not found")
    
    return data_files

def build_executable():
    print("Building Urgot Matchup Helper executable...")
    
    # Clean up previous build
    for dir_to_clean in ["build", "dist"]:
        if os.path.exists(dir_to_clean):
            try:
                shutil.rmtree(dir_to_clean)
                print(f"Cleaned up {dir_to_clean} directory")
            except Exception as e:
                print(f"Warning: Could not clean up {dir_to_clean}: {e}")
    
    # Ensure required dependencies are installed
    ensure_dependencies()
    
    # Create /dist and /build directories if they don't exist
    os.makedirs("dist", exist_ok=True)
    os.makedirs("build", exist_ok=True)
    
    # Check if icon exists
    icon_path = "urgot_icon.png"
    if not os.path.exists(icon_path):
        print(f"Warning: Icon file {icon_path} not found. Building without an icon.")
        icon_param = []
    else:
        icon_param = [f"--icon={icon_path}"]
    
    # Find all data files to include
    data_files = find_data_files()
    
    # Create a debug version of main.py that includes logging
    debug_main = "main_debug.py"
    with open("main.py", "r") as f:
        main_content = f.read()
    
    with open(debug_main, "w") as f:
        f.write("import sys\n")
        f.write("import os\n")
        f.write("import logging\n")
        f.write("import traceback\n\n")
        f.write("# Configure logging to both file and console\n")
        f.write("logging.basicConfig(\n")
        f.write("    level=logging.DEBUG,\n")
        f.write("    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',\n")
        f.write("    handlers=[\n")
        f.write("        logging.FileHandler('debug.log', mode='w'),\n")
        f.write("        logging.StreamHandler()\n")
        f.write("    ]\n")
        f.write(")\n\n")
        f.write("logger = logging.getLogger(__name__)\n")
        f.write("logger.debug('Application starting...')\n")
        f.write("logger.debug(f'Current working directory: {os.getcwd()}')\n")
        f.write("logger.debug(f'Sys path: {sys.path}')\n")
        f.write("logger.debug(f'Environment variables: {dict(os.environ)}')\n")
        f.write("logger.debug(f'Available files: {os.listdir()}')\n")
        f.write("logger.debug(f'Available files in src/data: {os.listdir(\"src/data\") if os.path.exists(\"src/data\") else \"src/data not found\"}')\n\n")
        f.write("try:\n")
        f.write("    " + main_content.replace("\n", "\n    "))  # Indent the main content
        f.write("\nexcept Exception as e:\n")
        f.write("    logger.error(f'Unhandled exception: {str(e)}')\n")
        f.write("    logger.error(f'Traceback:\\n{traceback.format_exc()}')\n")
        f.write("    raise\n")
    
    # Define the PyInstaller command
    cmd = [
        "pyinstaller",
        "--name=UrgotMatchupHelper",
        "--windowed",  # No console window
        "--onefile",   # Create a single executable
        *icon_param,
        *data_files,
        "--hidden-import=qasync",
        "--hidden-import=gspread",
        "--hidden-import=google.auth",
        "--hidden-import=google_auth_oauthlib.flow",
        "--hidden-import=google.oauth2.credentials",
        "--hidden-import=google_auth_oauthlib.flow",
        "--hidden-import=google.auth.transport.requests",
        "--debug=all",  # Add debug information
        debug_main  # Use the debug version of main.py
    ]
    
    # Run PyInstaller
    result = subprocess.run(cmd)
    
    # Clean up debug main file
    if os.path.exists(debug_main):
        os.remove(debug_main)
    
    if result.returncode != 0:
        print("Error: PyInstaller build failed. Check the output above for details.")
        return
    
    # Copy additional required files to dist folder
    print("Copying additional files...")
    required_files = [
        "README.md",
        "INSTALL.md",
        "PRIVACY_POLICY.md",
        "requirements.txt",
        "client_secrets.json",  # Include this file separately if it exists
        "token.json",          # Include token file if it exists
        "credentials.json"     # Include credentials file if it exists
    ]
    
    for file in required_files:
        if os.path.exists(file):
            shutil.copy(file, os.path.join("dist", file))
        else:
            print(f"Note: {file} not found, skipping...")
    
    # Create a docs folder in the dist directory
    os.makedirs(os.path.join("dist", "docs"), exist_ok=True)
    
    # Copy docs if they exist
    if os.path.exists("docs"):
        for file in os.listdir("docs"):
            if os.path.isfile(os.path.join("docs", file)):
                shutil.copy(os.path.join("docs", file), os.path.join("dist", "docs", file))
    
    # Create a debug.bat file to help users troubleshoot
    with open(os.path.join("dist", "debug.bat"), "w") as f:
        f.write("@echo off\n")
        f.write("echo Running UrgotMatchupHelper with debug output...\n")
        f.write("echo Current directory: %CD%\n")
        f.write("echo Files in current directory:\n")
        f.write("dir\n")
        f.write("echo.\n")
        f.write("echo Running application...\n")
        f.write("UrgotMatchupHelper.exe --debug > debug_output.txt 2>&1\n")
        f.write("echo.\n")
        f.write("echo Application output saved to debug_output.txt\n")
        f.write("echo Press any key to view the output...\n")
        f.write("pause > nul\n")
        f.write("type debug_output.txt\n")
        f.write("echo.\n")
        f.write("echo Press any key to exit...\n")
        f.write("pause > nul\n")
    
    print("Build complete!")
    print(f"Executable created at: {os.path.abspath(os.path.join('dist', 'UrgotMatchupHelper.exe'))}")
    print("\nTo distribute the application:")
    print("1. Share the UrgotMatchupHelper.exe file")
    print("2. Make sure client_secrets.json is included in the distribution")
    print("3. Recipients need to have client_secrets.json in the same directory as the exe")
    print("4. The first time they run it, they'll need to authenticate with Google")
    print("\nIf matchups don't appear:")
    print("1. Run debug.bat to see detailed error messages")
    print("2. Check debug.log in the same directory for detailed information")
    print("3. Make sure all required authentication files are present:")
    print("   - client_secrets.json")
    print("   - token.json (will be created on first run)")

if __name__ == "__main__":
    build_executable()
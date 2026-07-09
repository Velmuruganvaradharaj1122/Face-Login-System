import os
import subprocess
import sys
import shutil

def run_cmd(cmd):
    print(f"Running: {cmd}")
    result = subprocess.run(cmd, shell=True)
    if result.returncode != 0:
        print(f"Command failed with exit code {result.returncode}")
        sys.exit(1)

def main():
    print("=== Building FaceAuth Enterprise ===")
    
    # 1. Clean previous builds
    if os.path.exists("build"):
        shutil.rmtree("build")
    if os.path.exists("dist"):
        shutil.rmtree("dist")
    
    # 2. PyArmor Obfuscation
    # We obfuscate app.py and everything in models/ and face/ and config/
    print("\n--- Obfuscating Code with PyArmor ---")
    run_cmd("pyarmor gen -O dist/obfuscated app.py models/*.py face/*.py config/*.py")
    
    # Copy necessary static/templates to the obfuscated dir so PyInstaller finds them
    shutil.copytree("templates", "dist/obfuscated/templates", dirs_exist_ok=True)
    shutil.copytree("static", "dist/obfuscated/static", dirs_exist_ok=True)
    if os.path.exists("haarcascade_frontalface_default.xml"):
        shutil.copy("haarcascade_frontalface_default.xml", "dist/obfuscated/")
    
    # 3. PyInstaller Bundling
    print("\n--- Bundling with PyInstaller ---")
    # Change dir to obfuscated so PyInstaller bundles the protected scripts
    os.chdir("dist/obfuscated")
    
    # Build command
    # --add-data "templates;templates" and "--add-data "static;static"
    # Note: On Windows it's ';' on Linux it's ':'
    sep = ';' if os.name == 'nt' else ':'
    
    pyinstaller_cmd = (
        f"pyinstaller --name FaceAuthServer "
        f"--add-data \"templates{sep}templates\" "
        f"--add-data \"static{sep}static\" "
        f"--add-data \"haarcascade_frontalface_default.xml{sep}.\" "
        f"--hidden-import flask "
        f"--hidden-import cv2 "
        f"--hidden-import face_recognition "
        f"--hidden-import numpy "
        f"--hidden-import pymysql "
        f"--hidden-import cryptography "
        f"--onefile app.py"
    )
    
    run_cmd(pyinstaller_cmd)
    
    # Move the final executable back to the root dist folder
    exe_name = "FaceAuthServer.exe" if os.name == 'nt' else "FaceAuthServer"
    os.chdir("../..")
    shutil.copy(f"dist/obfuscated/dist/{exe_name}", f"dist/{exe_name}")
    
    print("\n=== Build Complete! ===")
    print(f"Your protected executable is located at: dist/{exe_name}")
    print("You can distribute this file without exposing your source code.")

if __name__ == "__main__":
    main()

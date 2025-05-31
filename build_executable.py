#!/usr/bin/env python3
# ABOUTME: Build script for creating platform-specific executables
# ABOUTME: Uses PyInstaller to package the application

import os
import sys
import shutil
import subprocess
import platform

def clean_build_dirs():
    """Remove old build directories."""
    dirs_to_remove = ['build', 'dist', '__pycache__']
    for dir_name in dirs_to_remove:
        if os.path.exists(dir_name):
            print(f"Removing {dir_name}...")
            shutil.rmtree(dir_name)
    
    # Clean pycache in subdirectories
    for root, dirs, files in os.walk('.'):
        if '__pycache__' in dirs:
            pycache_path = os.path.join(root, '__pycache__')
            print(f"Removing {pycache_path}...")
            shutil.rmtree(pycache_path)

def install_requirements():
    """Install required packages."""
    print("Installing requirements...")
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'])

def build_executable():
    """Build the executable using PyInstaller."""
    print(f"Building executable for {platform.system()}...")
    
    # Basic PyInstaller command
    cmd = [
        sys.executable,
        '-m', 'PyInstaller',
        'librarian-assistant.spec',
        '--clean',
        '--noconfirm'
    ]
    
    # Run PyInstaller
    subprocess.check_call(cmd)
    
    print("Build complete!")
    
    # Show output location
    if platform.system() == 'Darwin':
        print(f"Application bundle created at: dist/Librarian-Assistant.app")
    elif platform.system() == 'Windows':
        print(f"Executable created at: dist/Librarian-Assistant.exe")
    else:
        print(f"Executable created at: dist/Librarian-Assistant")

def create_distribution_package():
    """Create a distribution package with the executable and documentation."""
    dist_dir = 'dist'
    package_dir = os.path.join(dist_dir, 'Librarian-Assistant-Package')
    
    if os.path.exists(package_dir):
        shutil.rmtree(package_dir)
    
    os.makedirs(package_dir)
    
    # Copy executable
    if platform.system() == 'Darwin':
        shutil.copytree(
            os.path.join(dist_dir, 'Librarian-Assistant.app'),
            os.path.join(package_dir, 'Librarian-Assistant.app')
        )
    elif platform.system() == 'Windows':
        shutil.copy2(
            os.path.join(dist_dir, 'Librarian-Assistant.exe'),
            package_dir
        )
    else:
        shutil.copy2(
            os.path.join(dist_dir, 'Librarian-Assistant'),
            package_dir
        )
    
    # Copy README if it exists
    if os.path.exists('README.md'):
        shutil.copy2('README.md', package_dir)
    
    # Create a simple run instructions file
    instructions = f"""
Librarian-Assistant - Hardcover.app Edition Viewer
=================================================

How to Run:
-----------
"""
    
    if platform.system() == 'Darwin':
        instructions += """
macOS:
1. Double-click Librarian-Assistant.app
2. If you see a security warning, right-click the app and select "Open"
3. Click "Open" in the dialog that appears
"""
    elif platform.system() == 'Windows':
        instructions += """
Windows:
1. Double-click Librarian-Assistant.exe
2. If Windows Defender shows a warning, click "More info" then "Run anyway"
"""
    else:
        instructions += """
Linux:
1. Make the file executable: chmod +x Librarian-Assistant
2. Run: ./Librarian-Assistant
"""
    
    instructions += """

First Time Setup:
-----------------
1. Launch the application
2. Click "Set Token" button
3. Enter your Hardcover.app Bearer token
4. Enter a Book ID and click "Fetch Data"

Requirements:
-------------
- Internet connection for API access
- Valid Hardcover.app Bearer token

"""
    
    with open(os.path.join(package_dir, 'RUN_INSTRUCTIONS.txt'), 'w') as f:
        f.write(instructions)
    
    print(f"Distribution package created at: {package_dir}")

def main():
    """Main build process."""
    print("Librarian-Assistant Build Script")
    print("================================")
    
    # Check if we're in the right directory
    if not os.path.exists('librarian_assistant'):
        print("Error: librarian_assistant directory not found.")
        print("Please run this script from the project root directory.")
        sys.exit(1)
    
    # Clean old builds
    clean_build_dirs()
    
    # Install requirements (optional)
    if '--install-deps' in sys.argv:
        install_requirements()
    
    # Build executable
    build_executable()
    
    # Create distribution package
    create_distribution_package()
    
    print("\nBuild completed successfully!")

if __name__ == '__main__':
    main()
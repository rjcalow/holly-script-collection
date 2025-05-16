# ~/holly-script-collection/path_setup.py
'''
Automate path setup for Python scripts in the project.

'''
import sys
import os


# Get the absolute path to the directory containing *this* file (path_setup.py)
# If path_setup.py is in the project root (~/holly-script-collection), this correctly
# identifies the project base directory.
project_base_dir = os.path.dirname(os.path.abspath(__file__))

# Get the user's home directory
home_dir = os.path.expanduser("~")

# Add project base directory and home directory to sys.path
# Insert at the beginning so they are searched first.
# Add the project base dir first, then the home dir.
# This ensures modules within your project (like those in 'common')
# are found, followed by the home directory for _secrets.py.
if project_base_dir not in sys.path:
    sys.path.insert(0, project_base_dir)

if home_dir not in sys.path:
    sys.path.insert(0, home_dir)

# --- End of the block being automated ---


# Note: This file intentionally has no functions or classes.
# Its purpose is solely to modify sys.path when it is imported.

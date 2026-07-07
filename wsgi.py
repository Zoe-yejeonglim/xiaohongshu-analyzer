# WSGI configuration for PythonAnywhere
import sys
import os

# Add project directory to path
project_home = '/home/YOUR_USERNAME/xiaohongshu-analyzer'
if project_home not in sys.path:
    sys.path.insert(0, project_home)

os.chdir(project_home)

from app import app as application

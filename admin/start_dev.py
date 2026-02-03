#!/usr/bin/env python3
"""
Development launcher for the admin panel.
Sets up environment variables and starts Flask in debug mode.
"""
import os
import subprocess
import sys

# Set development environment variables
os.environ['ADMIN_DEV_MODE'] = 'true'
os.environ['ADMIN_DEBUG'] = 'true'
os.environ['ADMIN_PORT'] = '5000'
os.environ['FLASK_SECRET_KEY'] = 'dev-secret-key'

# Change to admin directory
admin_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(admin_dir)

print("=" * 50)
print("Starting michaelbeijer.co.uk Admin Panel")
print("=" * 50)
print(f"Dev mode: ON (authentication bypassed)")
print(f"URL: http://localhost:5000")
print("=" * 50)

# Run Flask app
subprocess.run([sys.executable, 'app.py'])

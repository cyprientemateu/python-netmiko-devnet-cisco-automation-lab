"""
NetDevOps Compliance Dashboard — Production WSGI Entry Point

Used by Gunicorn to serve the Flask app in production mode.

Run with:
    gunicorn --workers 4 --bind 0.0.0.0:5000 "dashboard.wsgi:app"

Or from project root:
    gunicorn --workers 4 --bind 0.0.0.0:5000 --chdir . "dashboard.wsgi:app"
"""

import sys
import os

# Ensure project root is in path so imports resolve correctly
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dashboard.app import app

# Disable debug mode for production
app.debug = False

if __name__ == "__main__":
    app.run()
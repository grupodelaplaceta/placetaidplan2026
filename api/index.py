"""
PlacetaID - Vercel Serverless Entry Point
Main wsgi handler for Vercel
"""

import os
import sys

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

os.environ.setdefault('FLASK_ENV', 'production')

from app import create_app

# Configure for serverless environment
app = create_app('production')

# Vercel requires the app to be exported
# This is the WSGI handler that Vercel will call

"""
PlacetaID - Vercel Serverless Entry Point
"""

import os
import sys

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

os.environ.setdefault('FLASK_ENV', 'production')

from app import create_app

# Create Flask app for Vercel
app = create_app('production')

# Vercel will automatically detect and use this Flask app

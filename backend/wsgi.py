"""
WSGI entry point for production deployment
Used with Gunicorn or similar WSGI server
"""

import os
from app import create_app, db

# Use production config if not specified
config_name = os.getenv('FLASK_ENV', 'production')
app = create_app(config_name)


if __name__ == '__main__':
    app.run()

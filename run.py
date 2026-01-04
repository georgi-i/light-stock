#!/usr/bin/env python3
"""
IMS - Inventory Management System
Entry point for the application
"""
import os
import warnings

from app import create_app

# Create application instance
app = create_app(os.environ.get('FLASK_ENV', 'development'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)

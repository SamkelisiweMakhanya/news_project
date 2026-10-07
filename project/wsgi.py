"""
WSGI configuration for the Django project.

This module configures the Web Server Gateway Interface (WSGI)
application used to serve the Django project with WSGI-compatible
web servers.

The ``application`` object is exposed as a module-level variable and
serves as the entry point for WSGI deployments.

For more information, see:
https://docs.djangoproject.com/en/6.1/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

# Set the default Django settings module.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "project.settings")


# Create the WSGI application callable.
application = get_wsgi_application()

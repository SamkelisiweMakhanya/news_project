"""
ASGI configuration for the Django project.

This module configures the Asynchronous Server Gateway Interface (ASGI)
application used to serve the Django project with ASGI-compatible
web servers.

The ``application`` object is exposed as a module-level variable and
serves as the entry point for ASGI deployments.

For more information, see:
https://docs.djangoproject.com/en/6.1/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application

# Set the default Django settings module.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "project.settings")


# Create the ASGI application callable.
application = get_asgi_application()

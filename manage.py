#!/usr/bin/env python
"""
Django's command-line utility for administrative tasks.

This module provides the entry point for running Django management
commands, such as starting the development server, applying database
migrations, and creating superusers.
"""

import os
import sys


def main():
    """
    Run Django administrative tasks.

    Configures the Django settings module and executes the command
    supplied through the command line. If Django cannot be imported,
    an informative error message is raised.
    """
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "project.settings")

    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc

    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()

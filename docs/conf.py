import os
import sys
import django

sys.path.insert(0, os.path.abspath(".."))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "project.settings")
django.setup()

project = "News Application"
copyright = "2026, Samkelisiwe Makhanya"
author = "Samkelisiwe Makhanya"

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.viewcode",
    "sphinx.ext.napoleon",
]

templates_path = ["_templates"]
exclude_patterns = ["_build"]

html_theme = "sphinx_rtd_theme"
# html_static_path = ["_static"]

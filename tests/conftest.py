"""
pytest configuration for combined-query tests.

Sets DJANGO_SETTINGS_MODULE so pytest-django picks it up before collection.
"""
import django
from django.conf import settings


def pytest_configure(config):
    import os
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tests.settings_test")

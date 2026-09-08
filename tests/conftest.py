import pytest
from django.test import Client


@pytest.fixture
def client():
    return Client()


@pytest.fixture
def demo_settings(settings):
    settings.DEMO_MODE = True
    return settings

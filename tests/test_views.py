"""
Smoke tests for the IP-SAKTI Sahayak views.

These tests verify that every public page returns the expected HTTP status and
that the HTMX-only /assistant/ask/ endpoint enforces its access constraints.
"""
from __future__ import annotations

import uuid

import pytest
from django.test import Client
from django.urls import reverse


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def client():
    return Client()


# ── Page smoke tests ──────────────────────────────────────────────────────────

@pytest.mark.django_db
def test_home_200(client):
    """Homepage returns HTTP 200."""
    response = client.get(reverse('core:home'))
    assert response.status_code == 200


@pytest.mark.django_db
def test_chat_200(client):
    """Chat assistant page returns HTTP 200."""
    response = client.get(reverse('chat:chat'))
    assert response.status_code == 200


@pytest.mark.django_db
def test_corpus_about_200(client):
    """Corpus about page returns HTTP 200."""
    response = client.get(reverse('corpus:about'))
    assert response.status_code == 200


@pytest.mark.django_db
def test_wizard_start_200(client):
    """Wizard start page returns HTTP 200."""
    response = client.get(reverse('wizard:start'))
    assert response.status_code == 200


# ── /assistant/ask/ access control ───────────────────────────────────────────

@pytest.mark.django_db
def test_ask_requires_htmx(client):
    """POST /assistant/ask/ without an HX-Request header is rejected (400 or 405)."""
    response = client.post(
        reverse('chat:ask'),
        data={
            'question': 'What is a trademark?',
            'jurisdiction': 'india',
            'request_id': str(uuid.uuid4()),
        },
        # Deliberately omit the HX-Request header
    )
    assert response.status_code in (400, 405), (
        f"Expected 400 or 405 for non-HTMX POST, got {response.status_code}"
    )


@pytest.mark.django_db
def test_ask_demo_mode(client, settings):
    """POST /assistant/ask/ with a valid form and DEMO_MODE=True returns 200."""
    settings.DEMO_MODE = True

    response = client.post(
        reverse('chat:ask'),
        data={
            'question': 'What is the process for filing a trademark application in India?',
            'jurisdiction': 'india',
            'request_id': str(uuid.uuid4()),
        },
        HTTP_HX_REQUEST='true',          # Simulate HTMX header
        HTTP_HX_TARGET='answer-area',
    )
    assert response.status_code == 200

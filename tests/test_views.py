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
def test_screen_reader_access_200(client):
    """GIGW Screen Reader Access page lists assistive tech and is linked from chrome."""
    response = client.get(reverse('core:screen_reader'))
    assert response.status_code == 200
    html = response.content.decode()
    assert "Screen Reader Access" in html
    assert "NVDA" in html
    assert "JAWS" in html
    home = client.get(reverse('core:home'))
    home_html = home.content.decode()
    assert "/screen-reader/" in home_html
    assert 'class="gov-a11y-bar" role="toolbar"' not in home_html
    assert 'class="gov-a11y-bar"' in home_html
    assert 'id="sr-live"' in client.get(reverse('chat:chat')).content.decode()


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
def test_history_turn_restores_answer(client, settings):
    """GET /assistant/history/<i>/ reopens a stored session turn."""
    settings.DEMO_MODE = True
    session = client.session
    session["chat_history"] = [
        {
            "request_id": "11111111-1111-1111-1111-111111111111",
            "question": "What is Ayurveda Aahara under the 2022 regulations?",
            "answer": "Ayurveda Aahara is defined in the FSSAI 2022 regulations.",
            "citations": [],
            "state": "unable_to_answer",
            "confidence_note": "",
            "demo_mode": True,
        }
    ]
    session.save()
    response = client.get(reverse("chat:history_turn", args=[0]))
    assert response.status_code == 200
    html = response.content.decode()
    assert "Ayurveda Aahara" in html
    assert "FSSAI 2022" in html


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
        HTTP_HX_REQUEST='true',
        HTTP_HX_TARGET='answer-area',
    )
    assert response.status_code == 200
    html = response.content.decode()
    assert "answer-card" in html
    assert "ev-label" in html
    assert "demonstration" in html.lower() or "Patents Act" in html
    assert "{#" not in html
    assert 'id="chat-history-panel"' in html


@pytest.mark.django_db
def test_session_clear_htmx_redirects(client):
    """HTMX session clear returns 204 with HX-Redirect to chat (CSRF required)."""
    session = client.session
    session['chat_history'] = [{'question': 'q', 'state': 'demo'}]
    session.save()

    # Ensure csrftoken cookie exists the way a browser would have it.
    client.get(reverse('chat:chat'))
    csrf = client.cookies.get('csrftoken')
    assert csrf is not None

    response = client.post(
        reverse('chat:session_clear'),
        HTTP_HX_REQUEST='true',
        HTTP_X_CSRFTOKEN=csrf.value,
    )
    assert response.status_code == 204
    assert response['HX-Redirect'] == reverse('chat:chat')
    assert 'chat_history' not in client.session


@pytest.mark.django_db
def test_session_clear_requires_csrf(client):
    """Clear Session without CSRF token must fail (403) under enforced checks."""
    csrf_client = Client(enforce_csrf_checks=True)
    csrf_client.get(reverse('chat:chat'))
    response = csrf_client.post(
        reverse('chat:session_clear'),
        HTTP_HX_REQUEST='true',
    )
    assert response.status_code == 403


@pytest.mark.django_db
def test_health_200(client):
    """GET /health/ returns JSON readiness payload."""
    response = client.get(reverse('core:health'))
    assert response.status_code == 200
    data = response.json()
    assert data['status'] == 'ok'
    assert 'demo_mode' in data
    assert 'ollama_reachable' in data
    assert 'chroma_reachable' in data
    assert 'active_corpus_version' in data
    assert data['active_corpus_version'] not in ('', None)
    assert 'debug' in data


@pytest.mark.django_db
def test_home_hindi_nav_chrome(client):
    """Hindi language cookie translates nav/home/chat chrome (Django 5.2+)."""
    from django.conf import settings

    # Django 5.2 LocaleMiddleware reads LANGUAGE_COOKIE_NAME (not session alone).
    client.cookies[settings.LANGUAGE_COOKIE_NAME] = "hi"
    response = client.get(reverse('core:home'))
    assert response.status_code == 200
    html = response.content.decode()
    assert 'होम' in html
    assert 'IP-SAKTI से पूछें' in html
    chat = client.get(reverse('chat:chat'))
    assert chat.status_code == 200
    chat_html = chat.content.decode()
    assert 'सत्र साफ़ करें' in chat_html
    assert 'न्यायाधिकार' in chat_html


@pytest.mark.django_db
def test_feedback_htmx(client):
    """HTMX feedback POST saves a Feedback row and returns 204."""
    rid = uuid.uuid4()
    response = client.post(
        reverse('chat:feedback'),
        data={'request_id': str(rid), 'rating': 'up'},
        HTTP_HX_REQUEST='true',
    )
    assert response.status_code == 204
    from chat.models import Feedback
    assert Feedback.objects.filter(request_id=rid, rating='up').exists()


@pytest.mark.django_db
def test_chat_composer_is_input_not_textarea(client):
    """Chat page uses a single-line text input, not a textarea."""
    response = client.get(reverse('chat:chat'))
    html = response.content.decode()
    assert 'id="chat-question"' in html
    assert '<input' in html and 'id="chat-question"' in html
    assert '<textarea' not in html.lower()
    assert 'scene3d.js' not in html
    assert 'chat.js' not in html

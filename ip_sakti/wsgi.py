"""
WSGI config for IP-SAKTI Sahayak.
Exposes the WSGI callable as a module-level variable named ``application``.
Production: gunicorn ip_sakti.wsgi:application --workers 1 --threads 4
"""
from __future__ import annotations

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ip_sakti.settings")

application = get_wsgi_application()

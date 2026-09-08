"""
core/templatetags/ip_sakti_tags.py
Custom template tags and filters for IP-SAKTI Sahayak.
"""
from __future__ import annotations

from django import template
from django.utils.safestring import mark_safe

register = template.Library()


@register.filter(name="language_direction")
def language_direction(lang_code: str) -> str:
    """Return 'rtl' for RTL scripts, 'ltr' otherwise."""
    RTL_CODES = {"ur", "sd", "ks", "ar", "fa", "he"}
    return "rtl" if lang_code in RTL_CODES else "ltr"


@register.filter(name="outcome_label")
def outcome_label(outcome: str) -> str:
    """Convert internal outcome code to display label."""
    LABELS = {
        "grounded":               "Strong evidence",
        "evidence_only":          "Limited evidence",
        "unable_to_answer":       "Unable to answer from verified sources",
        "out_of_scope":           "Out of scope",
        "conflict":               "Conflicting sources",
        "busy":                   "Service busy — please retry",
        "unavailable":            "Service unavailable",
    }
    return LABELS.get(outcome, outcome.replace("_", " ").title())


@register.filter(name="outcome_css_class")
def outcome_css_class(outcome: str) -> str:
    """Return CSS modifier class for the ev-label component."""
    MAP = {
        "grounded":         "ev-label--strong",
        "evidence_only":    "ev-label--limited",
        "unable_to_answer": "ev-label--unable",
        "out_of_scope":     "ev-label--unable",
        "conflict":         "ev-label--limited",
        "busy":             "ev-label--unable",
        "unavailable":      "ev-label--unable",
    }
    return MAP.get(outcome, "ev-label--unable")


@register.simple_tag
def jurisdiction_label(code: str) -> str:
    return {"IN": "India", "INT": "International", "BOTH": "India + International"}.get(code, code)

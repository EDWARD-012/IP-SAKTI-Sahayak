"""
chat/forms.py — ChatForm
"""
from __future__ import annotations

from django import forms

JURISDICTION_CHOICES = [
    ("india",         "India"),
    ("international", "International"),
    ("both",          "India + International"),
]


class ChatForm(forms.Form):
    question = forms.CharField(
        max_length=1000,
        min_length=5,
        widget=forms.Textarea(
            attrs={
                "rows": 3,
                "placeholder": "Type your IP / regulatory question here… (e.g. 'Can I patent an Ayurvedic formulation?')",
                "id": "id_question",
                "class": "chat-input__textarea",
                "autocomplete": "off",
                "aria-label": "Your question",
            }
        ),
        error_messages={
            "required": "Please enter your question.",
            "min_length": "Question must be at least 5 characters.",
            "max_length": "Question must be 1000 characters or fewer.",
        },
    )
    jurisdiction = forms.ChoiceField(
        choices=JURISDICTION_CHOICES,
        initial="IN",
        widget=forms.Select(
            attrs={
                "id": "id_jurisdiction",
                "class": "chat-input__select",
                "aria-label": "Select jurisdiction",
            }
        ),
    )
    request_id = forms.UUIDField(
        required=False,
        widget=forms.HiddenInput(),
    )

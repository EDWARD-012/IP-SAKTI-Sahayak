"""
wizard/forms.py — Formulation Wizard step forms.
Each step is a single-question form for HTMX step-through.
"""
from __future__ import annotations

from django import forms

# ── Step 1: Product type ────────────────────────────────────────
PRODUCT_CHOICES = [
    ("classical_generic",    "Classical / generic Ayurvedic medicine"),
    ("patent_proprietary",   "Patent / proprietary medicine"),
    ("new_nonclassical",     "New / non-classical drug"),
    ("phytopharmaceutical",  "Phytopharmaceutical"),
    ("ayurveda_aahara",      "Ayurveda Aahara / nutraceutical"),
    ("cosmetic",             "Cosmetic"),
    ("unsure",               "Other / not sure"),
]

# ── Step 2: Intent ──────────────────────────────────────────────
INTENT_CHOICES = [
    ("protect",      "Protect my innovation (file IP)"),
    ("commercialize","Commercialise / license to industry"),
    ("prevent",      "Prevent bio-piracy / protect traditional knowledge"),
    ("understand",   "Understand rights before using a formulation"),
    ("export",       "Export to other countries (international IP)"),
    ("other",        "Other / unsure"),
]

# ── Step 3: Jurisdiction ────────────────────────────────────────
JURISDICTION_CHOICES = [
    ("IN",   "India only"),
    ("INT",  "International / export markets"),
    ("BOTH", "Both India and international"),
]

# ── Step 4: Prior IP ────────────────────────────────────────────
PRIOR_IP_CHOICES = [
    ("none",     "No prior IP — starting fresh"),
    ("patent",   "Have / had a patent application"),
    ("gi",       "Have / had a GI registration"),
    ("tkdl",     "Documented in TKDL or similar register"),
    ("unsure",   "Not sure"),
]


class WizardStep1Form(forms.Form):
    """What type of product are you working with?"""
    product_type = forms.ChoiceField(
        choices=PRODUCT_CHOICES,
        widget=forms.RadioSelect(attrs={"class": "wizard-radio"}),
        label="What best describes your product?",
    )


class WizardStep2Form(forms.Form):
    """What is your primary intent?"""
    intent = forms.ChoiceField(
        choices=INTENT_CHOICES,
        widget=forms.RadioSelect(attrs={"class": "wizard-radio"}),
        label="What is your primary goal?",
    )


class WizardStep3Form(forms.Form):
    """Which jurisdiction?"""
    jurisdiction = forms.ChoiceField(
        choices=JURISDICTION_CHOICES,
        widget=forms.RadioSelect(attrs={"class": "wizard-radio"}),
        label="Which markets / jurisdictions are relevant?",
    )


class WizardStep4Form(forms.Form):
    """Prior IP status."""
    prior_ip = forms.ChoiceField(
        choices=PRIOR_IP_CHOICES,
        widget=forms.RadioSelect(attrs={"class": "wizard-radio"}),
        label="Do you have any existing IP protection?",
    )

    notes = forms.CharField(
        required=False,
        max_length=500,
        widget=forms.Textarea(
            attrs={
                "rows": 3,
                "placeholder": "Optional: any additional details about your product or situation…",
                "class": "wizard-notes",
            }
        ),
        label="Additional notes (optional)",
    )


WIZARD_STEPS: dict[int, type[forms.Form]] = {
    1: WizardStep1Form,
    2: WizardStep2Form,
    3: WizardStep3Form,
    4: WizardStep4Form,
}

TOTAL_STEPS = len(WIZARD_STEPS)

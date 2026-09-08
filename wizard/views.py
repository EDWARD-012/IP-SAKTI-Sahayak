"""
wizard/views.py — Formulation Wizard views.

4-step guided wizard to help users identify relevant IP protection paths.
Uses HTMX for step-through navigation without full page reloads.
"""
from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from wizard.forms import TOTAL_STEPS, WIZARD_STEPS
from wizard.models import WizardSession

logger = logging.getLogger("ip_sakti")

_SESSION_KEY = "wizard_session_id"


def _get_or_create_session(request: HttpRequest) -> WizardSession:
    """Get existing WizardSession from session key, or create a new one."""
    session_id = request.session.get(_SESSION_KEY)
    if session_id:
        try:
            ws = WizardSession.objects.get(session_key=session_id)
            if not ws.is_expired:
                return ws
            ws.reset()
            return ws
        except WizardSession.DoesNotExist:
            pass

    # Create new
    ws = WizardSession.objects.create(
        session_key=str(request.session.session_key or "anon") + "_" + str(id(request)),
        expires_at=timezone.now() + timedelta(hours=24),
    )
    request.session[_SESSION_KEY] = ws.session_key
    return ws


def _step_context(step: int, ws: WizardSession) -> dict[str, Any]:
    """Build context dict for a wizard step."""
    form_class = WIZARD_STEPS[step]
    step_titles = {
        1: "Product Type",
        2: "Your Goal",
        3: "Jurisdiction",
        4: "Existing IP",
    }
    step_descriptions = {
        1: "What type of product are you working with?",
        2: "What is your primary objective?",
        3: "Which markets are relevant to you?",
        4: "Do you have any existing IP protection?",
    }
    form = form_class()
    return {
        "form": form,
        "step_form": form,          # alias used by wizard.html shell
        "step": step,
        "wizard_step": step,        # alias used by wizard.html progress bar
        "total_steps": TOTAL_STEPS,
        "progress_pct": int((step - 1) / TOTAL_STEPS * 100),
        "step_title": step_titles.get(step, f"Step {step}"),
        "step_description": step_descriptions.get(step, ""),
        "is_last_step": step == TOTAL_STEPS,
    }


def wizard_start(request: HttpRequest) -> HttpResponse:
    """GET /wizard/ — renders the wizard shell with step 1 form."""
    ws = _get_or_create_session(request)
    if ws.is_expired:
        ws.reset()

    ctx = _step_context(1, ws)
    ctx["wizard_session"] = ws
    return render(request, "wizard/wizard.html", ctx)


@require_POST
def wizard_step(request: HttpRequest) -> HttpResponse:
    """
    POST /wizard/step/ (HTMX) — validate current step, save answer, return next step partial.

    POST params:
        current_step   — int (1..TOTAL_STEPS)
        <step-specific fields>  — from the step form
    """
    if not getattr(request, "htmx", None):
        return redirect("wizard:start")

    try:
        current_step = int(request.POST.get("current_step", "1"))
    except ValueError:
        current_step = 1

    if current_step < 1 or current_step > TOTAL_STEPS:
        return HttpResponse("Invalid step.", status=400)

    ws = _get_or_create_session(request)
    if ws.is_expired:
        ws.reset()

    form_class = WIZARD_STEPS[current_step]
    form = form_class(request.POST)

    if not form.is_valid():
        # Return the same step with errors
        ctx = _step_context(current_step, ws)
        ctx["form"] = form
        ctx["wizard_session"] = ws
        return render(request, "wizard/_step_form.html", ctx, status=422)

    # Save answer
    ws.answers[f"step_{current_step}"] = form.cleaned_data
    next_step = current_step + 1

    if next_step > TOTAL_STEPS:
        ws.completed = True
        ws.current_step = TOTAL_STEPS
        ws.save()
        # Signal completion via HTMX redirect
        response = HttpResponse(status=204)
        response["HX-Redirect"] = "/wizard/result/"
        return response

    ws.current_step = next_step
    ws.save()

    ctx = _step_context(next_step, ws)
    ctx["wizard_session"] = ws
    return render(request, "wizard/_step_form.html", ctx)


def wizard_result(request: HttpRequest) -> HttpResponse:
    """GET /wizard/result/ — show personalised IP recommendations."""
    session_id = request.session.get(_SESSION_KEY)
    ws = None
    if session_id:
        try:
            ws = WizardSession.objects.get(session_key=session_id)
        except WizardSession.DoesNotExist:
            pass

    if not ws or not ws.completed:
        return redirect("wizard:start")

    recommendations = _build_recommendations(ws.answers)
    return render(request, "wizard/result.html", {
        "answers": ws.answers,
        "recommendations": recommendations,
        "wizard_session": ws,
    })


@require_POST
def wizard_reset(request: HttpRequest) -> HttpResponse:
    """POST /wizard/reset/ — reset wizard session."""
    session_id = request.session.get(_SESSION_KEY)
    if session_id:
        try:
            ws = WizardSession.objects.get(session_key=session_id)
            ws.reset()
        except WizardSession.DoesNotExist:
            pass
    return redirect("wizard:start")


def _build_recommendations(answers: dict[str, Any]) -> list[dict[str, Any]]:
    """
    Derive recommended IP protection paths from wizard answers.
    Returns a list of recommendation dicts with: title, description, ip_types, suggested_question.
    """
    step1 = answers.get("step_1", {})
    step2 = answers.get("step_2", {})
    step3 = answers.get("step_3", {})

    raw_product = step1.get("product_type", "unsure")
    # Map §3.1 product keys onto legacy recommendation buckets.
    _PRODUCT_ALIASES = {
        "classical_generic": "classical",
        "patent_proprietary": "novel",
        "new_nonclassical": "novel",
        "phytopharmaceutical": "extract",
        "ayurveda_aahara": "food",
        "cosmetic": "cosmetic",
        "unsure": "other",
        # legacy keys (if any old sessions remain)
        "classical": "classical",
        "novel": "novel",
        "plant": "plant",
        "extract": "extract",
        "food": "food",
        "other": "other",
    }
    product_type = _PRODUCT_ALIASES.get(raw_product, "other")
    intent       = step2.get("intent",       "other")
    jurisdiction = step3.get("jurisdiction", "IN")

    recs: list[dict[str, Any]] = []

    # ── Patent recommendations ────────────────────────────────
    if product_type in ("novel", "extract") and intent in ("protect", "commercialize"):
        recs.append({
            "icon": "📄",
            "title": "Patent Protection",
            "ip_type": "patent",
            "description": (
                "Your novel formulation or extract may be eligible for patent protection "
                "under the Patents Act, 1970, if it is novel, inventive, and industrially applicable. "
                "Note that classical Ayurvedic formulations may be excluded under Section 3(p)."
            ),
            "suggested_question": f"Can I patent a novel {raw_product.replace('_', ' ')} under the Patents Act 1970?",
            "relevant_law": "Patents Act 1970, Section 3(p), Section 2(1)(j)",
        })

    # ── GI recommendations ────────────────────────────────────
    if product_type in ("classical", "plant") and intent in ("protect", "prevent"):
        recs.append({
            "icon": "🌿",
            "title": "Geographical Indication (GI) Registration",
            "ip_type": "gi",
            "description": (
                "If your product originates from a specific geographical region of India and "
                "has qualities or reputation attributable to that origin, GI registration "
                "under the GI Act 1999 can protect it."
            ),
            "suggested_question": "How do I register a Geographical Indication for an Ayurvedic product?",
            "relevant_law": "Geographical Indications of Goods (Registration and Protection) Act, 1999",
        })

    # ── TKDL / defensive publication ─────────────────────────
    if product_type == "classical" and intent in ("prevent", "understand"):
        recs.append({
            "icon": "🛡️",
            "title": "Document in TKDL / Defensive Publication",
            "ip_type": "tkdl",
            "description": (
                "Classical Ayurvedic formulations documented in ancient texts can be protected "
                "from bio-piracy by ensuring they are documented in the Traditional Knowledge "
                "Digital Library (TKDL). This creates prior art that prevents wrongful patenting."
            ),
            "suggested_question": "How does TKDL prevent bio-piracy of traditional Ayurvedic formulations?",
            "relevant_law": "TKDL, Section 3(p) Patents Act 1970",
        })

    # ── Biodiversity / ABS ────────────────────────────────────
    if product_type in ("plant", "extract", "classical"):
        recs.append({
            "icon": "🌱",
            "title": "Biodiversity & Access Benefit Sharing (ABS)",
            "ip_type": "biodiversity",
            "description": (
                "Using biological resources from India requires compliance with the Biological "
                "Diversity Act 2002. You may need NBA approval and an Access Benefit Sharing "
                "agreement with the local community."
            ),
            "suggested_question": "Do I need NBA approval to use medicinal plants in my Ayurvedic product?",
            "relevant_law": "Biological Diversity Act 2002, Section 3 and 7; Nagoya Protocol",
        })

    # ── Regulatory classification ─────────────────────────────
    if product_type in ("cosmetic", "food", "classical"):
        recs.append({
            "icon": "📋",
            "title": "Regulatory Classification",
            "ip_type": "regulatory",
            "description": (
                "Ayurvedic products may fall under the Drugs & Cosmetics Act 1940, "
                "Ayurveda Aahara Regulations 2022 (for food products), or FSSAI regulations. "
                "Getting the classification right is essential before commercialisation."
            ),
            "suggested_question": "Is my Ayurvedic cosmetic product classified as a drug or cosmetic under the Drugs & Cosmetics Act?",
            "relevant_law": "Drugs & Cosmetics Act 1940, Ayurveda Aahara Regulations 2022",
        })

    # ── International ─────────────────────────────────────────
    if jurisdiction in ("INT", "BOTH") and intent == "export":
        recs.append({
            "icon": "🌍",
            "title": "International IP Protection",
            "ip_type": "international",
            "description": (
                "For export markets, consider filing a PCT (Patent Cooperation Treaty) application "
                "for patent protection, and check TRIPS obligations. The WIPO GRATK Treaty (2024) "
                "provides new protections for traditional knowledge internationally."
            ),
            "suggested_question": "How do I protect an Ayurvedic invention internationally under the PCT?",
            "relevant_law": "TRIPS Agreement (Article 27), PCT, WIPO GRATK Treaty 2024",
        })

    if not recs:
        recs.append({
            "icon": "💬",
            "title": "General IP Guidance",
            "ip_type": "general",
            "description": (
                "Based on your answers, the most relevant starting point is to understand "
                "your IP options. Use the Ask IP-SAKTI chat to explore specific questions."
            ),
            "suggested_question": "What IP protection options are available for Ayurvedic innovations?",
            "relevant_law": "Patents Act 1970, GI Act 1999, BD Act 2002",
        })

    return recs

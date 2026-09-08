"""
ai/translate.py — Optional IndicTrans2 translation adapter.

Falls back gracefully (returns text unchanged) when IndicTrans2 is not installed.
English is the default retrieval pivot: non-English queries are translated to English
before retrieval, and answers are translated back if needed.
"""
from __future__ import annotations

import logging

logger = logging.getLogger("ai")

# IndicTrans2 not installed by default (requires ctranslate2, sacremoses)
# Activate after corpus sprint: pip install ctranslate2 sacremoses
_it2_model: object | None = None
_it2_available: bool | None = None  # None = not yet checked


def _check_availability() -> bool:
    """Check once if IndicTrans2 dependencies are present."""
    global _it2_available
    if _it2_available is not None:
        return _it2_available
    try:
        import ctranslate2  # noqa: F401
        import sacremoses  # noqa: F401
        _it2_available = True
        logger.info("IndicTrans2 dependencies available.")
    except ImportError:
        _it2_available = False
        logger.info(
            "IndicTrans2 not installed (ctranslate2, sacremoses missing). "
            "Install to enable multilingual translation."
        )
    return _it2_available


# ── BCP-47 → IndicTrans2 language tag mapping ─────────────────
_LANG_MAP: dict[str, str] = {
    "hi":  "hin_Deva",
    "bn":  "ben_Beng",
    "te":  "tel_Telu",
    "mr":  "mar_Deva",
    "ta":  "tam_Taml",
    "ur":  "urd_Arab",
    "gu":  "guj_Gujr",
    "kn":  "kan_Knda",
    "ml":  "mal_Mlym",
    "or":  "ory_Orya",
    "pa":  "pan_Guru",
    "as":  "asm_Beng",
    "mai": "mai_Deva",
    "kok": "kok_Deva",
    "sat": "sat_Olck",
    "ks":  "kas_Arab",
    "ne":  "npi_Deva",
    "sd":  "snd_Arab",
    "doi": "doi_Deva",
    "mni": "mni_Mtei",
    "brx": "brx_Deva",
    "sa":  "san_Deva",
    "en":  "eng_Latn",
}

# Languages where IndicTrans2 quality is experimental (low-resource)
_PILOT_LANGUAGES = {"sat", "doi", "brx", "mni", "ks", "mai", "kok"}


def translate(text: str, source_lang: str, target_lang: str) -> str:
    """
    Translate *text* from *source_lang* to *target_lang*.

    - source_lang / target_lang are BCP-47 codes (e.g. "hi", "en")
    - If source and target are identical, returns text unchanged.
    - If IndicTrans2 is unavailable, returns text unchanged with a warning log.
    - Legal citation text and section numbers should NOT be translated — they are
      passed through unchanged (caller responsibility).

    Returns:
        Translated text string.
    """
    if source_lang == target_lang:
        return text

    if not text.strip():
        return text

    if not _check_availability():
        logger.debug(
            "translate: skipping %s→%s (IndicTrans2 not installed)", source_lang, target_lang
        )
        return text

    src_tag = _LANG_MAP.get(source_lang)
    tgt_tag = _LANG_MAP.get(target_lang)
    if not src_tag or not tgt_tag:
        logger.warning(
            "translate: unsupported language pair %s→%s, returning original text.",
            source_lang, target_lang,
        )
        return text

    try:
        # Lazy import and init IndicTrans2 model (first call only)
        global _it2_model
        if _it2_model is None:
            _it2_model = _init_model()

        translated = _it2_model.translate(text, src_tag, tgt_tag)  # type: ignore[union-attr]
        return translated
    except Exception as exc:
        logger.error("IndicTrans2 translation error: %s", exc)
        return text


def is_pilot(lang_code: str) -> bool:
    """Return True if *lang_code* is in the pilot/beta language set."""
    return lang_code in _PILOT_LANGUAGES


def _init_model() -> object:
    """
    Initialise IndicTrans2 model (called once, CPU-first).
    Returns a wrapper object with a translate(text, src, tgt) method.
    """
    # This is the stub initialisation path.
    # Real implementation: download from ai4bharat/indictrans2 on HuggingFace,
    # run with ctranslate2 in CPU mode (device="cpu").
    raise NotImplementedError(
        "IndicTrans2 model init not implemented. "
        "See IMPLEMENTATION_PLAN.md §22 for setup instructions."
    )

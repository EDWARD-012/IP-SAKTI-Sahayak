"""
ai/translate.py — Optional IndicTrans2 translation adapter.

Falls back gracefully (returns text unchanged) when IndicTrans2 is not installed.
English is the default retrieval pivot: non-English queries are translated to English
before retrieval, and answers are translated back if needed.
"""
from __future__ import annotations

import logging

logger = logging.getLogger("ai")

# IndicTrans2 not installed by default (heavy: torch + transformers + toolkit).
# Activate after corpus sprint:
#   pip install torch transformers
#   pip install git+https://github.com/VarunGumma/IndicTransToolkit
_it2_model: object | None = None
_it2_available: bool | None = None  # None = not yet checked


def _check_availability() -> bool:
    """Check once if IndicTrans2 dependencies are present."""
    global _it2_available
    if _it2_available is not None:
        return _it2_available
    try:
        import torch  # noqa: F401
        import transformers  # noqa: F401
        # IndicProcessor lives in IndicTransToolkit (import path varies by version)
        try:
            from IndicTransToolkit.processor import IndicProcessor  # noqa: F401
        except ImportError:
            from IndicTransToolkit import IndicProcessor  # noqa: F401
        _it2_available = True
        logger.info("IndicTrans2 dependencies available.")
    except ImportError:
        _it2_available = False
        logger.info(
            "IndicTrans2 not installed (torch / transformers / IndicTransToolkit "
            "missing). Install to enable multilingual translation."
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
    Initialise the IndicTrans2 wrapper (called once, CPU-first).
    Returns an object exposing ``translate(text, src_tag, tgt_tag)``.
    """
    return _IndicTrans2Wrapper()


# HuggingFace model IDs (1B distilled checkpoints — CPU-runnable).
_EN_INDIC_MODEL = "ai4bharat/indictrans2-en-indic-1B"
_INDIC_EN_MODEL = "ai4bharat/indictrans2-indic-en-1B"
_EN_TAG = "eng_Latn"


class _IndicTrans2Wrapper:
    """
    Thin wrapper around IndicTrans2 HF checkpoints.

    - Loads the en→indic and indic→en models lazily, only when a direction is
      first needed (keeps memory down on CPU-only boxes).
    - indic→indic is handled by pivoting through English (avoids a third model).
    - Runs fully on CPU with torch.no_grad(); safe to call from request threads
      because generation is serialised upstream by the generate-semaphore, and
      translation itself is short.
    """

    def __init__(self) -> None:
        import torch  # local import — only when translation is actually used

        try:
            from IndicTransToolkit.processor import IndicProcessor
        except ImportError:
            from IndicTransToolkit import IndicProcessor

        self._torch = torch
        self._processor = IndicProcessor(inference=True)
        self._device = "cpu"
        # Lazily populated: direction key -> (tokenizer, model)
        self._models: dict[str, tuple] = {}
        logger.info("IndicTrans2 wrapper initialised (CPU, lazy model loading).")

    def _get(self, model_id: str) -> tuple:
        """Load (and cache) tokenizer + model for *model_id*."""
        if model_id not in self._models:
            from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
            logger.info("Loading IndicTrans2 model %s (CPU) …", model_id)
            tok = AutoTokenizer.from_pretrained(model_id, trust_remote_code=True)
            mdl = AutoModelForSeq2SeqLM.from_pretrained(model_id, trust_remote_code=True)
            mdl.to(self._device).eval()
            self._models[model_id] = (tok, mdl)
        return self._models[model_id]

    def _translate_direction(self, text: str, src_tag: str, tgt_tag: str, model_id: str) -> str:
        tok, mdl = self._get(model_id)
        batch = self._processor.preprocess_batch([text], src_lang=src_tag, tgt_lang=tgt_tag)
        enc = tok(
            batch, truncation=True, padding="longest",
            return_tensors="pt", max_length=256,
        ).to(self._device)
        with self._torch.no_grad():
            out = mdl.generate(
                **enc, max_length=256, num_beams=5,
                num_return_sequences=1, use_cache=True,
            )
        decoded = tok.batch_decode(out, skip_special_tokens=True)
        result = self._processor.postprocess_batch(decoded, lang=tgt_tag)
        return result[0] if result else text

    def translate(self, text: str, src_tag: str, tgt_tag: str) -> str:
        if src_tag == tgt_tag:
            return text
        if src_tag == _EN_TAG:
            return self._translate_direction(text, src_tag, tgt_tag, _EN_INDIC_MODEL)
        if tgt_tag == _EN_TAG:
            return self._translate_direction(text, src_tag, tgt_tag, _INDIC_EN_MODEL)
        # indic → indic: pivot through English
        english = self._translate_direction(text, src_tag, _EN_TAG, _INDIC_EN_MODEL)
        return self._translate_direction(english, _EN_TAG, tgt_tag, _EN_INDIC_MODEL)

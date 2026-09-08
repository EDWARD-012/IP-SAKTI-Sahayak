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


def _patch_transformers_indictrans_compat() -> None:
    """Shims for IndicTrans2 + IndicTransToolkit on transformers 5.x."""
    import sys
    import types

    import transformers.tokenization_utils as tu

    if not hasattr(tu, "PreTrainedTokenizerBase"):
        from transformers.tokenization_utils_base import PreTrainedTokenizerBase

        tu.PreTrainedTokenizerBase = PreTrainedTokenizerBase  # type: ignore[attr-defined]

    # configuration_indictrans.py still imports transformers.onnx (removed in v5).
    if "transformers.onnx" not in sys.modules:
        onnx_mod = types.ModuleType("transformers.onnx")

        class _OnnxConfig:  # minimal stub — unused at inference time
            pass

        class _OnnxSeq2SeqConfigWithPast(_OnnxConfig):
            pass

        onnx_mod.OnnxConfig = _OnnxConfig  # type: ignore[attr-defined]
        onnx_mod.OnnxSeq2SeqConfigWithPast = _OnnxSeq2SeqConfigWithPast  # type: ignore[attr-defined]
        utils_mod = types.ModuleType("transformers.onnx.utils")

        def compute_effective_axis_dimension(*_a, **_k):  # noqa: ANN001
            return 1

        utils_mod.compute_effective_axis_dimension = compute_effective_axis_dimension  # type: ignore[attr-defined]
        sys.modules["transformers.onnx"] = onnx_mod
        sys.modules["transformers.onnx.utils"] = utils_mod


def _patch_indictrans_tokenizer_file(path: str) -> None:
    """Patch HF trust_remote_code tokenizer for transformers 5.x.

    Must init ``_special_tokens_map`` at the very start of ``__init__`` —
    IndicTrans assigns ``unk_token``/etc. before ``super().__init__()``, and
    transformers 5 ``__setattr__`` requires the map already.
    """
    from pathlib import Path

    p = Path(path)
    if not p.is_file():
        return
    text = p.read_text(encoding="utf-8")
    marker = "transformers>=5 expects this private map before special-token setattr"
    old_marker = "transformers>=5 expects this private map during PreTrainedTokenizer.__init__"
    old_block = (
        f"        # {old_marker}\n"
        "        self._special_tokens_map = {\n"
        '            "bos_token": self.bos_token,\n'
        '            "eos_token": self.eos_token,\n'
        '            "unk_token": self.unk_token,\n'
        '            "pad_token": self.pad_token,\n'
        "        }\n\n"
    )
    original = text
    if old_block in text:
        text = text.replace(old_block, "")
    if marker not in text:
        needle = (
            "    ):\n"
            "        self.src_vocab_fp = src_vocab_fp\n"
        )
        insert = (
            "    ):\n"
            f"        # {marker}\n"
            "        self._special_tokens_map = dict.fromkeys(self.SPECIAL_TOKENS_ATTRIBUTES)\n"
            "        self.src_vocab_fp = src_vocab_fp\n"
        )
        if needle not in text:
            logger.warning("Could not patch IndicTrans tokenizer at %s", p)
            if text != original:
                p.write_text(text, encoding="utf-8")
            return
        text = text.replace(needle, insert, 1)
        logger.info("Patched IndicTrans tokenizer for transformers 5: %s", p)
    if text != original:
        p.write_text(text, encoding="utf-8")


def _patch_indictrans_modeling_file(path: str) -> None:
    """Patch IndicTrans modeling for transformers 4.57+/5.x generate + tie_weights."""
    from pathlib import Path

    p = Path(path)
    if not p.is_file():
        return
    text = p.read_text(encoding="utf-8")
    original = text

    tie_marker = "transformers>=5 passes recompute_mapping to tie_weights"
    if tie_marker not in text:
        # Prefer upstream PR #130 shape: accept kwargs and do not re-tie under v5 init.
        old_tie = (
            "    def tie_weights(self):\n"
            "        if self.config.share_decoder_input_output_embed:\n"
            "            self._tie_or_clone_weights(self.model.decoder.embed_tokens, self.lm_head)\n"
        )
        old_tie_patched = (
            "    def tie_weights(self, missing_keys=None, recompute_mapping=True, **kwargs):\n"
            f"        # {tie_marker}\n"
            "        if self.config.share_decoder_input_output_embed:\n"
            "            self._tie_or_clone_weights(self.model.decoder.embed_tokens, self.lm_head)\n"
        )
        new_tie = (
            f"    def tie_weights(self, **kwargs):  # {tie_marker}\n"
            "        pass\n"
        )
        if old_tie_patched in text:
            text = text.replace(old_tie_patched, new_tie, 1)
        elif old_tie in text:
            text = text.replace(old_tie, new_tie, 1)
        elif "    def tie_weights(self):\n" in text:
            text = text.replace("    def tie_weights(self):\n", new_tie, 1)
        else:
            logger.warning("Could not patch IndicTrans tie_weights at %s", p)
    elif "self._tie_or_clone_weights(self.model.decoder.embed_tokens, self.lm_head)" in text:
        # Upgrade earlier partial patch to PR #130 no-op body
        import re

        text2, n = re.subn(
            r"    def tie_weights\(self(?:,[^)]*)?\):\n"
            r"(?:        #[^\n]*\n)?"
            r"        if self\.config\.share_decoder_input_output_embed:\n"
            r"            self\._tie_or_clone_weights\(self\.model\.decoder\.embed_tokens, self\.lm_head\)\n",
            f"    def tie_weights(self, **kwargs):  # {tie_marker}\n        pass\n",
            text,
            count=1,
        )
        if n:
            text = text2
        else:
            logger.warning("Could not upgrade IndicTrans tie_weights body at %s", p)

    cache_marker = "transformers>=4.57 EncoderDecoderCache opt-out"
    if cache_marker not in text:
        needle = (
            'class IndicTransForConditionalGeneration(IndicTransPreTrainedModel, GenerationMixin):\n'
            '    base_model_prefix = "model"\n'
        )
        insert = (
            'class IndicTransForConditionalGeneration(IndicTransPreTrainedModel, GenerationMixin):\n'
            '    base_model_prefix = "model"\n\n'
            '    @classmethod\n'
            f'    def _supports_default_dynamic_cache(cls):  # {cache_marker}\n'
            '        return False\n'
        )
        if needle in text:
            text = text.replace(needle, insert, 1)
        else:
            logger.warning("Could not patch IndicTrans cache opt-out at %s", p)

    if text != original:
        p.write_text(text, encoding="utf-8")
        logger.info("Patched IndicTrans modeling for transformers 5: %s", p)


def _patch_all_cached_indictrans_tokenizers() -> None:
    """Patch hub snapshots AND transformers_modules dynamic imports."""
    import os
    from pathlib import Path

    root = Path(os.environ.get("USERPROFILE", "")) / ".cache" / "huggingface"
    if not root.is_dir():
        return
    for p in root.rglob("tokenization_indictrans.py"):
        _patch_indictrans_tokenizer_file(str(p))
    for p in root.rglob("modeling_indictrans.py"):
        _patch_indictrans_modeling_file(str(p))


def _local_indictrans_snapshot(model_id: str) -> str:
    """Resolve/download snapshot and apply local remote-code patches (no hub overwrite)."""
    import os

    from huggingface_hub import snapshot_download

    local = snapshot_download(model_id, token=os.environ.get("HF_TOKEN"))
    from pathlib import Path

    snap = Path(local)
    _patch_indictrans_tokenizer_file(str(snap / "tokenization_indictrans.py"))
    _patch_indictrans_modeling_file(str(snap / "modeling_indictrans.py"))
    _patch_all_cached_indictrans_tokenizers()
    return local


def _check_availability() -> bool:
    """Check once if IndicTrans2 dependencies are present."""
    global _it2_available
    if _it2_available is not None:
        return _it2_available
    try:
        import torch  # noqa: F401
        import transformers  # noqa: F401
        _patch_transformers_indictrans_compat()
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


def _looks_degenerate(text: str) -> bool:
    """True if translation collapsed into heavy n-gram repetition (IT2+transformers5 failure mode)."""
    words = text.split()
    if len(words) < 6:
        return False
    from collections import Counter

    counts = Counter(words)
    top = counts.most_common(1)[0][1]
    return (top / len(words)) >= 0.35 or ("Convention Convention" in text)


def _translate_via_ollama(text: str, source_lang: str, target_lang: str) -> str | None:
    """CPU-friendly pivot via the already-running Ollama chat model."""
    try:
        from django.conf import settings

        from ai.generate import _call_ollama
    except Exception:
        return None

    lang_names = {
        "hi": "Hindi", "en": "English", "bn": "Bengali", "te": "Telugu",
        "mr": "Marathi", "ta": "Tamil", "ur": "Urdu", "gu": "Gujarati",
        "kn": "Kannada", "ml": "Malayalam", "or": "Odia", "pa": "Punjabi",
        "as": "Assamese", "ne": "Nepali", "sa": "Sanskrit",
    }
    src = lang_names.get(source_lang, source_lang)
    tgt = lang_names.get(target_lang, target_lang)
    prompt = (
        f"Translate the following text from {src} to {tgt}. "
        "Return ONLY the translation — no quotes, no explanation, no romanization notes.\n\n"
        f"{text}"
    )
    try:
        out = _call_ollama(
            prompt,
            model=settings.OLLAMA_MODEL,
            base_url=settings.OLLAMA_BASE_URL,
            timeout=min(float(getattr(settings, "OLLAMA_TIMEOUT", 180)), 90.0),
        ).strip()
        if not out or _looks_degenerate(out):
            return None
        return out
    except Exception as exc:
        logger.warning("Ollama translation failed: %s", exc)
        return None


def translate(text: str, source_lang: str, target_lang: str) -> str:
    """
    Translate *text* from *source_lang* to *target_lang*.

    - source_lang / target_lang are BCP-47 codes (e.g. "hi", "en")
    - If source and target are identical, returns text unchanged.
    - Prefer IndicTrans2 when it produces usable output; otherwise fall back to Ollama.
    - Legal citation text and section numbers should NOT be translated — they are
      passed through unchanged (caller responsibility).

    Returns:
        Translated text string.
    """
    if source_lang == target_lang:
        return text

    if not text.strip():
        return text

    src_tag = _LANG_MAP.get(source_lang)
    tgt_tag = _LANG_MAP.get(target_lang)
    if not src_tag or not tgt_tag:
        logger.warning(
            "translate: unsupported language pair %s→%s, returning original text.",
            source_lang, target_lang,
        )
        return text

    backend = ""
    try:
        from django.conf import settings

        backend = str(getattr(settings, "TRANSLATE_BACKEND", "") or "").strip().lower()
    except Exception:
        backend = ""

    # Explicit Ollama-only (demo-safe on transformers 5.x until IT2 upstream is green).
    if backend in {"ollama", "qwen"}:
        ollama = _translate_via_ollama(text, source_lang, target_lang)
        return ollama if ollama else text

    if backend in {"", "auto", "indictrans", "indictrans2"} and _check_availability():
        try:
            global _it2_model
            if _it2_model is None:
                _it2_model = _init_model()
            translated = _it2_model.translate(text, src_tag, tgt_tag)  # type: ignore[union-attr]
            if translated and translated != text and not _looks_degenerate(translated):
                return translated
            logger.warning(
                "IndicTrans2 output unusable for %s→%s; falling back to Ollama.",
                source_lang, target_lang,
            )
        except Exception as exc:
            logger.error("IndicTrans2 translation error: %s", exc)

    ollama = _translate_via_ollama(text, source_lang, target_lang)
    if ollama:
        return ollama
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

        _patch_transformers_indictrans_compat()
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
            _patch_transformers_indictrans_compat()
            from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

            local = _local_indictrans_snapshot(model_id)
            logger.info("Loading IndicTrans2 model %s from local snapshot (CPU) …", model_id)
            tok = AutoTokenizer.from_pretrained(
                local, trust_remote_code=True, local_files_only=True
            )
            mdl = AutoModelForSeq2SeqLM.from_pretrained(
                local, trust_remote_code=True, local_files_only=True
            )
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
        forced_bos = tok.src_encoder.get(tgt_tag) or tok.convert_tokens_to_ids(tgt_tag)
        with self._torch.no_grad():
            out = mdl.generate(
                **enc,
                max_length=256,
                num_beams=5,
                num_return_sequences=1,
                use_cache=True,
                forced_bos_token_id=forced_bos,
            )
        # Generated IDs are target-side; decode with tgt SPM/vocab (not src).
        tok._switch_to_target_mode()
        try:
            decoded = tok.batch_decode(out, skip_special_tokens=True)
        finally:
            tok._switch_to_input_mode()
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

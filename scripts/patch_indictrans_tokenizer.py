"""Patch all cached IndicTrans remote-code files for transformers 5.x.

Mirrors AI4Bharat/IndicTrans2 PR #130 plus tokenizer special-token map fix.
"""
from __future__ import annotations

import os
import re
from pathlib import Path

TOK_MARKER = "transformers>=5 expects this private map before special-token setattr"
OLD_TOK_MARKER = "transformers>=5 expects this private map during PreTrainedTokenizer.__init__"
OLD_TOK_BLOCK = (
    f"        # {OLD_TOK_MARKER}\n"
    "        self._special_tokens_map = {\n"
    '            "bos_token": self.bos_token,\n'
    '            "eos_token": self.eos_token,\n'
    '            "unk_token": self.unk_token,\n'
    '            "pad_token": self.pad_token,\n'
    "        }\n\n"
)
TOK_NEEDLE = "    ):\n        self.src_vocab_fp = src_vocab_fp\n"
TOK_INSERT = (
    "    ):\n"
    f"        # {TOK_MARKER}\n"
    "        self._special_tokens_map = dict.fromkeys(self.SPECIAL_TOKENS_ATTRIBUTES)\n"
    "        self.src_vocab_fp = src_vocab_fp\n"
)

TIE_MARKER = "transformers>=5 passes recompute_mapping to tie_weights"
TIE_RE = re.compile(
    r"    def tie_weights\(self(?:,[^)]*)?\):\n"
    r"(?:        #[^\n]*\n)?"
    r"(?:        if self\.config\.share_decoder_input_output_embed:\n"
    r"            self\._tie_or_clone_weights\(self\.model\.decoder\.embed_tokens, self\.lm_head\)\n"
    r"|        pass\n)?"
)
TIE_NEW = f"    def tie_weights(self, **kwargs):  # {TIE_MARKER}\n        pass\n"

CACHE_MARKER = "transformers>=4.57 EncoderDecoderCache opt-out"
CACHE_NEEDLE = (
    'class IndicTransForConditionalGeneration(IndicTransPreTrainedModel, GenerationMixin):\n'
    '    base_model_prefix = "model"\n'
)
CACHE_INSERT = (
    'class IndicTransForConditionalGeneration(IndicTransPreTrainedModel, GenerationMixin):\n'
    '    base_model_prefix = "model"\n\n'
    '    @classmethod\n'
    f'    def _supports_default_dynamic_cache(cls):  # {CACHE_MARKER}\n'
    '        return False\n'
)


def patch_tokenizer(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    if OLD_TOK_BLOCK in text:
        text = text.replace(OLD_TOK_BLOCK, "")
    if TOK_MARKER in text:
        path.write_text(text, encoding="utf-8")
        return "tok-already"
    if TOK_NEEDLE not in text:
        path.write_text(text, encoding="utf-8")
        return "tok-missing"
    path.write_text(text.replace(TOK_NEEDLE, TOK_INSERT, 1), encoding="utf-8")
    return "tok-patched"


def patch_model(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    statuses: list[str] = []

    if TIE_MARKER in text and "        pass\n" in text[text.find("def tie_weights") : text.find("def tie_weights") + 200]:
        statuses.append("tie-ok")
    else:
        new_text, n = TIE_RE.subn(TIE_NEW, text, count=1)
        if n:
            text = new_text
            statuses.append("tie")
        elif "    def tie_weights(self):\n" in text:
            text = text.replace("    def tie_weights(self):\n", TIE_NEW, 1)
            statuses.append("tie-sig")
        else:
            statuses.append("tie-missing")

    if CACHE_MARKER in text:
        statuses.append("cache-ok")
    elif CACHE_NEEDLE in text:
        text = text.replace(CACHE_NEEDLE, CACHE_INSERT, 1)
        statuses.append("cache")
    else:
        statuses.append("cache-missing")

    path.write_text(text, encoding="utf-8")
    return "mdl:" + ",".join(statuses)


def main() -> None:
    root = Path(os.environ["USERPROFILE"]) / ".cache" / "huggingface"
    for p in root.rglob("tokenization_indictrans.py"):
        print(patch_tokenizer(p), p)
    for p in root.rglob("modeling_indictrans.py"):
        print(patch_model(p), p)


if __name__ == "__main__":
    main()

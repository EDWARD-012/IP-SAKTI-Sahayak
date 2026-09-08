# Optional IndicTrans2 enablement

Models cached locally after gated Agree + `HF_TOKEN`:

- `ai4bharat/indictrans2-indic-en-1B`
- `ai4bharat/indictrans2-en-indic-1B`

Adapter: `ai/translate.py` (transformers 5 remote-code patches + Ollama fallback).

Token: `.env` → `HF_TOKEN` (gitignored). **Revoke any token that was pasted in chat** and create a fresh one.

## Status (transformers 5.16)

Load path works after local patches (`tokenization_indictrans.py` special-token map,
`tie_weights(**kwargs)`, `_supports_default_dynamic_cache → False`).

**Inference quality is still broken** on this stack (degenerate “Convention…”
repetition even under teacher forcing). sentence-transformers 6 requires
`transformers>=5`, so we cannot pin 4.x in the same venv.

## Demo backend

`.env`:

```
TRANSLATE_BACKEND=ollama
```

(or omit / `auto` — IndicTrans is tried first, then Ollama if output looks degenerate)

Smoke: Hindi → English via `translate()` should return English through Ollama
while the jury laptop already has Qwen warm.

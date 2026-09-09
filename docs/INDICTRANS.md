# Optional IndicTrans2 enablement

IP-SAKTI can use IndicTrans2 for query/answer translation. Default production
path uses Ollama (`TRANSLATE_BACKEND=ollama` or `auto`).

## Models

After Hugging Face access + `HF_TOKEN` in `.env`:

- `ai4bharat/indictrans2-indic-en-1B`
- `ai4bharat/indictrans2-en-indic-1B`

Adapter: `ai/translate.py`.

## Configuration

```env
TRANSLATE_BACKEND=ollama
# or: auto | indictrans2
HF_TOKEN=
```

With `auto`, IndicTrans2 is tried first; if output looks degenerate the pipeline
falls back to Ollama.

## Notes

- `HF_TOKEN` must never be committed (`.env` is gitignored).
- sentence-transformers 6 expects `transformers>=5`; pin choices affect both
  embeddings and IndicTrans2 in the same environment.
- For jury demos, keep Qwen warm and prefer the Ollama translation backend.

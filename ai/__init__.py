"""
ai/ — IP-SAKTI RAG Pipeline package.

Sub-modules:
  pipeline   — main coordinator (process_question)
  retrieve   — Chroma vector search
  generate   — Ollama generation with concurrency semaphore
  citations  — citation validation against retrieved chunks
  safety     — deterministic input/output safety checks
  translate  — optional IndicTrans2 adapter

When DEMO_MODE=True (settings.py), all modules return stub/placeholder results
so the Django app runs without Ollama or a Chroma index.
"""

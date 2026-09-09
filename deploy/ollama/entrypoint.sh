#!/bin/sh
# Start Ollama, pull SIH model once (cached on volume), keep serving.
set -eu

MODEL="${OLLAMA_MODEL:-qwen2.5:3b-instruct-q4_K_M}"

ollama serve &
pid=$!

# Wait until API accepts connections
i=0
while [ "$i" -lt 60 ]; do
  if ollama list >/dev/null 2>&1; then
    break
  fi
  i=$((i + 1))
  sleep 1
done

echo "Pulling model: ${MODEL}"
ollama pull "${MODEL}" || echo "Model pull failed (will retry on next restart)"
echo "Ollama ready with: $(ollama list 2>/dev/null || true)"

wait "$pid"

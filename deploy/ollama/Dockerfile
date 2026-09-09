# Cloud Ollama for IP-SAKTI (Railway / Docker)
# Persists models on a volume mounted at /root/.ollama
FROM ollama/ollama:latest

ENV OLLAMA_HOST=0.0.0.0:11434
ENV OLLAMA_ORIGINS=*
ENV OLLAMA_MODEL=qwen2.5:3b-instruct-q4_K_M

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 11434
ENTRYPOINT ["/entrypoint.sh"]

# IP-SAKTI Sahayak (SIH26045)

Workspace: `C:\IP-SAKTI-Sahayak`

IP-SAKTI Sahayak is an India-first, multilingual information assistant for
Ayurveda-related intellectual property, traditional knowledge, biodiversity/
ABS and regulatory questions. It uses a versioned official-source corpus and
server-validated citations, and refuses questions that cannot be answered
safely. The MVP is designed for a six-member SIH team and an offline-capable
demonstration; it is not a substitute for legal, regulatory or medical advice.

**Build guide:** [IMPLEMENTATION_PLAN.md](./IMPLEMENTATION_PLAN.md) — **v4.3**

**End-user guide:** [USER_GUIDE.md](./USER_GUIDE.md)

**Audit resolution:** [AUDIT_RESOLUTION.md](./AUDIT_RESOLUTION.md)

### v4.3 MVP stack (no OpenAI / no Gemini)
Django + HTMX + small vanilla JavaScript · thin LangChain · Chroma · bge-m3 ·
**Qwen2.5-7B (Ollama)** · optional IndicTrans2 · SQLite

Advanced retrieval, extra services, fine-tuning and equal-quality support
across all 22 Eighth Schedule languages are gated behind evaluation results.

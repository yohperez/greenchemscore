# ╔══════════════════════════════════════════════════════════════════════╗
# ║  GreenChem Score — Dockerfile                                        ║
# ║  Imagen Docker para despliegue en Streamlit Cloud / Docker Hub      ║
# ╚══════════════════════════════════════════════════════════════════════╝

FROM python:3.11-slim

# ── Metadata ───────────────────────────────────────────────────────────
LABEL maintainer="tu-email@example.com"
LABEL org.opencontainers.image.title="GreenChem Score"
LABEL org.opencontainers.image.description="Pipeline ETL para clasificación química sostenible"
LABEL org.opencontainers.image.source="https://github.com/tu-usuario/greenchemscore"

# ── Dependencias del sistema ─────────────────────────────────────────
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libsqlite3-dev \
    && rm -rf /var/lib/apt/lists/*

# ── Directorio de trabajo ──────────────────────────────────────────────
WORKDIR /app

# ── Instalar dependencias Python ───────────────────────────────────────
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ── Copiar código fuente ─────────────────────────────────────────────
COPY app.py .
COPY .streamlit/ .streamlit/

# ── Puerto y healthcheck ─────────────────────────────────────────────
EXPOSE 8501
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health || exit 1

# ── Comando de inicio ──────────────────────────────────────────────────
ENTRYPOINT ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]

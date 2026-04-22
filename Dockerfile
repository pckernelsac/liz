FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PORT=5000 \
    FORWARDED_ALLOW_IPS=* \
    SESSION_COOKIE_SECURE=1

WORKDIR /app

# Dependencias del sistema (Pillow necesita libjpeg/zlib; psycopg2-binary trae libpq)
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        libjpeg-dev \
        zlib1g-dev \
        curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
# SessionMiddleware necesita itsdangerous; Jinja2Templates necesita jinja2 (no vienen como deps obligatorias de starlette).
RUN pip install --no-cache-dir -r requirements.txt \
    && python -c "import itsdangerous, jinja2; import starlette.middleware.sessions; from starlette.templating import Jinja2Templates"

COPY . .

# Carpetas que la app escribe en runtime
RUN mkdir -p uploads logs static/img tmp

EXPOSE 5000

HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
    CMD curl -fsS "http://127.0.0.1:${PORT}/" || exit 1

# Tras Nginx/Traefik de EasyPanel: confiar X-Forwarded-Proto para cookies de sesión (HTTPS).
# En EasyPanel, define PORT en las env vars (5000 por defecto) y expón ese puerto.
CMD ["sh", "-c", "uvicorn app:app --host 0.0.0.0 --port ${PORT} --proxy-headers"]

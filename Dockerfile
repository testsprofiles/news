FROM python:3.11-slim

# Deterministic, quiet and production-friendly Python behaviour.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    FLASK_DEBUG=False \
    PORT=5000

WORKDIR /app

# psycopg2-binary / bcrypt ship manylinux wheels, so no build toolchain needed.
COPY requirements.txt ./
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY . .

RUN mkdir -p uploads \
 && chmod +x docker-entrypoint.sh

EXPOSE 5000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:'+__import__('os').getenv('PORT','5000')+'/').status==200 else 1)" || exit 1

# The entrypoint waits for PostgreSQL, applies yoyo migrations and starts gunicorn.
CMD ["/bin/sh", "docker-entrypoint.sh"]

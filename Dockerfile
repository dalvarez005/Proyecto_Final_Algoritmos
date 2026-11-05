# Expedientes Confidenciales: Flask servido con Gunicorn.
FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1 \
    EXPEDIENTES_JSON=/app/data/expedientes.json
WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-compile -r requirements.txt gunicorn==23.0.0

COPY expedientes-confidenciales/app.py ./
COPY expedientes-confidenciales/algoritmos ./algoritmos
COPY expedientes-confidenciales/templates ./templates
COPY expedientes-confidenciales/static ./static
COPY expedientes-confidenciales/data/expedientes_ejemplo.json ./ejemplo/expedientes.json
COPY docker-entrypoint.sh /usr/local/bin/

RUN mkdir -p /app/data && chown 1000:1000 /app/data
USER 1000:1000
EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8080/salud').status == 200 else 1)"

ENTRYPOINT ["docker-entrypoint.sh"]
# Un solo worker: el JSON se lee y escribe en cada petición, sin bloqueo entre procesos.
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "1", "--threads", "4", "--access-logfile", "-", "app:app"]

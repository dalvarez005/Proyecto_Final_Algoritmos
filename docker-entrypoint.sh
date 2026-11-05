#!/bin/sh
# Si el volumen de datos está vacío, arranca con los expedientes de ejemplo.
set -e
if [ ! -f "$EXPEDIENTES_JSON" ]; then
    mkdir -p "$(dirname "$EXPEDIENTES_JSON")"
    cp /app/ejemplo/expedientes.json "$EXPEDIENTES_JSON"
fi
exec "$@"

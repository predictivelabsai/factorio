#!/usr/bin/env sh
set -e

if [ "${SKIP_MIGRATE:-0}" != "1" ]; then
    echo "[entrypoint] running db.migrate"
    python -m db.migrate
fi

exec "$@"

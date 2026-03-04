#!/bin/sh
set -e

# =============================================================================
# UpdatEngine entrypoint — Gunicorn + Nginx stack
# =============================================================================

# ---------------------------------------------------------------------------
# 1. Secret key management
# ---------------------------------------------------------------------------
SECRET_KEY_FILE=./secret_key
if [ -z "$SECRET_KEY" ]; then
    if [ ! -f "$SECRET_KEY_FILE" ]; then
        echo "[entrypoint] Generating a new SECRET_KEY"
        dd bs=48 count=1 if=/dev/urandom 2>/dev/null | base64 > "$SECRET_KEY_FILE"
        chmod go-r "$SECRET_KEY_FILE"
    fi
    export SECRET_KEY=$(cat "$SECRET_KEY_FILE")
else
    echo "$SECRET_KEY" > "$SECRET_KEY_FILE"
fi

# ---------------------------------------------------------------------------
# 2. Generate settings.py from template
# ---------------------------------------------------------------------------
echo "[entrypoint] Generating settings.py"
envsubst < ./updatengine/settings.py.in > ./updatengine/settings.py

# Add 127.0.0.1 to ALLOWED_HOSTS (required for Docker healthcheck)
sed -i "s|^ALLOWED_HOSTS = \[|ALLOWED_HOSTS = ['127.0.0.1',|" ./updatengine/settings.py

# ---------------------------------------------------------------------------
# 3. Optional custom settings_local.py overlay
# ---------------------------------------------------------------------------
if [ -f ./install/docker/custom.dist/settings_local.py ]; then
    cp ./install/docker/custom.dist/settings_local.py ./updatengine/settings_local.py
elif [ -f ./updatengine/settings_local.py ]; then
    rm ./updatengine/settings_local.py
fi

# ---------------------------------------------------------------------------
# 4. Collect static files
# ---------------------------------------------------------------------------
echo "[entrypoint] Collecting static files"
python manage.py collectstatic --clear --noinput --verbosity=0

# ---------------------------------------------------------------------------
# 5. Apply database migrations
# ---------------------------------------------------------------------------
echo "[entrypoint] Running database migrations"
python manage.py migrate --noinput

# ---------------------------------------------------------------------------
# 6. Load initial data (only if DB is empty)
# ---------------------------------------------------------------------------
ROW_COUNT=$(echo 'SELECT COUNT(*) FROM configuration_globalconfig;' \
    | python manage.py dbshell 2>/dev/null \
    | grep -E '^[0-9]+$' || echo "0")
if [ "$ROW_COUNT" = "0" ]; then
    echo "[entrypoint] Loading initial data"
    python manage.py loaddata initial_data/configuration_initial_data.yaml
    python manage.py loaddata initial_data/groups_initial_data.yaml
fi

# ---------------------------------------------------------------------------
# 7. Start Gunicorn using gunicorn.conf.py
# ---------------------------------------------------------------------------
echo "[entrypoint] Starting Gunicorn (workers=$(python -c 'import multiprocessing; print(multiprocessing.cpu_count()*2+1)'), config=gunicorn.conf.py)"
exec gunicorn updatengine.wsgi:application -c ./install/docker/gunicorn.conf.py

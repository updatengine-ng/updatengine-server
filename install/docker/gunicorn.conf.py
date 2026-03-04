# =============================================================================
# Gunicorn configuration — UpdatEngine Server
# =============================================================================
# Docs: https://docs.gunicorn.org/en/stable/settings.html

import multiprocessing
import os

# ---------------------------------------------------------------------------
# Server socket
# ---------------------------------------------------------------------------
bind = "0.0.0.0:8000"
backlog = 2048

# ---------------------------------------------------------------------------
# Worker processes
# Formula: (2 * CPU) + 1  — good default for I/O-bound Django apps
# ---------------------------------------------------------------------------
workers = int(os.environ.get("GUNICORN_WORKERS", multiprocessing.cpu_count() * 2 + 1))
worker_class = "sync"
worker_connections = 1000
threads = int(os.environ.get("GUNICORN_THREADS", 2))

# ---------------------------------------------------------------------------
# Timeouts
# ---------------------------------------------------------------------------
# 120s for large file uploads (UpdatEngine handles big packages)
timeout = int(os.environ.get("GUNICORN_TIMEOUT", 120))
graceful_timeout = 30
keepalive = 5

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
accesslog = "-"       # stdout — captured by Docker
errorlog  = "-"       # stderr — captured by Docker
loglevel  = os.environ.get("GUNICORN_LOG_LEVEL", "info")
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# ---------------------------------------------------------------------------
# Process naming
# ---------------------------------------------------------------------------
proc_name = "updatengine"

# ---------------------------------------------------------------------------
# Security
# ---------------------------------------------------------------------------
limit_request_line   = 8190   # max URL length (bytes)
limit_request_fields = 200

# ---------------------------------------------------------------------------
# Reliability
# ---------------------------------------------------------------------------
# Restart workers after this many requests (prevents memory leaks)
max_requests = int(os.environ.get("GUNICORN_MAX_REQUESTS", 1000))
max_requests_jitter = 100     # randomise so workers don't all restart at once

# Preload app to share memory across workers (faster startup, less RAM)
preload_app = True

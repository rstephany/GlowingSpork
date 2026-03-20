import multiprocessing
import yaml
import os

# Load settings from app.yml
with open(os.path.join(os.path.dirname(__file__), "config", "app.yml")) as f:
    cfg = yaml.safe_load(f)

# Server socket
bind    = f"{cfg['app']['host']}:{cfg['app']['port']}"

# Worker processes — 2 per CPU core is a good default
workers = multiprocessing.cpu_count() * 2 + 1

# Worker class (sync is fine; use 'gevent' or 'uvicorn.workers.UvicornWorker' for async)
worker_class = "sync"

# Logging
accesslog = "-"   # stdout
errorlog  = "-"   # stderr
loglevel  = "info"

# Reload on code changes (dev only — remove in production)
reload = cfg["app"].get("debug", False)

# Timeouts
timeout          = 30
keepalive        = 5
graceful_timeout = 30

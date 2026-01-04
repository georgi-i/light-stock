"""
Gunicorn configuration for IMS
Optimized for AWS Lightsail $3.50-$5 tier (512MB-1GB RAM)
"""

import multiprocessing
import os

# Server socket
# Using Unix socket in /run for better compatibility with systemd security
bind = "unix:/run/ims/ims.sock"
backlog = 2048

# Worker processes
# For 512MB RAM: 2 workers
# For 1GB RAM: 3 workers
workers = 2
worker_class = "sync"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 50
timeout = 30
keepalive = 2

# Logging
accesslog = "/home/ims/logs/access.log"
errorlog = "/home/ims/logs/error.log"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'

# Process naming
proc_name = "ims-gunicorn"

# Server mechanics
daemon = False
pidfile = "/home/ims/logs/gunicorn.pid"
umask = 0
user = None
group = None
tmp_upload_dir = None

# SSL (if needed)
# keyfile = None
# certfile = None

# Preload app for better performance
preload_app = True

# Security
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190

def on_starting(server):
    """Called just before the master process is initialized."""
    print("Starting IMS application...")

def on_reload(server):
    """Called to recycle workers during a reload via SIGHUP."""
    print("Reloading IMS application...")

def when_ready(server):
    """Called just after the server is started."""
    print("IMS application ready to serve requests")

def on_exit(server):
    """Called just before exiting Gunicorn."""
    print("Shutting down IMS application...")

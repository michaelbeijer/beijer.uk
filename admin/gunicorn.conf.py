import os


# Read the Railway-assigned port directly from environment variables.
bind = f"0.0.0.0:{os.getenv('PORT', '8080')}"

# Keep worker count conservative for small containers.
workers = int(os.getenv("WEB_CONCURRENCY", "2"))
threads = int(os.getenv("GUNICORN_THREADS", "2"))


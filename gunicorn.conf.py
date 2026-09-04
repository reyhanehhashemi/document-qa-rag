import os


bind = "0.0.0.0:8000"

workers = int(
    os.getenv(
        "GUNICORN_WORKERS",
        "1",
    )
)

threads = int(
    os.getenv(
        "GUNICORN_THREADS",
        "2",
    )
)

worker_class = "gthread"

timeout = int(
    os.getenv(
        "GUNICORN_TIMEOUT",
        "180",
    )
)

graceful_timeout = int(
    os.getenv(
        "GUNICORN_GRACEFUL_TIMEOUT",
        "30",
    )
)

keepalive = int(
    os.getenv(
        "GUNICORN_KEEPALIVE",
        "5",
    )
)

accesslog = "-"
errorlog = "-"
capture_output = True

loglevel = os.getenv(
    "GUNICORN_LOG_LEVEL",
    "info",
)
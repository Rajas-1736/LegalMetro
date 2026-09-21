import os
import socket
from celery import Celery
from app.config import settings

def is_celery_available() -> bool:
    """Fast check to verify if Redis broker is actively running."""
    try:
        host_port = settings.REDIS_URL.replace("redis://", "").split("/")[0]
        host, port = (host_port.split(":") + ["6379"])[:2]
        with socket.create_connection((host, int(port)), timeout=0.15):
            return True
    except Exception:
        return False

celery_app = Celery(
    "legalmetro_tasks",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.tasks.scan_worker"]
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300, # 5 minutes max per scan
    broker_connection_retry_on_startup=False,
    broker_connection_max_retries=1,
)

from celery import Celery

from app.core.config import settings

celery_app = Celery(
    "agentops",
    broker=settings.celery_broker_url,
    include=["app.workers.tasks"],
)


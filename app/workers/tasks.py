from app.workers.celery_app import celery_app

@celery_app.task(name="app.workers.tasks.smoke_task")
def smoke_task(message: str)-> str:
    return f"smoke:{message}"
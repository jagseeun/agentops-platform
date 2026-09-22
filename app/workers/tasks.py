from app.workers.celery_app import celery_app
from app.workers.run_worker import process_run

@celery_app.task(name="app.workers.tasks.smoke_task")
def smoke_task(message: str)-> str:
    return f"smoke:{message}"

@celery_app.task(name="app.workers.tasks.process_run_task")
def process_run_task(run_id: int)->None:
    process_run(run_id)
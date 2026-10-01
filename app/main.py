from uuid import uuid4

from fastapi import FastAPI, HTTPException, Request, status
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.api.routes.workspaces import router as workspaces_router
from app.api.routes.agents import router as agent_router
from app.api.routes.runs import router as runs_router
from app.db.session import engine

app = FastAPI(title="AgentOps Mini Platform")

REQUEST_ID_HEADER = "X-Request-Id"

@app.middleware("http")
async def add_request_id_header(request: Request, call_next):
    request_id = request.headers.get(REQUEST_ID_HEADER)
    if request_id is None:
        request_id = str(uuid4())
    response = await call_next(request)
    response.headers[REQUEST_ID_HEADER] = request_id
    return response

app.include_router(workspaces_router)
app.include_router(agent_router)
@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status" : "ok"}
@app.get("/health/live")
def health_live()->dict[str,str]:
    return {"status":"ok"}
@app.get("/health/ready")
def health_ready()->dict[str,str]:
    try:
        with engine.connect() as connection:
            connection.execute(text("select 1"))
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="database unavailable",
        ) from exc
    return {"status":"ok"}
app.include_router(runs_router)
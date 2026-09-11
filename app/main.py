from fastapi import FastAPI

from app.db.base import Base
from app.db.session import engine

from app.api.routes.workspaces import router as workspaces_router
from app.api.routes.agents import router as agent_router

from app.api.routes.runs import router as runs_router
Base.metadata.create_all(bind=engine)

app = FastAPI(title="AgentOps Mini Platform")

app.include_router(workspaces_router)
app.include_router(agent_router)
@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status" : "ok"}

app.include_router(runs_router)
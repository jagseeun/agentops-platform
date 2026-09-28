from decimal import Decimal
import pytest
from app.db.session import SessionLocal
from app.models.model_call import ModelCall
from app.models.workspace import Workspace
from app.services.model_gateway import ModelGateway
from app.repositories.model_call_repository import ModelCallRepository

from uuid import uuid4
from fastapi import HTTPException

def create_workspace(db, name: str = "Model Gateway Workspace")->int:
    workspace = Workspace(
        name=name,
        slug=f"model-gateway-{uuid4().hex}",
    )
    db.add(workspace)
    db.commit()
    db.refresh(workspace)
    return workspace.id

def test_model_gateway_records_successful_model_call()->None:
    db = SessionLocal()
    try:
        workspace_id = create_workspace(db, "Model Gateway Success")
        gateway = ModelGateway(db)
        output = gateway.complete(
            workspace_id = workspace_id,
            run_id = None,
            prompt = "hello model gateway",
        )
        model_call = (
            db.query(ModelCall)
            .filter(ModelCall.workspace_id == workspace_id) 
            .order_by(ModelCall.id.desc())
            .first()
        )
        
        assert output == "fake response for : hello model gateway"
        assert model_call is not None
        assert model_call.workspace_id == workspace_id
        assert model_call.run_id is None
        assert model_call.provider == "fake"
        assert model_call.model_name == "fake-model"
        assert model_call.prompt_tokens == 3
        assert model_call.completion_tokens == 3
        assert model_call.latency_ms >= 0
        assert model_call.estimated_cost == Decimal("0.000000")
        assert model_call.status == "success"
        assert model_call.error_message is None
    finally:
        db.close()
        
def test_model_gateway_records_failed_model_call()->None:
    db = SessionLocal()
    try:
        workspace_id = create_workspace(db, "Model Gateway Failure")
        gateway = ModelGateway(db)
        with pytest.raises(RuntimeError, match="fake provider failure"):
            gateway.complete(
                workspace_id = workspace_id,
                run_id = None,
                prompt = "please FAIL"
            )
        model_call = (
            db.query(ModelCall)
            .filter(ModelCall.workspace_id == workspace_id)
            .order_by(ModelCall.id.desc())
            .first()
        )
        assert model_call is not None
        assert model_call.workspace_id == workspace_id
        assert model_call.run_id is None
        assert model_call.provider == "fake"
        assert model_call.model_name == "fake-model"
        assert model_call.prompt_tokens == 2
        assert model_call.completion_tokens == 0
        assert model_call.latency_ms >= 0
        assert model_call.estimated_cost == Decimal("0.000000")
        assert model_call.status == "failed"
        assert model_call.error_message == "fake provider failure"
    finally:
        db.close()
def test_model_call_repository_lists_calls_by_workspace()->None:
    db = SessionLocal()
    try : 
        workspace_one_id = create_workspace(db, "Model Gateway List One")
        workspace_two_id = create_workspace(db, "Model Gateway List Two")
        gateway = ModelGateway(db)
        gateway.complete(
            workspace_id = workspace_one_id,
            run_id = None,
            prompt = "workspace one call"
        )
        gateway.complete(
            workspace_id=workspace_two_id,
            run_id=None,
            prompt="workspace two call"
        )
        repository = ModelCallRepository(db)
        calls = repository.list_by_workspace(workspace_id=workspace_one_id)
        
        assert len(calls) >= 1
        assert all(call.workspace_id == workspace_one_id for call in calls)
    finally:
        db.close()

def test_model_gateway_allows_calls_under_limit()->None:
    db = SessionLocal()
    try:
        workspace_id = create_workspace(db, "Model Gateway Under Limit")
        gateway = ModelGateway(db)
        
        output = gateway.complete(
            workspace_id = workspace_id,
            run_id = None,
            prompt = "under limit",
        )
        assert output == "fake response for : under limit"
    finally:
        db.close()
        
def test_model_gateway_returns_429_when_daily_limit_exceeded()->None:
    db = SessionLocal()
    
    try:
        workspace_id = create_workspace(db, "Model Gateway Limit")
        gateway = ModelGateway(db)
        
        for index in range(100):
            gateway.complete(
                workspace_id = workspace_id,
                run_id = None,
                prompt = f"limit call {index}",
            )
        with pytest.raises(HTTPException) as exc_info:
            gateway.complete(
                workspace_id = workspace_id,
                run_id = None,
                prompt = "one more call"
            )
        assert exc_info.value.status_code == 429
        assert exc_info.value.detail == "daily model call limit exceeded"
    finally:
        db.close()

def test_model_gateway_rate_limit_is_separated_by_workspace()->None:
    db = SessionLocal()
    
    try:
        limited_workspace_id = create_workspace(db, "Model Gateway Limited Workspace")
        other_workspace_id = create_workspace(db, "Model Gateway Other Workspace")
        gateway = ModelGateway(db)
        
        for index in range(100):
            gateway.complete(
                workspace_id = limited_workspace_id,
                run_id = None,
                prompt = f"workspace limit call {index}",
            )
        output = gateway.complete(
            workspace_id = other_workspace_id,
            run_id = None,
            prompt = "other workspace call",
        )
        assert output == "fake response for : other workspace call"
        
    finally:
        db.close()
        
def test_model_gateway_masks_secret_in_failed_model_call()->None:
    db = SessionLocal()
    try:
        workspace_id = create_workspace(db, "Model Gateway Secret Mask")
        gateway = ModelGateway(db)
        with pytest.raises(RuntimeError) as exc_info:
            gateway.complete(
                workspace_id = workspace_id,
                run_id = None,
                prompt = "please SECRET_FAIL",
            )
        assert "sk-abc123" not in str(exc_info.value)
        assert "sk-***123" in str(exc_info.value)
        
        model_call = (
            db.query(ModelCall)
            .filter(ModelCall.workspace_id == workspace_id)
            .order_by(ModelCall.id.desc())
            .first()
        )
        assert model_call is not None
        assert model_call.error_message is not None
        assert "sk-abc123" not in model_call.error_message
        assert "sk-***123" in model_call.error_message
    finally:
        db.close()

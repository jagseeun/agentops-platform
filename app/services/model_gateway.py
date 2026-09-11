from decimal import Decimal
from time import perf_counter

from sqlalchemy.orm import Session

from fastapi import HTTPException, status

from app.core.secret_masking import mask_secrets
from app.providers.fake_model_provider import FakeModelProvider
from app.repositories.model_call_repository import ModelCallRepository

DAILY_MODEL_CALL_LIMIT = 100

class ModelGateway:
    def __init__(self, db : Session):
        self.provider = FakeModelProvider()
        self.model_call_repository = ModelCallRepository(db)
    def complete(
        self, *, workspace_id : int, run_id : int | None, prompt : str,
    )->str : 
        if (
            self.model_call_repository.count_today_by_workspace(
                workspace_id=workspace_id,
            )
            >=DAILY_MODEL_CALL_LIMIT
        ):
            raise HTTPException(
                status_code = status.HTTP_429_TOO_MANY_REQUESTS,
                detail="daily model call limit exceeded"
            )
        start = perf_counter()
        try:
            result = self.provider.complete(prompt)
            latency_ms = int((perf_counter() - start) * 1000)
                    
            self.model_call_repository.create(
                workspace_id=workspace_id,
                run_id=run_id,
                provider="fake",
                model_name="fake-model",
                prompt_tokens=len(prompt.split()),
                completion_tokens=result["tokens"],
                latency_ms=latency_ms,
                estimated_cost=Decimal("0"),
                status="success",
            )
            return result["output"]
        except Exception as exc:
            latency_ms = int((perf_counter()-start) * 1000)
            safe_error_message = mask_secrets(str(exc))
            
            self.model_call_repository.create(
                workspace_id = workspace_id,
                run_id=run_id,
                provider="fake",
                model_name="fake-model",
                prompt_tokens=len(prompt.split()),
                completion_tokens= 0,
                latency_ms=latency_ms,
                estimated_cost=Decimal("0"),
                status="failed",
                error_message=safe_error_message,
            )
            raise RuntimeError(safe_error_message) from exc
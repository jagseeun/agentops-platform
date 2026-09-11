from decimal import Decimal
from sqlalchemy.orm import Session
from app.models.model_call import ModelCall

from datetime import UTC, datetime,time
class ModelCallRepository:
    def __init__(self, db : Session):
        self.db = db
    
    def create(
        self,
        *,
        workspace_id : int,
        run_id : int | None,
        provider : str,
        model_name :str,
        prompt_tokens: int,
        completion_tokens : int,
        latency_ms : int,
        estimated_cost : Decimal,
        status : str,
        error_message: str | None = None,
    )-> ModelCall:
        model_call = ModelCall(
            workspace_id = workspace_id,
            run_id = run_id,
            provider = provider,
            model_name = model_name,
            prompt_tokens = prompt_tokens,
            completion_tokens = completion_tokens,
            latency_ms=latency_ms,
            estimated_cost = estimated_cost,
            status=status,
            error_message=error_message
        )
        self.db.add(model_call)
        self.db.commit()
        self.db.refresh(model_call)
        
        return model_call
    
    def list_by_workspace(self, *, workspace_id: int)-> list[ModelCall]:
        return (
            self.db.query(ModelCall)
            .filter(ModelCall.workspace_id == workspace_id)
            .order_by(ModelCall.created_at.desc(), ModelCall.id.desc())
            .all()
        )
        
    def count_today_by_workspace(self, *, workspace_id: int)->int:
        start_of_day = datetime.combine(datetime.now(UTC).date(), time.min)
        
        return (
            self.db.query(ModelCall)
            .filter(
                ModelCall.workspace_id == workspace_id,
                ModelCall.created_at >= start_of_day,
            )
            .count()
        )
    
    def get_usage_summary_by_workspace(self, *, workspace_id: int)-> dict:
        calls =  (
            self.db.query(ModelCall)
            .filter(ModelCall.workspace_id == workspace_id)
            .all()
        )
        total_calls = len(calls)
        success_calls = len([call for call in calls if call.status == "success"])
        failed_calls = len([call for call in calls if call.status == "failed"])
        
        estimated_cost = sum(call.estimated_cost for call in calls)
        if total_calls == 0:
            average_latency_ms = 0
        else : 
            average_latency_ms = int(
                sum(call.latency_ms for call in calls) / total_calls
            )
        return {
            "workspace_id" : workspace_id,
            "total_calls" : total_calls,
            "success_calls" : success_calls,
            "failed_calls" : failed_calls,
            "estimated_cost" : float(estimated_cost),
            "average_latency_ms" : average_latency_ms,
        }
from pydantic import BaseModel

class ModelUsageSummaryRead(BaseModel):
    workspace_id : int
    total_calls : int
    success_calls : int
    failed_calls : int
    estimated_cost : float
    average_latency_ms : int
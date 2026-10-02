import json
import logging

from uuid import UUID
def test_response_includes_generated_request_id(client)->None:
    response = client.get("/health")
    assert response.status_code==200
    request_id = response.headers["X-Request-Id"]
    UUID(request_id)
    
def test_response_reuses_request_id_from_header(client)->None:
    request_id = "test-request-id-123"
    response= client.get(
        "/health",
        headers={"X-Request-Id": request_id},
    )
    assert response.status_code == 200
    assert response.headers["X-Request-Id"] == request_id
    
def test_request_log_contains_request_details(client, caplog) -> None:
    request_id = "test-request-id-456"
    
    with caplog.at_level(
        logging.INFO,
        logger="uvicorn.error.agentops.request",
    ):
        response = client.get(
            "/health",
            headers={"X-Request-Id": request_id},
        )
    request_logs = [
        record for record in caplog.records
        if record.name=="uvicorn.error.agentops.request"
    ]
    assert request_logs
    
    log_data=json.loads(request_logs[-1].getMessage())
    
    assert log_data["event"] == "request_completed"
    assert log_data["request_id"] == request_id
    assert log_data["method"] == "GET"
    assert log_data["path"] == "/health"
    assert log_data["status_code"] == response.status_code
    assert log_data["duration_ms"] >= 0
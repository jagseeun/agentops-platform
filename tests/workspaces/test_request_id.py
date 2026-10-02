import json
import logging
import pytest
from app.main import app

from uuid import UUID

@app.get("/_test/request-failure")
def raise_test_request_error()->None:
    raise RuntimeError("test request failure")

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
    
def test_failure_request_log_contains_request_details(client, caplog)->None:
    request_id = "test-failed-request-id"
    with caplog.at_level(
        logging.ERROR,
        logger="uvicorn.error.agentops.request",
    ):
        with pytest.raises(RuntimeError, match="test request failure"):
            client.get(
                "/_test/request-failure",
               headers={"X-Request-Id":request_id}, 
            )
    failure_logs = [
        record for record in caplog.records
        if record.name == "uvicorn.error.agentops.request"
        and record.levelno == logging.ERROR
    ]
    assert failure_logs
    failure_log = failure_logs[-1]
    log_data = json.loads(failure_log.getMessage())
    
    assert log_data["event"] == "request_failed"
    assert log_data["request_id"] == request_id
    assert log_data["method"] == "GET"
    assert log_data["path"] == "/_test/request-failure"
    assert log_data["status_code"] == 500
    assert log_data["duration_ms"]>=0
    assert log_data["error_type"] == "RuntimeError"
    assert failure_log.exc_info is not None
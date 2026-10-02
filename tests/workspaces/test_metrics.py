import pytest
from app.main import app
from prometheus_client import REGISTRY

@app.get("/_test/metrics-failure")
def raise_metrics_test_error()->None:
    raise RuntimeError("metrics test failure")

def test_metrics_endpoint_returns_prometheus_data(client)->None:
    response=client.get("/metrics/")
    assert response.status_code == 200
    assert "python_info" in response.text
    
def test_metrics_records_successful_request(client)->None:
    counter_labels={
        "method": "GET",
        "route": "/health",
        "status_code": "200",
    }
    duration_labels = {
        "method": "GET",
        "route": "/health"
    }
    counter_before=(
        REGISTRY.get_sample_value(
            "agentops_http_requests_total",
            counter_labels,
        )
        or 0
    )
    duration_count_before = (
        REGISTRY.get_sample_value(
            "agentops_http_request_duration_seconds_count",
            duration_labels,
        )
        or 0
    )
    
    
    response=client.get("/health")
    assert response.status_code == 200
    
    counter_after = REGISTRY.get_sample_value(
        "agentops_http_requests_total",
        counter_labels,
    )
    duration_count_after = REGISTRY.get_sample_value(
        "agentops_http_request_duration_seconds_count",
        duration_labels,
    )
    
    assert counter_after == counter_before+1
    assert duration_count_after == duration_count_before+1
    
def  test_metrics_records_failed_request(client)->None:
    counter_labels = {
        "method": "GET",
        "route": "/_test/metrics-failure",
        "status_code": "500",
    }
    duration_labels = {
        "method": "GET",
        "route": "/_test/metrics-failure",
    }
    counter_before=(
        REGISTRY.get_sample_value(
            "agentops_http_requests_total",
            counter_labels,
        )
        or 0
    )
    duration_counter_before = (
        REGISTRY.get_sample_value(
            "agentops_http_request_duration_seconds_count",
            duration_labels,
        )
        or 0
    )
    with pytest.raises(RuntimeError, match="metrics test failure"):
        client.get("/_test/metrics-failure")
        
    counter_after = REGISTRY.get_sample_value(
        "agentops_http_requests_total",
        counter_labels,
    )
    duration_count_after = REGISTRY.get_sample_value(
        "agentops_http_request_duration_seconds_count",
        duration_labels,
    )
    assert counter_after == counter_before+1
    assert duration_count_after == duration_counter_before+1
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
    
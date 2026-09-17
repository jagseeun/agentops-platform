from fastapi.testclient import TestClient
from uuid import uuid4

from app.main import app


client = TestClient(app)

# Service에서 409만 처리 해서 201 코드는 없애야 했음 안 그럴시 에러 발생;
# def test_create_workspace() -> None:
#     response = client.post(
#         "/workspaces",
#         json={"name": "Acme", "slug": "acme"},
#     )

#     assert response.status_code == 201
#     data = response.json()
#     assert data["name"] == "Acme"
#     assert data["slug"] == "acme"
#     assert data["status"] == "active"

# 409는 중복 값 넣기여서 중복된 값을 넣고 status_code를 409로 수정.
def test_create_workspace_add_duplicate_values() -> None:
    slug = f"acme-{uuid4().hex}"

    response = client.post(
        "/workspaces",
        json={"name": "Acme", "slug": slug},
    )
    assert response.status_code == 201
    
    duplicate_response = client.post(
        "/workspaces",
        json={"name":"Acme Duplicate", "slug":slug}
    )
    assert duplicate_response.status_code == 409

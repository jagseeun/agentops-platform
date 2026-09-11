from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

# def test_create_workspace()->None:
#     response = client.post(
#         "/workspaces",
#         json={"name":"Seun", "slug":"seun"}
#     )
#     assert response.status_code == 201
#     data = response.json()
#     assert data["name"] == "Seun"
#     assert data["slug"] == "seun"
#     assert data["status"] == "active"


from __future__ import annotations

from uuid import uuid4

import httpx

BASE_URL = "http://127.0.0.1:8000"

def auth_headers(workspace_id: int, role: str="admin")->dict[str, str]:
    return {
        "X-User-Id": "1",
        "X-Workspace-Id" : str(workspace_id),
        "X-User-Role" : role,
    }
    
def assert_status(response: httpx.Response, expected_status: int)-> None:
    if response.status_code != expected_status:
        raise RuntimeError(
            f"Expected {expected_status}, got {response.status_code}: {response.text}"
        )
        
def main()->None:
    with httpx.Client(base_url=BASE_URL, timeout=10.0) as client:
        health_response = client.get("/health")
        assert_status(health_response,200)
        
        slug = f"pg-smoke-{uuid4().hex}"
        
        workspace_response = client.post(
            "/workspaces",
            json={
                "name":"Postgres Smoke",
                "slug": slug,
            },
        )
        assert_status(workspace_response, 201)
        workspace = workspace_response.json()
        workspace_id = workspace["id"]
        
        duplicate_workspace_response = client.post(
            "/workspaces",
            json={
                "name" : "Postgres Smoke Duplicate",
                "slug" : slug
            },
        )
        assert_status(duplicate_workspace_response, 409)
        
        agent_response = client.post(
            "/agents",
            headers=auth_headers(workspace_id),
            json={
                "workspace_id":workspace_id,
                "name":"pg-smoke-agent",
                "version":"1.0.0",
            },
        )
        assert_status(agent_response, 201)
        agent = agent_response.json()
        
        list_agents_response = client.get(
            f"/workspaces/{workspace_id}/agents",
            
            headers=auth_headers(workspace_id, role="viewer"),
        )
        assert_status(list_agents_response,200)
        agents = list_agents_response.json()
        
        if not any(item["id"] == agent["id"] for item in agents):
            raise RuntimeError("Created agent was not found in workspace agent list")
    
    print("PostgreSQL smoke test passed")
    print(f"workspace_id = {workspace_id}")
    print(f"agent_id={agent['id']}")
    
if __name__ == "__main__":
    main()
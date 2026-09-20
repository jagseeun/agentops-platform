from uuid import uuid4

def unique_slug(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex}"

def test_list_agent_allowed_whn_url_workspace_matches_header(client, auth_headers) -> None:
    workspace_response = client.post(
        "/workspaces",
        json ={"name":"Context Match", "slug": unique_slug("context_match_workspace_test")},
    )
    assert workspace_response.status_code == 201
    workspace_id = workspace_response.json()["id"]
    
    response = client.get(
        f"/workspaces/{workspace_id}/agents",
        headers = auth_headers(workspace_id=workspace_id, role="viewer"),
    )
    assert response.status_code==200
    
def test_list_agents_forbidden_when_url_workspace_differs_from_header(client, auth_headers)->None:
    workspace_response = client.post(
        "/workspaces",
        json={"name":"Context Mismatch", "slug": unique_slug("context_mismatch_workspace_test")},
    )
    assert workspace_response.status_code==201
    workspace_id = workspace_response.json()["id"]
    
    other_workspace_response = client.post(
        "/workspaces",
        json = {"name":"Other Context", "slug": unique_slug("other_context_workspace_test")},
    )
    assert other_workspace_response.status_code == 201
    other_workspace_id = other_workspace_response.json()["id"]
    
    response = client.get(
        f"/workspaces/{workspace_id}/agents",
        headers=auth_headers(workspace_id=other_workspace_id, role = "viewer")
    )
    print(response.json())
    assert response.status_code == 403

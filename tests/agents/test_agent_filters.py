from uuid import uuid4


def unique_slug(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex}"


def test_inactive_filter_returns_inactive_agents(client, auth_headers)->None:
    workspace_response = client.post(
        "/workspaces",
        json={"name":"Inactive Filter", "slug" : unique_slug("inactive_filter_workspace_test")},
    )
    assert workspace_response.status_code == 201
    workspace_id = workspace_response.json()["id"]
    
    agent_response = client.post(
        "/agents",
        json = {
            "workspace_id" : workspace_id,
            "name": "inactive-filter-agent",
            "version": "1.0.0",
        },
        headers=auth_headers(workspace_id),
    )
    assert agent_response.status_code==201
    agent_id = agent_response.json()["id"]
    
    deactivate_response = client.post(
        f"/workspaces/{workspace_id}/agents/{agent_id}/deactivate",
        headers=auth_headers(workspace_id),
    )
    assert deactivate_response.status_code==200
    list_response = client.get(
        f"/workspaces/{workspace_id}/agents?status=inactive",
        headers=auth_headers(workspace_id, role="viewer"),
    )
    assert list_response.status_code == 200
    data = list_response.json()
    assert len(data)==1
    assert data[0]["id"] == agent_id
    assert data[0]["workspace_id"] == workspace_id
    assert data[0]["status"] == "inactive"

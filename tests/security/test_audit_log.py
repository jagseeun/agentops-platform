from app.repositories.audit_log_repository import AuditLogRepository

def test_create_audi_log(db_session)->None:
    repository = AuditLogRepository(db_session)
    audit_log = repository.create(
    workspace_id = 1,
    actor_user_id=10,
    action="create run",
    resource_type="Run",
    resource_id=100,
    audit_metadata={"status": "queued"},
    )
    assert audit_log.id is not None
    assert audit_log.workspace_id == 1
    assert audit_log.actor_user_id == 10
    assert audit_log.action == "create run"
    assert audit_log.resource_type == "Run"
    assert audit_log.resource_id == 100
    assert audit_log.audit_metadata == {"status" : "queued"}
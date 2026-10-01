from sqlalchemy.exc import SQLAlchemyError

def test_health_check_returns_ok(client)->None:
    response = client.get("/health")
    
    assert response.status_code==200
    assert response.json() == {"status": "ok"}
    
def test_health_live_returns_ok(client)->None:
    response=client.get("/health/live")
    assert response.status_code==200
    assert response.json()=={"status":"ok"} 

def test_health_ready_returns_ok_when_database_is_available(client)->None:
    response=client.get("/health/ready")
    assert response.status_code == 200
    assert response.json()=={"status":"ok"}

def test_health_ready_returns_503_when_database_is_unavailable(client, monkeypatch)->None:
    class BrokenEngine:
        def connect(self):
            raise SQLAlchemyError("database down")
    
    monkeypatch.setattr("app.main.engine", BrokenEngine())
    
    response = client.get("/health/ready")
    
    assert response.status_code==503
    assert response.json()=={"detail":"database unavailable"}
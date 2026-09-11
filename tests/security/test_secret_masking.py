from app.core.secret_masking import mask_secrets
def test_mask_secrets_hides_api_key()->None:
    message="Calling provider with api_key=sk-abc123"
    
    masked = mask_secrets(message)
    
    assert "sk-abc123" not in masked
    assert "sk-***123" in masked
    

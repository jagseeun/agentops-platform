import pytest
from app.providers.fake_model_provider import FakeModelProvider

def test_fake_provider_success() -> None:
    provider = FakeModelProvider()
    
    result = provider.complete("hello fake provider")
    
    assert result["output"] == "fake response for : hello fake provider"
    assert result["tokens"] == 3
    
def test_fake_provider_failure() -> None:
    provider = FakeModelProvider()
    
    with pytest.raises(RuntimeError, match="fake provider failure"):
        provider.complete("please FAIL")
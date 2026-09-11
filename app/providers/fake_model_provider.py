class FakeModelProvider:
    def complete(self, prompt: str)->dict:
        if "SECRET_FAIL" in prompt:
            raise RuntimeError("provider failed with api_key=sk-abc123")
        if "FAIL" in prompt:
            raise RuntimeError("fake provider failure")
        return {
            "output" : f"fake response for : {prompt[:50]}",
            "tokens" : len(prompt.split()),
        }
import re
_SECRET_PATTERN = re.compile(r"(sk-)[A-Za-z0-9_-]*([A-Za-z0-9_-]{3})")

def mask_secrets(message: str)-> str:
    return _SECRET_PATTERN.sub(r"\1***\2", message)
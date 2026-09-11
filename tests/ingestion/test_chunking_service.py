import pytest

from app.services.chunking_service import chunk_text

def test_short_text_returns_one_chunk()->None:
    chunks = chunk_text("hello", chunk_size = 500, overlap=50)
    assert chunks == ["hello"]

def test_long_text_returns_multiple_chunks()->None:
    text = "abcdefghij"
    
    chunks = chunk_text(text,chunk_size=4, overlap=1)

    assert len(chunks) > 1
    assert chunks == ["abcd", "defg", "ghij", "j"]
    
def test_overlap_is_applied() -> None:
    chunks = chunk_text("abcdefghij", chunk_size = 5, overlap=2)
    assert chunks[0] == "abcde"
    assert chunks[1] == "defgh"
    
def test_chunk_size_must_be_greater_than_overlap()->None:
    with pytest.raises(ValueError):
        chunk_text("hello world", chunk_size=5, overlap=5)
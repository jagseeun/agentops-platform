def chunk_text(
    text: str,
    chunk_size : int = 500,
    overlap: int = 50,
)-> list[str]:
    if chunk_size <= overlap:
        raise ValueError("chunk_size must be grater than over lap")
    
    chunks = []
    start = 0
    
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start = end - overlap
        
    return chunks
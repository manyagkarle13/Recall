"""
Chunking utility for Recall memories.
Splits long documents into chunks if token length > 500 tokens.
Preserves semantic continuity with token overlap.
"""

from typing import List, Tuple
import logging

logger = logging.getLogger(__name__)

# Try importing tiktoken for precise subword token counting; fallback to heuristic
try:
    import tiktoken
    _ENCODING = tiktoken.get_encoding("cl100k_base")
except Exception:
    _ENCODING = None


def count_tokens(text: str) -> int:
    """Returns token count using cl100k_base if available, else approximate word count * 1.3."""
    if not text:
        return 0
    if _ENCODING is not None:
        try:
            return len(_ENCODING.encode(text))
        except Exception:
            pass
    # Approximate heuristic (1 word ≈ 1.33 tokens)
    return int(len(text.split()) * 1.33)


def chunk_text(
    text: str,
    max_tokens: int = 500,
    overlap_tokens: int = 50,
) -> List[Tuple[int, str, int]]:
    """
    Chunks input text if token length exceeds max_tokens.
    
    Returns:
        List of tuples: (chunk_index, chunk_content, token_count)
    """
    text = text.strip()
    if not text:
        return []

    total_tokens = count_tokens(text)
    if total_tokens <= max_tokens:
        return [(0, text, total_tokens)]

    chunks: List[Tuple[int, str, int]] = []

    if _ENCODING is not None:
        try:
            tokens = _ENCODING.encode(text)
            step = max_tokens - overlap_tokens
            chunk_idx = 0
            for start in range(0, len(tokens), step):
                chunk_slice = tokens[start : start + max_tokens]
                chunk_str = _ENCODING.decode(chunk_slice).strip()
                if chunk_str:
                    chunks.append((chunk_idx, chunk_str, len(chunk_slice)))
                    chunk_idx += 1
                if start + max_tokens >= len(tokens):
                    break
            return chunks
        except Exception as e:
            logger.warning(f"Tiktoken chunking failed, falling back to sentence chunking: {e}")

    # Sentence / paragraph fallback chunker
    paragraphs = text.split("\n\n")
    current_chunk = []
    current_tokens = 0
    chunk_idx = 0

    for para in paragraphs:
        para_tokens = count_tokens(para)
        if current_tokens + para_tokens > max_tokens and current_chunk:
            combined = "\n\n".join(current_chunk).strip()
            chunks.append((chunk_idx, combined, current_tokens))
            chunk_idx += 1
            # Simple overlap
            current_chunk = [para]
            current_tokens = para_tokens
        else:
            current_chunk.append(para)
            current_tokens += para_tokens

    if current_chunk:
        combined = "\n\n".join(current_chunk).strip()
        chunks.append((chunk_idx, combined, current_tokens))

    return chunks

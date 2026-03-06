"""
Text Chunking Utilities
Split large documents into manageable chunks for processing.
"""

from typing import Generator


def chunk_text(text: str, chunk_size: int = 4000, overlap: int = 200) -> list[str]:
    """
    Split text into overlapping chunks.

    Args:
        text: The text to split
        chunk_size: Maximum characters per chunk
        overlap: Number of overlapping characters between chunks

    Returns:
        List of text chunks
    """
    if len(text) <= chunk_size:
        return [text]

    chunks = []
    start = 0

    while start < len(text):
        end = start + chunk_size

        # Try to break at a sentence or paragraph boundary
        if end < len(text):
            # Look for paragraph break
            newline_pos = text.rfind('\n\n', start, end)
            if newline_pos > start + chunk_size // 2:
                end = newline_pos
            else:
                # Look for sentence break
                for sep in ['. ', '! ', '? ', '\n']:
                    sep_pos = text.rfind(sep, start, end)
                    if sep_pos > start + chunk_size // 2:
                        end = sep_pos + len(sep)
                        break

        chunks.append(text[start:end].strip())
        start = end - overlap

    return [c for c in chunks if c]  # Filter empty chunks


def chunk_text_generator(text: str, chunk_size: int = 4000, overlap: int = 200) -> Generator[str, None, None]:
    """
    Generator version of chunk_text for memory efficiency.

    Args:
        text: The text to split
        chunk_size: Maximum characters per chunk
        overlap: Number of overlapping characters between chunks

    Yields:
        Text chunks
    """
    if len(text) <= chunk_size:
        yield text
        return

    start = 0

    while start < len(text):
        end = start + chunk_size

        if end < len(text):
            newline_pos = text.rfind('\n\n', start, end)
            if newline_pos > start + chunk_size // 2:
                end = newline_pos
            else:
                for sep in ['. ', '! ', '? ', '\n']:
                    sep_pos = text.rfind(sep, start, end)
                    if sep_pos > start + chunk_size // 2:
                        end = sep_pos + len(sep)
                        break

        chunk = text[start:end].strip()
        if chunk:
            yield chunk

        start = end - overlap


def estimate_tokens(text: str) -> int:
    """
    Rough estimate of token count (approximately 4 chars per token).

    Args:
        text: The text to estimate

    Returns:
        Estimated token count
    """
    return len(text) // 4


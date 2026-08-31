"""PDF extraction and token-aware chunking.

Extraction uses pymupdf directly (no LangChain). The splitter works on token
windows so chunk sizes and overlaps are exact in tokens, and chunks never
cross page boundaries, keeping the page number in every citation exact.
"""

from __future__ import annotations

import hashlib
import logging
import re
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class Chunk:
    text: str
    source: str  # PDF filename (no directory)
    page: int  # 1-based page number
    chunk_id: str


# ---------------------------------------------------------------------------
# Tokenizers
# ---------------------------------------------------------------------------


class SimpleTokenizer:
    """Whitespace-preserving word tokenizer, used when tiktoken is unavailable
    (e.g. fully offline first run). encode/decode round-trip losslessly."""

    name = "simple-words"

    def encode(self, text: str) -> list[str]:
        return re.findall(r"\S+\s*|\s+", text)

    def decode(self, tokens: list[str]) -> str:
        return "".join(tokens)


class TiktokenTokenizer:
    name = "tiktoken/cl100k_base"

    def __init__(self):
        import tiktoken

        self._enc = tiktoken.get_encoding("cl100k_base")

    def encode(self, text: str) -> list[int]:
        return self._enc.encode(text, disallowed_special=())

    def decode(self, tokens: list[int]) -> str:
        return self._enc.decode(tokens)


def get_tokenizer():
    """tiktoken if it can load its vocabulary (cached or online), else the
    simple fallback."""
    try:
        return TiktokenTokenizer()
    except Exception as exc:  # network failure on first run, missing package
        logger.warning("tiktoken unavailable (%s); using simple word tokenizer", exc)
        return SimpleTokenizer()


# ---------------------------------------------------------------------------
# Splitter
# ---------------------------------------------------------------------------


class TokenSplitter:
    """Split text into overlapping token windows of at most chunk_size tokens
    with exactly overlap_tokens of overlap between consecutive chunks."""

    def __init__(self, chunk_size: int = 800, overlap: int = 150, tokenizer=None):
        if overlap >= chunk_size:
            raise ValueError("chunk_overlap must be smaller than chunk_size")
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.tokenizer = tokenizer or get_tokenizer()

    def split(self, text: str) -> list[str]:
        tokens = self.tokenizer.encode(text)
        if not tokens:
            return []
        stride = self.chunk_size - self.overlap
        chunks = []
        i = 0
        while True:
            window = tokens[i : i + self.chunk_size]
            piece = self.tokenizer.decode(window).strip()
            if piece:
                chunks.append(piece)
            if i + self.chunk_size >= len(tokens):
                break
            i += stride
        return chunks


# ---------------------------------------------------------------------------
# PDF handling
# ---------------------------------------------------------------------------


def extract_pages(pdf_path: Path) -> list[tuple[int, str]]:
    """Return (1-based page number, text) for every page with any text."""
    import pymupdf

    pages = []
    with pymupdf.open(pdf_path) as doc:
        for i, page in enumerate(doc):
            text = page.get_text()
            if text.strip():
                pages.append((i + 1, text))
    return pages


def chunk_pdf(pdf_path: Path, splitter: TokenSplitter) -> list[Chunk]:
    source = Path(pdf_path).name
    chunks: list[Chunk] = []
    for page_no, text in extract_pages(Path(pdf_path)):
        for j, piece in enumerate(splitter.split(text)):
            chunks.append(
                Chunk(
                    text=piece,
                    source=source,
                    page=page_no,
                    chunk_id=f"{source}::p{page_no}::c{j}",
                )
            )
    return chunks


def file_fingerprint(path: Path, with_hash: bool = True) -> dict:
    """size/mtime (cheap) plus a content hash (definitive) for change detection."""
    stat = path.stat()
    record = {"size": stat.st_size, "mtime": stat.st_mtime}
    if with_hash:
        record["sha256"] = content_hash(path)
    return record


def content_hash(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def list_pdfs(pdf_dir: Path) -> list[Path]:
    return sorted(p for p in Path(pdf_dir).iterdir() if p.suffix.lower() == ".pdf")

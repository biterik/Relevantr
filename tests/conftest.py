"""Shared fixtures: tiny generated PDFs and a deterministic fake embedder."""

from __future__ import annotations

import hashlib
from pathlib import Path

import numpy as np
import pytest

from relevantr.embed import EmbeddingBackend


def make_pdf(path: Path, pages: list[str]) -> Path:
    """Write a small PDF with one text block per page."""
    import pymupdf

    doc = pymupdf.open()
    for text in pages:
        page = doc.new_page()
        page.insert_text((72, 72), text, fontsize=11)
    path.parent.mkdir(parents=True, exist_ok=True)
    doc.save(path)
    doc.close()
    return path


class FakeEmbedder(EmbeddingBackend):
    """Deterministic bag-of-words hashing embedder: shared words give shared
    vector components, so a query containing a chunk's words ranks it high."""

    def __init__(self, name: str = "fake:test", dim: int = 64):
        self.name = name
        self.dim = dim

    def _vector(self, text: str) -> np.ndarray:
        vec = np.zeros(self.dim, dtype=np.float32)
        for word in text.lower().split():
            idx = int(hashlib.md5(word.encode()).hexdigest(), 16) % self.dim
            vec[idx] += 1.0
        norm = np.linalg.norm(vec)
        return vec / norm if norm else vec

    def embed_documents(self, texts: list[str]) -> np.ndarray:
        return np.stack([self._vector(t) for t in texts])

    def embed_query(self, text: str) -> np.ndarray:
        return self._vector(text)


class SpyEmbedder(FakeEmbedder):
    """Records every document text it embeds, to prove incrementality."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.embedded_texts: list[str] = []

    def embed_documents(self, texts: list[str]) -> np.ndarray:
        self.embedded_texts.extend(texts)
        return super().embed_documents(texts)


@pytest.fixture
def fake_embedder():
    return FakeEmbedder()


@pytest.fixture
def spy_embedder():
    return SpyEmbedder()

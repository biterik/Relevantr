"""Embedding backends behind one interface.

Two implementations:
- LocalEmbedding: Qwen/Qwen3-Embedding-0.6B via sentence-transformers,
  device auto-selected (MPS on macOS, CUDA, else CPU). Queries use the
  model's retrieval prompt (prompt_name="query"); documents are encoded plain.
- GWDGEmbedding: qwen3-embedding-4b via the GWDG Chat AI OpenAI-compatible
  /embeddings endpoint.

Every backend exposes a stable ``name`` and ``dim`` that are recorded in the
index manifest so a mismatched backend can be refused.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod

import numpy as np

from .config import (
    GWDG_BASE_URL,
    GWDG_EMBEDDING_MODEL,
    LOCAL_EMBEDDING_MODEL,
    AppConfig,
    resolve_api_key,
)

logger = logging.getLogger(__name__)


class EmbeddingBackend(ABC):
    name: str
    dim: int

    @abstractmethod
    def embed_documents(self, texts: list[str]) -> np.ndarray: ...

    @abstractmethod
    def embed_query(self, text: str) -> np.ndarray: ...


def pick_device() -> str:
    import torch

    if torch.backends.mps.is_available():
        return "mps"
    if torch.cuda.is_available():
        return "cuda"
    return "cpu"


class LocalEmbedding(EmbeddingBackend):
    def __init__(self, model_name: str = LOCAL_EMBEDDING_MODEL):
        self.model_name = model_name
        self.name = f"local:{model_name}"
        self._model = None
        self._dim = None

    @property
    def dim(self) -> int:  # type: ignore[override]
        if self._dim is None:
            model = self._load()
            getter = getattr(model, "get_embedding_dimension", None) or (
                model.get_sentence_embedding_dimension
            )
            self._dim = getter()
        return self._dim

    def _load(self):
        if self._model is None:
            from sentence_transformers import SentenceTransformer

            device = pick_device()
            logger.info("Loading %s on %s", self.model_name, device)
            self._model = SentenceTransformer(self.model_name, device=device)
        return self._model

    def embed_documents(self, texts: list[str]) -> np.ndarray:
        model = self._load()
        return np.asarray(
            model.encode(texts, normalize_embeddings=True, show_progress_bar=False)
        )

    def embed_query(self, text: str) -> np.ndarray:
        model = self._load()
        return np.asarray(
            model.encode(
                [text],
                prompt_name="query",
                normalize_embeddings=True,
                show_progress_bar=False,
            )
        )[0]


class GWDGEmbedding(EmbeddingBackend):
    def __init__(
        self,
        model_name: str = GWDG_EMBEDDING_MODEL,
        base_url: str = GWDG_BASE_URL,
        api_key: str | None = None,
    ):
        self.model_name = model_name
        self.name = f"gwdg:{model_name}"
        self.base_url = base_url
        if api_key is None:
            api_key, source = resolve_api_key("gwdg")
            if api_key is None:
                raise RuntimeError(
                    "The GWDG embedding backend needs an API key. Set the "
                    "GWDG_API_KEY environment variable or enter the key in "
                    "Settings."
                )
            logger.info("GWDG API key from %s", source)
        self._api_key = api_key
        self._client = None
        self._dim = None

    def _get_client(self):
        if self._client is None:
            from openai import OpenAI

            self._client = OpenAI(base_url=self.base_url, api_key=self._api_key)
        return self._client

    @property
    def dim(self) -> int:  # type: ignore[override]
        if self._dim is None:
            self._dim = len(self.embed_query("dimension probe"))
        return self._dim

    def _embed(self, texts: list[str]) -> np.ndarray:
        client = self._get_client()
        vectors: list[list[float]] = []
        batch_size = 32
        for start in range(0, len(texts), batch_size):
            batch = texts[start : start + batch_size]
            response = client.embeddings.create(model=self.model_name, input=batch)
            ordered = sorted(response.data, key=lambda item: item.index)
            vectors.extend(item.embedding for item in ordered)
        arr = np.asarray(vectors, dtype=np.float32)
        norms = np.linalg.norm(arr, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        return arr / norms

    def embed_documents(self, texts: list[str]) -> np.ndarray:
        return self._embed(texts)

    def embed_query(self, text: str) -> np.ndarray:
        return self._embed([text])[0]


def backend_name(config: AppConfig) -> str:
    """The manifest name the configured backend would use, without loading it."""
    if config.embedding_backend == "gwdg":
        return f"gwdg:{GWDG_EMBEDDING_MODEL}"
    return f"local:{LOCAL_EMBEDDING_MODEL}"


def get_backend(config: AppConfig) -> EmbeddingBackend:
    if config.embedding_backend == "gwdg":
        return GWDGEmbedding()
    if config.embedding_backend == "local":
        return LocalEmbedding()
    raise ValueError(f"Unknown embedding backend: {config.embedding_backend!r}")

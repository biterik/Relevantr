# SPDX-License-Identifier: AGPL-3.0-or-later
"""GWDG embedding backend with a mocked OpenAI-compatible client
(used when no GWDG_API_KEY is available in the test environment)."""

from types import SimpleNamespace

import numpy as np

from relevantr.embed import GWDGEmbedding


class FakeEmbeddingsAPI:
    def __init__(self):
        self.calls = []

    def create(self, model, input):  # noqa: A002 - OpenAI API name
        self.calls.append((model, list(input)))
        # return items deliberately out of order to test index-based sorting
        data = [
            SimpleNamespace(index=i, embedding=[float(len(text)), 1.0, 0.0])
            for i, text in enumerate(input)
        ]
        return SimpleNamespace(data=list(reversed(data)))


def make_backend():
    backend = GWDGEmbedding(api_key="test-key")
    fake = SimpleNamespace(embeddings=FakeEmbeddingsAPI())
    backend._client = fake
    return backend, fake.embeddings


def test_batching_and_order():
    backend, api = make_backend()
    texts = [f"t{'x' * i}" for i in range(70)]  # distinct lengths, 3 batches
    vectors = backend.embed_documents(texts)
    assert vectors.shape == (70, 3)
    assert len(api.calls) == 3  # 32 + 32 + 6
    assert all(model == "qwen3-embedding-4b" for model, _ in api.calls)
    # order restored despite reversed API response: first component encodes
    # the (normalized) text length, so it must increase monotonically
    firsts = vectors[:, 0] / vectors[:, 1]
    assert all(a < b for a, b in zip(firsts, firsts[1:]))


def test_vectors_normalized():
    backend, _ = make_backend()
    vec = backend.embed_query("hello")
    assert np.isclose(np.linalg.norm(vec), 1.0)


def test_backend_name_and_dim():
    backend, _ = make_backend()
    assert backend.name == "gwdg:qwen3-embedding-4b"
    assert backend.dim == 3  # probed lazily via one embedding call

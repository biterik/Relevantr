# SPDX-License-Identifier: AGPL-3.0-or-later
"""Cross-encoder reranking stage.

Hybrid search retrieves ~retrieve_k candidates; this stage rescores them with
BAAI/bge-reranker-v2-m3 and keeps the top final_n. The scorer is injectable
so the logic can be tested without downloading the model.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

from .config import RERANKER_MODEL

logger = logging.getLogger(__name__)


@dataclass
class Passage:
    text: str
    source: str
    page: int
    score: float = 0.0


class Reranker:
    def __init__(self, model_name: str = RERANKER_MODEL, scorer=None):
        """scorer: callable(list[(query, text)]) -> list[float]; defaults to
        the CrossEncoder model, loaded lazily on first use."""
        self.model_name = model_name
        self._scorer = scorer

    def _get_scorer(self):
        if self._scorer is None:
            from sentence_transformers import CrossEncoder

            from .embed import pick_device

            device = pick_device()
            logger.info("Loading reranker %s on %s", self.model_name, device)
            model = CrossEncoder(self.model_name, device=device)
            self._scorer = lambda pairs: model.predict(pairs, show_progress_bar=False)
        return self._scorer

    def rerank(self, query: str, passages: list[Passage], top_n: int) -> list[Passage]:
        if not passages:
            return []
        scorer = self._get_scorer()
        scores = scorer([(query, p.text) for p in passages])
        rescored = [
            Passage(text=p.text, source=p.source, page=p.page, score=float(s))
            for p, s in zip(passages, scores)
        ]
        rescored.sort(key=lambda p: p.score, reverse=True)
        return rescored[:top_n]

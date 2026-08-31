# SPDX-License-Identifier: AGPL-3.0-or-later
"""Reranker: ordering changes when the cross-encoder stage is applied."""

from relevantr.rerank import Passage, Reranker

PASSAGES = [
    Passage("first passage about nothing", "a.pdf", 1, score=0.9),
    Passage("second passage about the actual topic", "b.pdf", 2, score=0.5),
    Passage("third passage, tangential", "c.pdf", 3, score=0.1),
]


def scorer_prefers_topic(pairs):
    return [10.0 if "actual topic" in text else 1.0 for _query, text in pairs]


def test_ordering_changes():
    reranker = Reranker(scorer=scorer_prefers_topic)
    result = reranker.rerank("what is the actual topic?", list(PASSAGES), top_n=3)
    assert [p.source for p in result] != [p.source for p in PASSAGES]
    assert result[0].source == "b.pdf"
    assert result[0].score == 10.0


def test_top_n_respected():
    reranker = Reranker(scorer=scorer_prefers_topic)
    result = reranker.rerank("q", list(PASSAGES), top_n=2)
    assert len(result) == 2


def test_empty_input():
    reranker = Reranker(scorer=scorer_prefers_topic)
    assert reranker.rerank("q", [], top_n=5) == []

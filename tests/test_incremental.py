# SPDX-License-Identifier: AGPL-3.0-or-later
"""Incremental updates: only new/changed files are embedded, removed files'
chunks disappear, and changed chunk settings demand a rebuild."""

import os

import pytest

from relevantr import pipeline
from relevantr.config import AppConfig
from relevantr.store import RebuildRequiredError

from conftest import make_pdf


@pytest.fixture
def corpus(tmp_path, spy_embedder):
    pdf_dir = tmp_path / "papers"
    db_dir = tmp_path / "database"
    make_pdf(pdf_dir / "alpha.pdf", ["Alpha paper about dislocation glide."])
    make_pdf(pdf_dir / "beta.pdf", ["Beta paper about vacancy diffusion."])
    config = AppConfig(pdf_dir=str(pdf_dir), db_dir=str(db_dir),
                       use_reranker=False)
    summary = pipeline.build_index(config, spy_embedder)
    assert sorted(summary.added) == ["alpha.pdf", "beta.pdf"]
    return config, pdf_dir


def test_add_pdf_embeds_only_new_file(corpus, spy_embedder):
    config, pdf_dir = corpus
    spy_embedder.embedded_texts.clear()
    make_pdf(pdf_dir / "gamma.pdf", ["Gamma paper about twin boundaries."])

    summary = pipeline.update_index(config, spy_embedder)
    assert summary.added == ["gamma.pdf"]
    assert summary.changed == [] and summary.removed == []
    assert spy_embedder.embedded_texts, "the new file must be embedded"
    assert all("Gamma" in t for t in spy_embedder.embedded_texts), (
        "only the new file's chunks may be embedded"
    )


def test_unchanged_files_never_reembedded(corpus, spy_embedder):
    config, _ = corpus
    spy_embedder.embedded_texts.clear()
    summary = pipeline.update_index(config, spy_embedder)
    assert summary.nothing_to_do
    assert spy_embedder.embedded_texts == []


def test_remove_pdf_removes_chunks(corpus, spy_embedder):
    config, pdf_dir = corpus
    os.remove(pdf_dir / "beta.pdf")
    summary = pipeline.update_index(config, spy_embedder)
    assert summary.removed == ["beta.pdf"]

    passages = pipeline.query_index(config, spy_embedder, "vacancy diffusion beta")
    assert all(p.source != "beta.pdf" for p in passages)
    info = pipeline.index_info(config)
    assert info["documents"] == 1


def test_changed_pdf_reembedded(corpus, spy_embedder):
    config, pdf_dir = corpus
    make_pdf(pdf_dir / "alpha.pdf",
             ["Alpha paper rewritten, now about superalloys."])
    spy_embedder.embedded_texts.clear()
    summary = pipeline.update_index(config, spy_embedder)
    assert summary.changed == ["alpha.pdf"]
    assert all("superalloys" in t or "Alpha" in t for t in spy_embedder.embedded_texts)

    passages = pipeline.query_index(config, spy_embedder, "superalloys rewritten")
    assert any(p.source == "alpha.pdf" and "superalloys" in p.text for p in passages)


def test_changed_chunk_settings_demand_rebuild(corpus, spy_embedder):
    config, _ = corpus
    config.chunk_size = 400
    config.chunk_overlap = 50
    with pytest.raises(RebuildRequiredError):
        pipeline.update_index(config, spy_embedder)
    # and the check that the GUI/CLI use reports the same
    reason = pipeline.check_rebuild_needed(config, spy_embedder.name)
    assert reason and "chunk settings" in reason

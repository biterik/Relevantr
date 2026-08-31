"""Store: LanceDB roundtrip via hybrid search, and mismatch detection."""

import pytest

from relevantr.config import AppConfig
from relevantr.ingest import Chunk
from relevantr.store import (
    EmbeddingMismatchError,
    IndexStore,
    LocationUnavailableError,
    Manifest,
    RebuildRequiredError,
)

from conftest import FakeEmbedder


def make_store(tmp_path, embedder, chunks):
    store = IndexStore(tmp_path / "db")
    manifest = Manifest(
        pdf_dir=str(tmp_path / "pdfs"),
        embedding_model=embedder.name,
        embedding_dim=embedder.dim,
        chunk_size=800,
        chunk_overlap=150,
    )
    store.create(manifest)
    if chunks:
        vectors = embedder.embed_documents([c.text for c in chunks])
        store.add_chunks(chunks, vectors)
        store.rebuild_fts()
    return store, manifest


CHUNKS = [
    Chunk("Dislocation mobility in nickel alloys.", "a.pdf", 1, "a.pdf::p1::c0"),
    Chunk("The melting point of zirconium hydride is remarkable.", "b.pdf", 3,
          "b.pdf::p3::c0"),
    Chunk("Grain boundaries influence crack propagation.", "c.pdf", 2,
          "c.pdf::p2::c0"),
]


def test_hybrid_roundtrip(tmp_path, fake_embedder):
    store, _ = make_store(tmp_path, fake_embedder, CHUNKS)
    query = "zirconium hydride melting point"
    results = store.search_hybrid(query, fake_embedder.embed_query(query), k=3)
    assert results
    top = results[0]
    assert top["source"] == "b.pdf"
    assert top["page"] == 3
    assert "zirconium" in top["text"]


def test_mismatched_model_refused(tmp_path, fake_embedder):
    store, manifest = make_store(tmp_path, fake_embedder, CHUNKS)
    other = FakeEmbedder(name="fake:other-model", dim=64)
    with pytest.raises(EmbeddingMismatchError, match="rebuild"):
        store.check_compatible(manifest, other, 800, 150)


def test_changed_chunk_settings_refused(tmp_path, fake_embedder):
    store, manifest = make_store(tmp_path, fake_embedder, CHUNKS)
    with pytest.raises(RebuildRequiredError):
        store.check_compatible(manifest, fake_embedder, 400, 50)


def test_matching_settings_accepted(tmp_path, fake_embedder):
    store, manifest = make_store(tmp_path, fake_embedder, CHUNKS)
    store.check_compatible(manifest, fake_embedder, 800, 150)


def test_missing_db_dir_is_unavailable_not_created(tmp_path, fake_embedder):
    missing = tmp_path / "not-mounted" / "db"
    store = IndexStore(missing)
    with pytest.raises(LocationUnavailableError, match="not available"):
        store.open_existing()
    assert not missing.exists()  # no silent re-creation of an empty index


def test_corrupt_manifest_demands_rebuild(tmp_path, fake_embedder):
    store, _ = make_store(tmp_path, fake_embedder, [])
    store.manifest_path.write_text("{not json", encoding="utf-8")
    with pytest.raises(RebuildRequiredError, match="corrupt"):
        store.open_existing()


def test_legacy_chroma_detected(tmp_path):
    legacy = tmp_path / "db"
    legacy.mkdir()
    (legacy / "chroma.sqlite3").write_bytes(b"")
    from relevantr.store import LegacyIndexError

    with pytest.raises(LegacyIndexError, match="v1"):
        IndexStore(legacy).open_existing()


def test_moved_index_reopens(tmp_path, fake_embedder):
    """The DB dir is self-contained: copying it elsewhere must just work."""
    import shutil

    store, _ = make_store(tmp_path, fake_embedder, CHUNKS)
    moved = tmp_path / "elsewhere" / "db"
    moved.parent.mkdir()
    shutil.copytree(store.db_dir, moved)

    config = AppConfig(db_dir=str(moved))
    from relevantr import pipeline

    store2, manifest2 = pipeline.open_for_query(config, fake_embedder)
    query = "zirconium hydride melting point"
    results = store2.search_hybrid(query, fake_embedder.embed_query(query), k=3)
    assert results[0]["source"] == "b.pdf"

"""Independent storage locations: PDF dir and DB dir on different paths,
and clear messages when a location is unavailable."""

import shutil

import pytest

from relevantr import pipeline
from relevantr.config import AppConfig
from relevantr.store import LocationUnavailableError

from conftest import make_pdf


def test_separated_locations_work(tmp_path):
    """Index built with the DB dir in a different tree than the PDF dir."""
    pdf_dir = tmp_path / "library" / "papers"
    db_dir = tmp_path / "other-drive" / "relevantr-index"
    db_dir.parent.mkdir(parents=True)
    make_pdf(pdf_dir / "one.pdf", ["A paper about niobium precipitates."])

    from conftest import FakeEmbedder

    embedder = FakeEmbedder()
    config = AppConfig(pdf_dir=str(pdf_dir), db_dir=str(db_dir), use_reranker=False)
    pipeline.build_index(config, embedder)

    assert (db_dir / "manifest.json").exists()
    passages = pipeline.query_index(config, embedder, "niobium precipitates")
    assert passages and passages[0].source == "one.pdf"


def test_missing_pdf_dir_message(tmp_path, fake_embedder):
    pdf_dir = tmp_path / "papers"
    db_dir = tmp_path / "db"
    make_pdf(pdf_dir / "one.pdf", ["Content about niobium."])
    config = AppConfig(pdf_dir=str(pdf_dir), db_dir=str(db_dir), use_reranker=False)
    pipeline.build_index(config, fake_embedder)

    shutil.rmtree(pdf_dir)  # e.g. the drive with the papers is unmounted
    with pytest.raises(LocationUnavailableError) as excinfo:
        pipeline.update_index(config, fake_embedder)
    assert "not available" in str(excinfo.value)
    # querying the existing index still works without the PDF dir
    passages = pipeline.query_index(config, fake_embedder, "niobium")
    assert passages


def test_missing_db_dir_message(tmp_path, fake_embedder):
    config = AppConfig(pdf_dir=str(tmp_path), db_dir=str(tmp_path / "gone" / "db"))
    with pytest.raises(LocationUnavailableError, match="not available"):
        pipeline.query_index(config, fake_embedder, "anything")
    assert not (tmp_path / "gone").exists()


def test_unmounted_volume_message():
    from relevantr.store import describe_unavailable

    msg = describe_unavailable("/Volumes/MissingDisk-xyz/relevantr", "database")
    assert "mounted" in msg


def test_repoint_pdf_dir(tmp_path, fake_embedder):
    """Moving the library: re-confirm the PDF dir once, manifest is updated."""
    pdf_dir = tmp_path / "papers"
    db_dir = tmp_path / "db"
    make_pdf(pdf_dir / "one.pdf", ["Content about niobium."])
    config = AppConfig(pdf_dir=str(pdf_dir), db_dir=str(db_dir), use_reranker=False)
    pipeline.build_index(config, fake_embedder)

    new_pdf_dir = tmp_path / "moved-papers"
    shutil.move(str(pdf_dir), str(new_pdf_dir))
    pipeline.repoint_pdf_dir(config, str(new_pdf_dir))
    summary = pipeline.update_index(config, fake_embedder)
    assert summary.nothing_to_do  # same files, just a new location
    assert pipeline.index_info(config)["pdf_dir"] == str(new_pdf_dir)

"""End-to-end test with two tiny generated PDFs and the real local embedding
backend (Qwen/Qwen3-Embedding-0.6B). Skipped unless the model is already
downloaded to the Hugging Face cache."""

import pytest

from conftest import make_pdf


def _local_model_cached() -> bool:
    try:
        from huggingface_hub import snapshot_download

        from relevantr.config import LOCAL_EMBEDDING_MODEL

        snapshot_download(LOCAL_EMBEDDING_MODEL, local_files_only=True)
        return True
    except Exception:
        return False


pytestmark = [
    pytest.mark.local_model,
    pytest.mark.skipif(
        not _local_model_cached(),
        reason="local embedding model not downloaded (see pip install '.[local]')",
    ),
]


def test_end_to_end_local(tmp_path):
    from relevantr import pipeline
    from relevantr.config import AppConfig
    from relevantr.embed import LocalEmbedding

    pdf_dir = tmp_path / "papers"
    db_dir = tmp_path / "separate" / "db"
    db_dir.parent.mkdir()
    make_pdf(
        pdf_dir / "hydrogen.pdf",
        ["Hydrogen embrittlement reduces the ductility of austenitic steels.",
         "The second page discusses trap binding energies of vacancies."],
    )
    make_pdf(
        pdf_dir / "creep.pdf",
        ["Creep in nickel-base superalloys is controlled by rafting of the "
         "gamma-prime precipitates at high temperature."],
    )

    embedder = LocalEmbedding()
    config = AppConfig(pdf_dir=str(pdf_dir), db_dir=str(db_dir),
                       use_reranker=False, final_n=3)
    summary = pipeline.build_index(config, embedder)
    assert summary.chunks_embedded >= 3

    passages = pipeline.query_index(
        config, embedder, "What controls creep in superalloys?"
    )
    assert passages
    assert passages[0].source == "creep.pdf"
    assert passages[0].page == 1

    passages = pipeline.query_index(
        config, embedder, "hydrogen embrittlement of steels"
    )
    assert passages[0].source == "hydrogen.pdf"

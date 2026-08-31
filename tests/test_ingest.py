"""Chunking: page metadata preserved, overlap correct, token counts in range."""

import pytest

from relevantr.ingest import SimpleTokenizer, TokenSplitter, chunk_pdf

from conftest import make_pdf


def words(n, prefix="word"):
    return " ".join(f"{prefix}{i}" for i in range(n))


def test_short_text_single_chunk():
    splitter = TokenSplitter(chunk_size=100, overlap=20)
    chunks = splitter.split("A short sentence about dislocations.")
    assert len(chunks) == 1
    assert "dislocations" in chunks[0]


def test_token_counts_in_range():
    tokenizer = SimpleTokenizer()
    splitter = TokenSplitter(chunk_size=50, overlap=10, tokenizer=tokenizer)
    chunks = splitter.split(words(400))
    assert len(chunks) > 1
    for chunk in chunks:
        assert len(tokenizer.encode(chunk)) <= 50
    # all but the last window should be full-size
    for chunk in chunks[:-1]:
        assert len(tokenizer.encode(chunk)) == 50


def test_overlap_correct():
    tokenizer = SimpleTokenizer()
    splitter = TokenSplitter(chunk_size=50, overlap=10, tokenizer=tokenizer)
    chunks = splitter.split(words(200))
    assert len(chunks) >= 3
    for a, b in zip(chunks, chunks[1:]):
        tokens_a = tokenizer.encode(a)
        tokens_b = tokenizer.encode(b)
        tail = tokenizer.decode(tokens_a[-10:]).strip()
        head = tokenizer.decode(tokens_b[:10]).strip()
        assert tail == head


def test_default_tokenizer_counts_bounded():
    # with the default (tiktoken if available) tokenizer, re-encoded chunks
    # stay close to the requested budget
    splitter = TokenSplitter(chunk_size=50, overlap=10)
    chunks = splitter.split(words(400))
    assert len(chunks) > 1
    for chunk in chunks:
        assert len(splitter.tokenizer.encode(chunk)) <= 52


def test_nothing_lost():
    splitter = TokenSplitter(chunk_size=50, overlap=10)
    chunks = splitter.split(words(173))
    joined = " ".join(chunks)
    for i in range(173):
        assert f"word{i}" in joined


def test_page_metadata_preserved(tmp_path):
    pdf = make_pdf(
        tmp_path / "paper.pdf",
        ["Page one talks about vacancies.", "Page two talks about dislocations.",
         "Page three talks about cracks."],
    )
    chunks = chunk_pdf(pdf, TokenSplitter(chunk_size=100, overlap=20))
    assert {c.page for c in chunks} == {1, 2, 3}
    assert all(c.source == "paper.pdf" for c in chunks)
    by_page = {c.page: c.text for c in chunks}
    assert "vacancies" in by_page[1]
    assert "dislocations" in by_page[2]
    assert "cracks" in by_page[3]
    assert len({c.chunk_id for c in chunks}) == len(chunks)


def test_invalid_overlap_rejected():
    with pytest.raises(ValueError):
        TokenSplitter(chunk_size=100, overlap=100)

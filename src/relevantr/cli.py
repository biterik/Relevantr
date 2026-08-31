"""Command-line interface.

    python -m relevantr                     # launches the GUI
    python -m relevantr index --pdf-dir P --db-dir D
    python -m relevantr update
    python -m relevantr rebuild
    python -m relevantr info
    python -m relevantr query "question"    # retrieval-only, prints passages

The CLI reads the same JSON config as the GUI; --pdf-dir/--db-dir override it
for the invocation without persisting.
"""

from __future__ import annotations

import argparse
import sys

from . import __version__
from .config import AppConfig
from .store import StoreError, detect_legacy_chroma


def make_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="relevantr",
        description="Relevantr - scientific PDF retrieval (RAG). "
        "Run without a subcommand to open the GUI.",
    )
    parser.add_argument("--version", action="version", version=f"relevantr {__version__}")
    sub = parser.add_subparsers(dest="command")

    def add_common(p, pdf=True):
        if pdf:
            p.add_argument("--pdf-dir", help="Directory containing the PDF papers")
        p.add_argument("--db-dir", help="Directory for the index database")
        p.add_argument(
            "--backend",
            choices=["local", "gwdg"],
            help="Embedding backend (default: from saved config)",
        )
        p.add_argument("--chunk-size", type=int, help="Chunk size in tokens")
        p.add_argument("--chunk-overlap", type=int, help="Chunk overlap in tokens")

    p_index = sub.add_parser("index", help="Build a new index from a PDF directory")
    add_common(p_index)

    p_update = sub.add_parser(
        "update", help="Incremental update: embed only new/changed PDFs"
    )
    add_common(p_update)

    p_rebuild = sub.add_parser("rebuild", help="Re-extract and re-embed everything")
    add_common(p_rebuild)

    p_info = sub.add_parser("info", help="Show index manifest (locations, model, counts)")
    p_info.add_argument("--db-dir", help="Directory of the index database")

    p_query = sub.add_parser("query", help="Retrieval-only query; prints passages")
    p_query.add_argument("question")
    p_query.add_argument("--db-dir", help="Directory of the index database")
    p_query.add_argument(
        "--backend", choices=["local", "gwdg"], help="Embedding backend"
    )
    p_query.add_argument("-k", "--retrieve-k", type=int, help="Candidates to retrieve")
    p_query.add_argument("-n", "--final-n", type=int, help="Passages to keep")
    p_query.add_argument(
        "--no-rerank", action="store_true", help="Skip the cross-encoder reranker"
    )
    return parser


def load_config(args) -> AppConfig:
    config = AppConfig.load()
    for attr, arg in [
        ("pdf_dir", "pdf_dir"),
        ("db_dir", "db_dir"),
        ("embedding_backend", "backend"),
        ("chunk_size", "chunk_size"),
        ("chunk_overlap", "chunk_overlap"),
        ("retrieve_k", "retrieve_k"),
        ("final_n", "final_n"),
    ]:
        value = getattr(args, arg, None)
        if value is not None:
            setattr(config, attr, value)
    if getattr(args, "no_rerank", False):
        config.use_reranker = False
    return config


def _progress(current, total, message):
    print(f"[{current}/{total}] {message}", flush=True)


def _warn_legacy(config: AppConfig):
    legacy = detect_legacy_chroma(config.db_dir)
    if legacy:
        print(
            f"Note: '{legacy}' holds a Relevantr v1 (ChromaDB) index. v2 cannot "
            "read it; rebuild the index from your PDF folder.",
            file=sys.stderr,
        )


def run_cli(argv: list[str]) -> int:
    parser = make_parser()
    args = parser.parse_args(argv)

    if args.command is None:
        from .gui.app import run_gui

        run_gui()
        return 0

    config = load_config(args)

    try:
        if args.command == "info":
            from . import pipeline

            _warn_legacy(config)
            info = pipeline.index_info(config)
            width = max(len(k) for k in info)
            for key, value in info.items():
                print(f"{key.ljust(width)}  {value}")
            return 0

        from . import pipeline
        from .embed import get_backend

        if args.command in ("index", "rebuild"):
            if not config.pdf_dir:
                parser.error("no PDF directory configured; pass --pdf-dir")
            embedder = get_backend(config)
            summary = pipeline.build_index(config, embedder, progress=_progress)
            print(summary.describe())
            print(f"Index written to {config.db_dir}")
            return 0

        if args.command == "update":
            embedder = get_backend(config)
            if args.pdf_dir:
                # allow re-confirming the PDF dir after moving the library
                pipeline.repoint_pdf_dir(config, args.pdf_dir)
            summary = pipeline.update_index(config, embedder, progress=_progress)
            print(summary.describe())
            return 0

        if args.command == "query":
            embedder = get_backend(config)
            passages = pipeline.query_index(config, embedder, args.question)
            if not passages:
                print("No passages found.")
                return 0
            for i, p in enumerate(passages, 1):
                print(f"\n[{i}] {p.source} (Page: {p.page})  score={p.score:.4f}")
                print("-" * 72)
                print(p.text.strip())
            return 0

    except StoreError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        return 130

    parser.error(f"unknown command {args.command!r}")
    return 2

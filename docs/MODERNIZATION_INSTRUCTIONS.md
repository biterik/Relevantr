# Relevantr v2 — Modernization instructions for Claude Code

Audience: Claude Code, working in `/Users/e.bitzek/DEVEL/Relevantr`.
These decisions were discussed with and approved by Erik Bitzek on 2026-08-31. Do not
re-litigate them; ask only if something below is contradictory or impossible.

## Why

Relevantr v1 (Aug 2025) is a scientific PDF RAG (Retrieval-Augmented Generation)
desktop app. It is broken by upstream deprecations: the `google-generativeai` SDK is
deprecated, the Gemini 1.5 models are retired, and `text-embedding-004` is deprecated.
It is also hard-wired to Google for both embeddings and generation, uses pure dense
similarity search (weak for exact scientific terms, formulas, author names), and has
accumulated repo clutter.

## Agreed target design

1. **Embeddings — configurable, two backends behind one interface:**
   - Default: **local `Qwen/Qwen3-Embedding-0.6B`** via `sentence-transformers`
     (device auto-select: MPS (Metal Performance Shaders) on macOS, CUDA, else CPU).
     Use the model's retrieval instruction/prompt for queries (`prompt_name="query"`),
     plain encoding for documents.
   - Alternative: **GWDG (Gesellschaft für wissenschaftliche Datenverarbeitung
     Göttingen) Chat AI embeddings API**, model `qwen3-embedding-4b`, via the
     OpenAI-compatible `/embeddings` endpoint at
     `https://chat-ai.academiccloud.de/v1` (API key in env var `GWDG_API_KEY`).
   - The index must record which embedding model (name + dimension) built it and
     refuse to open/append with a mismatched backend — offer "rebuild index" instead.

2. **Vector database — LanceDB** (embedded, no server), replacing ChromaDB.
   - One table per corpus: columns `vector`, `text`, `source` (PDF filename),
     `page` (int), `chunk_id`.
   - Create a full-text search (FTS, BM25-based) index on `text`.
   - Query with LanceDB **hybrid search** (`query_type="hybrid"`) fusing vector +
     BM25 results (default Reciprocal Rank Fusion reranker is fine at this stage).
   - **Both storage locations are user-chosen, independently of each other:**
     the PDF (papers) directory AND the database directory are free paths that may
     live on different drives (external disk, network volume). The database
     location defaults to the `platformdirs` user-data dir but is selectable in
     Settings and on the CLI (`--db-dir`); never store the index in the CWD.
     Handle an unavailable location gracefully (unmounted external drive →
     clear "drive not mounted" message, no crash, no silent re-creation of an
     empty index elsewhere).
   - Each index stores a small manifest (JSON alongside the LanceDB table):
     the PDF directory it indexes, embedding model + dimension, chunk
     size/overlap, creation/update timestamps, and a per-file record
     (filename, size, mtime, content hash) to support incremental updates.
     Detect a legacy `vector_db/` (Chroma) directory and tell the user it must
     be rebuilt.

3. **Reranker — local cross-encoder stage, on by default (toggleable):**
   - Retrieve ~30 candidates by hybrid search → rerank with
     `BAAI/bge-reranker-v2-m3` (via `sentence_transformers.CrossEncoder`) →
     keep top `n` (default 8) for display / the LLM.
   - Make retrieve-k, final-n, and reranker on/off configurable in Settings.

4. **LLM layer — optional, provider-configurable, default OFF:**
   - The app **starts in retrieval-only mode**: a query returns the reranked
     passages with source attribution (filename + page), no LLM call at all.
     This mode must work fully offline when local embeddings are selected.
   - When the user enables an LLM answer, use ONE OpenAI-compatible client
     (`openai` Python package). The provider is chosen in the **Settings menu
     via a preset dropdown** — GWDG Chat AI is only available to German
     academic users, so the app must make it equally easy for anyone to plug
     in their own API:
     - Presets (each prefills base URL + a sensible default model; the user
       supplies their own API key): **GWDG Chat AI**
       (`https://chat-ai.academiccloud.de/v1`, default `openai-gpt-oss-120b`,
       note "free for German academic users"), **OpenAI**
       (`https://api.openai.com/v1`), **Google Gemini** (OpenAI-compatible
       endpoint `https://generativelanguage.googleapis.com/v1beta/openai/`),
       **Ollama (local)** (`http://localhost:11434/v1`, no key needed), and
       **Custom** (free-text base URL, model, key — covers any
       OpenAI-compatible service, institutional gateways included).
     - After base URL + key are set, query `GET /v1/models` to populate the
       model dropdown dynamically; fall back to a free-text model field if the
       endpoint doesn't support listing.
     - **API keys are entered in the Settings dialog** and stored in the OS
       credential store via the `keyring` package (macOS Keychain, Windows
       Credential Manager, Secret Service on Linux) — never in plaintext
       config or the repo. An environment variable per provider (e.g.
       `GWDG_API_KEY`, `OPENAI_API_KEY`, or a generic `RELEVANTR_API_KEY`)
       overrides the stored key for scripted use. If `keyring` has no usable
       backend, degrade to session-only (key kept in memory, re-entered next
       launch) with a note in the dialog.
     - No key is ever required to use the app: local embeddings +
       retrieval-only mode must work out of the box for every user.
   - Keep the strict source-attribution prompt from v1 (it is good); pass the
     reranked passages as context.
   - Every LLM answer view must still expose the underlying passages (keep the
     v1 double-click-source-to-see-passage behavior).

5. **Corpus and index management — first-class, easy, documented:**
   - **Add / update (incremental):** an "Update index" action scans the PDF
     directory, compares against the manifest (new, changed, removed files —
     changed detected via size/mtime, confirmed by content hash), embeds only
     new/changed files, and deletes chunks belonging to removed files. Adding
     papers must be: drop PDFs into the folder → click "Update index" (or run
     the CLI command). Never re-embed unchanged files.
   - **Rebuild (full recreation):** a "Rebuild index" action re-extracts and
     re-embeds everything from scratch. The app must itself detect when a
     rebuild is required — embedding backend/model changed, chunk settings
     changed, manifest missing/corrupt — explain why, and offer the rebuild
     with a time estimate (files × observed embed rate); until confirmed, the
     old index keeps working for queries.
   - **CLI in addition to the GUI**, so all of this is scriptable:
     `python -m relevantr index --pdf-dir <path> --db-dir <path>`,
     `... update`, `... rebuild`, `... info` (show manifest: locations, model,
     counts), `... query "<question>"` (retrieval-only, prints passages).
     GUI and CLI share the same config and code paths.
   - Moving an index is supported: the DB directory is self-contained
     (LanceDB table + manifest), so copying it to another drive and pointing
     Settings/`--db-dir` at the new location must just work; only the absolute
     PDF-directory path in the manifest may need re-confirming (prompt once,
     update manifest).

6. **Drop LangChain entirely.** Use `pymupdf` directly for extraction, write a
   small token-aware splitter (target ~800 tokens, ~150 overlap, configurable;
   `tiktoken` or the embedding tokenizer for counting), preserve per-page
   metadata so page numbers in citations stay exact.

7. **GUI — keep Tkinter, evolve it:**
   - Add a Settings panel: **PDF directory picker and database directory picker
     (two independent choosers, any drive)**, embedding backend, the LLM
     provider section described in item 4 (preset dropdown, base URL, model
     dropdown, API-key entry with a "test connection" button), reranker
     toggle, retrieve-k / final-n, chunk size/overlap.
   - Toolbar buttons for "Update index" (incremental) and "Rebuild index"
     (full), with a status line showing current locations, embedding model,
     and document/chunk counts (from the manifest).
   - Add a prominent "Answer with LLM: on/off" toggle in the main window.
   - Keep: processing progress, results pane with clickable sources, export.
   - Long operations (indexing, querying) must not block the Tk main loop —
     keep the existing threading approach.

## Repo restructuring

- New layout: `pyproject.toml` + `src/relevantr/` package with modules roughly:
  `config.py`, `ingest.py` (PDF → chunks), `embed.py` (backend interface + the
  two backends), `store.py` (LanceDB), `rerank.py`, `llm.py`, `gui/`, `__main__.py`
  (so `python -m relevantr` launches the GUI). Optional console entry point
  `relevantr`.
- Dependencies: `lancedb`, `pymupdf`, `openai`, `sentence-transformers` (extra
  `[local]` if you want to keep the base install light), `platformdirs`,
  `keyring`, `python-dotenv`, `tqdm`. No `langchain*`, no `chromadb`, no
  `google-generativeai`.
- Config persistence: JSON in the platformdirs user-config dir (provider
  choice, base URL, model, paths, tuning parameters). API keys live only in
  the OS keyring or environment / `.env` — never in the JSON or the repo.
- Delete: `relevantr_original_backup.py`, `relevantr_fixed.spec`,
  `relentr_simple.spec`, `build_windows_simple.py`, `build_app.py`,
  `build_script.sh` — keep ONE PyInstaller path per platform (`build_mac.py`,
  `build_windows.py`, each with its `.spec`), updated for the new package
  layout. (If deletion is not permitted in the session, move them to
  `_to_delete/`.)
- Keep `.github/workflows/repo-vitals.yml`, `CITATION.cff` (bump version to 2.0),
  `assets/`, `LICENSE` untouched.
- Much of v1's defensive network-debug scaffolding (gRPC/DNS workarounds, REST
  transport forcing) existed for the old Google SDK — drop it; keep a simple
  connectivity check for the configured API base URL.

## Tests

Rewrite the test scripts as a proper `tests/` suite (pytest):
- chunking: page metadata preserved, overlap correct, token counts in range;
- store: LanceDB roundtrip (insert → hybrid search returns the planted chunk),
  embedding-model-mismatch detection;
- rerank: ordering changes when the cross-encoder is applied (small fixture);
- llm: prompt assembly and retrieval-only path with a mocked client;
- incremental update: add a PDF → only it is embedded; remove one → its chunks
  disappear; change chunk settings → rebuild is demanded, not a silent mix;
- separated locations: index built with `--db-dir` in a different temp dir than
  the PDF dir works; opening with the PDF dir path missing gives the clear
  "location unavailable" message;
- a small end-to-end test with 2 tiny generated PDFs and the local embedding
  backend (skip with a marker if the model isn't downloaded).

## README rewrite

Rewrite `README.md` for v2: what it does, the pipeline diagram (ingest →
hybrid retrieval → rerank → optional LLM), install (pip + conda), quick start,
retrieval-only/offline mode, settings reference, a **"Connecting an AI
provider"** section written for an international audience — the preset table
(GWDG marked as the free option for German academic users, with the Academic
Cloud / KISSKI key steps; OpenAI; Google Gemini; local Ollama; any custom
OpenAI-compatible endpoint), where to paste the key in Settings, and the
env-var override — and a dedicated
**"Managing your library and database"** section: choosing the PDF and database
locations independently (external drives included, with the unmounted-drive
behavior), adding new papers (drop in folder → Update index, GUI and CLI),
rebuilding from scratch and exactly which changes require it (embedding model,
chunk settings), moving the database to another drive, and expected disk usage
and indexing time per 100 PDFs. Then: CLI reference, migration note (v1 Chroma
indexes cannot be reused — reprocess the PDF folder), build instructions, and the
existing disclaimers. Spell out every abbreviation at first use (RAG, BM25, FTS,
MTEB, etc.). Keep the logo and tone. Also update `environment.yml` and drop
`requirements.txt` in favor of `pyproject.toml` (or keep a generated one — your
call, but say so in the README).

## Verification before finishing

1. `pytest` green.
2. Fresh venv install from `pyproject.toml`; `python -m relevantr` opens the GUI.
3. Index a folder of 3–5 real PDFs with local embeddings, with the database
   directory deliberately placed outside the PDF directory; ask a question in
   retrieval-only mode; verify passages carry correct filename + page. Then add
   one more PDF, run "Update index", and confirm only that file was embedded.
4. If `GWDG_API_KEY` is set in the environment: verify `/v1/models` listing,
   one embeddings call with `qwen3-embedding-4b`, and one LLM answer end-to-end.
   If not set, mock and note it in the summary.
5. Summarize what changed in the final report; do not tag a release.

<p align="center">
  <img src="assets/Relevantr_logo2.png" alt="Relevantr Logo" width="400"/>
</p>
<p align="center"><em>A Scientific PDF RAG Application for Advanced Literature Analysis</em></p>

**Relevantr** is a desktop application for asking questions about your own collection of scientific PDF papers. It is a RAG (Retrieval-Augmented Generation) tool: it indexes your papers locally, finds the passages most relevant to a question, and — only if you want — hands those passages to an AI model to compose an answer with precise source attribution (file name and page number for every claim).

**Version 2.0** is a full modernization: local embeddings that work completely offline, hybrid search (semantic vectors + exact keyword matching), a cross-encoder reranking stage, and a provider-agnostic AI layer that works with any OpenAI-compatible service — or with none at all.

## ✨ Features

- 🔍 **Hybrid search** — combines semantic vector search with BM25 (Best Match 25, a classic keyword-ranking algorithm), so exact scientific terms, formulas, and author names are found as reliably as paraphrases
- 🖥️ **Works fully offline** — the default embedding model runs on your own machine; retrieval-only mode needs no API key and no internet
- 🎯 **Cross-encoder reranking** — a second, more accurate model re-scores the candidates so the best passages come out on top
- 🤖 **Optional AI answers** — plug in any OpenAI-compatible provider (GWDG Chat AI, OpenAI, Google Gemini, a local Ollama, your institution's gateway); off by default
- 📖 **Strict source attribution** — answers cite file name and page; double-click any source to read the exact passage behind it
- 📂 **Free choice of locations** — your PDF folder and the search database are chosen independently and may live on different drives
- ♻️ **Incremental updates** — drop new PDFs into your folder and click "Update index"; unchanged papers are never re-processed
- ⌨️ **GUI and CLI** — everything the GUI (graphical user interface) does is also scriptable from the CLI (command-line interface)
- 📤 **Export results** — save answers and passages to text or Markdown files

## 🏗️ The pipeline

```
 PDF folder                                    your question
     │                                              │
     ▼                                              ▼
 ┌─────────┐    ┌────────────────┐    ┌──────────────────────────┐
 │ Ingest  │    │  Index (LanceDB)│   │   Hybrid retrieval       │
 │ pymupdf │───▶│  vectors + FTS  │──▶│  vector + BM25 (~30 hits)│
 │ + chunk │    └────────────────┘    └────────────┬─────────────┘
 └─────────┘                                       ▼
                                      ┌──────────────────────────┐
                                      │  Rerank (cross-encoder)  │
                                      │  keep the best ~8        │
                                      └────────────┬─────────────┘
                                                   ▼
                             ┌─────────────────────┴───────────────────┐
                             │ passages with file + page (always)      │
                             │ + optional LLM answer (if switched on)  │
                             └─────────────────────────────────────────┘
```

- **Ingest**: text is extracted per page with [PyMuPDF](https://pymupdf.readthedocs.io/) and split into chunks of ~800 tokens with ~150 tokens of overlap (configurable). Chunks never cross page boundaries, so page numbers in citations stay exact.
- **Index**: chunks and their embedding vectors are stored in [LanceDB](https://lancedb.com), an embedded vector database (no server), together with an FTS (full-text search) index based on BM25.
- **Embeddings**: by default the local model [Qwen3-Embedding-0.6B](https://huggingface.co/Qwen/Qwen3-Embedding-0.6B) (a top performer on the MTEB — Massive Text Embedding Benchmark — leaderboard for its size), running on Apple's Metal GPU, CUDA (Compute Unified Device Architecture, NVIDIA's GPU platform), or CPU — whichever is available. Alternatively, the GWDG Chat AI embeddings API.
- **Rerank**: the top ~30 hybrid hits are re-scored by the cross-encoder [BAAI/bge-reranker-v2-m3](https://huggingface.co/BAAI/bge-reranker-v2-m3), and the best ~8 are kept. Can be toggled off in Settings.
- **LLM (Large Language Model) answer**: optional and off by default. When on, the reranked passages are sent to the configured provider with a strict "cite everything" prompt.

## 🚀 Quick start

### Prerequisites

- Python 3.10 or newer (3.11+ recommended)
- ~4 GB of free disk space for the local models (downloaded automatically on first use)
- No API key needed for the default (local, retrieval-only) setup

### Installation

Dependencies are declared in `pyproject.toml` (there is no `requirements.txt` anymore — v1's was dropped in favor of the packaged install below).

#### Using pip

```bash
git clone https://github.com/biterik/Relevantr.git
cd Relevantr
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -e ".[local]"       # includes the local embedding + reranker models
```

#### Using conda

```bash
git clone https://github.com/biterik/Relevantr.git
cd Relevantr
conda env create -f environment.yml
conda activate relevantr
```

### First run

```bash
python -m relevantr             # opens the GUI  (or simply: relevantr)
```

1. Open **Settings…** and choose your **PDF directory** (where your papers are) and, if you like, a different **database directory** (where the index goes — defaults to your user data folder).
2. Click **Rebuild Index** to build the index for the first time. The first run also downloads the embedding model (~1.2 GB).
3. Type a question and click **Ask**. You get the most relevant passages, each labeled with file name and page. Double-click a source to read the passage.
4. Optionally flip on **"Answer with LLM"** once you have configured an AI provider (see below).

Or entirely from the command line:

```bash
python -m relevantr index --pdf-dir ~/Papers --db-dir ~/RelevantrIndex
python -m relevantr query "Which papers discuss hydrogen embrittlement?"
```

## 🔌 Retrieval-only / offline mode

Relevantr starts in **retrieval-only mode**: a query returns the reranked passages with their sources — no AI-generated text, no API call, no key. With the default local embedding backend this works **completely offline** (after the one-time model download). This mode is often all you need to locate the right paper and page, and it is immune to AI hallucination: everything you see is verbatim from your PDFs.

## 🤖 Connecting an AI provider

To get composed answers ("Answer with LLM" toggle in the main window), connect any OpenAI-compatible service. Open **Settings… → AI provider**, pick a preset, and paste your API key into the **API key** field — that's it. The key is stored in your operating system's credential store (macOS Keychain, Windows Credential Manager, Secret Service on Linux) via the `keyring` library — never in a config file and never in this repository. If no credential store is available, the key is kept for the current session only and you'll be asked again next launch.

| Preset | Base URL | Who it's for | Key |
|---|---|---|---|
| **GWDG Chat AI** | `https://chat-ai.academiccloud.de/v1` | **Free for German academic users.** Log in at [Academic Cloud](https://academiccloud.de) with your institution account, then request an API key via the [KISSKI Chat AI service](https://kisski.gwdg.de/en/leistungen/2-02-llm-service/) ("Chat AI" → API access). | `GWDG_API_KEY` |
| **OpenAI** | `https://api.openai.com/v1` | Anyone with an [OpenAI API account](https://platform.openai.com) (paid). | `OPENAI_API_KEY` |
| **Google Gemini** | `https://generativelanguage.googleapis.com/v1beta/openai/` | Anyone with a [Google AI Studio](https://aistudio.google.com) key; Gemini's OpenAI-compatible endpoint is used. | `GEMINI_API_KEY` |
| **Ollama (local)** | `http://localhost:11434/v1` | Fully local models via [Ollama](https://ollama.com) — private, free, no key at all. | — |
| **Custom** | anything | Any other OpenAI-compatible endpoint: institutional gateways, vLLM, LM Studio, Azure-style proxies, … | `RELEVANTR_API_KEY` |

After entering base URL and key, click **Fetch models** — Relevantr queries the provider's `GET /v1/models` endpoint and fills the model dropdown. If the endpoint doesn't support listing, just type the model name. **Test connection** verifies reachability and authentication.

**Environment-variable override for scripting:** a key in the provider's environment variable (last column above), or in the generic `RELEVANTR_API_KEY`, takes precedence over the stored key. A `.env` file in the working directory is also read. This lets you script Relevantr without touching the keyring.

**No key is ever required** to use Relevantr — local embeddings plus retrieval-only mode work out of the box for every user.

## 📚 Managing your library and database

### Two independent locations

- The **PDF directory** is wherever your papers live. Relevantr only reads it.
- The **database directory** holds the search index (LanceDB table + a small `manifest.json`). It defaults to your user-data folder (e.g. `~/Library/Application Support/Relevantr/index` on macOS) but can be placed anywhere — an external SSD, a network volume — via Settings or `--db-dir`. It is never created in your current working directory.

Both may be on different drives. If a location is on an external drive that isn't mounted, Relevantr shows a clear "drive not mounted" message and refuses to touch anything — it never silently creates a fresh empty index somewhere else.

### Adding new papers

Drop the PDFs into your PDF folder, then click **Update Index** (GUI) or run:

```bash
python -m relevantr update
```

The update scans the folder and compares it with the index manifest: new files are embedded, files whose content changed (detected by size/modification time and confirmed by a content hash) are re-embedded, and chunks of removed files are deleted. **Unchanged files are never re-embedded.**

### Rebuilding from scratch

**Rebuild Index** (GUI) or `python -m relevantr rebuild` re-extracts and re-embeds everything. A rebuild is **required** when:

- the **embedding backend or model** changed (vectors from different models cannot be mixed), or
- the **chunk size/overlap** settings changed, or
- the manifest is missing or corrupt.

Relevantr detects these cases itself, explains the reason, and offers the rebuild with a time estimate (number of files × the embedding rate observed on your machine). Until you confirm, the existing index keeps answering queries with its old settings.

### Moving the database to another drive

The database directory is self-contained. Copy it to the new drive, then point Settings (or `--db-dir`) at the new location — done. If you also moved your PDF folder, Relevantr asks once to re-confirm its new path and updates the manifest.

### Expected disk usage and indexing time

Ballpark figures per **100 typical journal PDFs** (~10 pages each) with the default local backend:

- **Database size**: roughly 30–60 MB (vectors + text + full-text index; measured ~7 KB per chunk, ~40 chunks per paper).
- **Indexing time**: on an Apple-Silicon Mac (Metal GPU) on the order of 5–15 minutes; on plain CPU expect several times longer. The GWDG API backend is typically faster than CPU but depends on your network.
- **One-time model downloads**: ~1.2 GB (embedding model) + ~2.3 GB (reranker).

Your first indexing run measures the real rate on your machine; subsequent rebuild estimates use it.

## ⚙️ Settings reference

| Setting | Default | Meaning |
|---|---|---|
| PDF directory | – | Folder with your papers (read-only for Relevantr) |
| Database directory | user-data dir | Where the index lives; any drive |
| Embedding backend | `local` | `local` = Qwen3-Embedding-0.6B on your machine; `gwdg` = qwen3-embedding-4b via GWDG Chat AI |
| Chunk size / overlap | 800 / 150 tokens | Splitter granularity; changing them requires a rebuild |
| Reranker | on | Cross-encoder re-scoring (BAAI/bge-reranker-v2-m3) |
| Candidates k | 30 | Passages fetched by hybrid search before reranking |
| Passages n | 8 | Passages kept for display / the LLM |
| Answer with LLM | off | Toggle in the main window; retrieval-only when off |
| AI provider | GWDG preset | Preset, base URL, model, API key (see above) |

Settings persist as JSON in your user-config directory (API keys excluded — they live in the OS keyring).

## ⌨️ CLI reference

```
python -m relevantr                 # launch the GUI
python -m relevantr index   --pdf-dir <path> [--db-dir <path>] [--backend local|gwdg]
python -m relevantr update  [--db-dir <path>] [--pdf-dir <path to re-confirm a moved library>]
python -m relevantr rebuild [--db-dir <path>]
python -m relevantr info    [--db-dir <path>]        # manifest: locations, model, counts
python -m relevantr query "<question>" [-k 30] [-n 8] [--no-rerank]
```

The CLI reads the same configuration as the GUI; command-line options override it for that invocation. `query` is retrieval-only and prints the passages with file and page.

## 🔄 Migrating from Relevantr v1

v1 stored its index in a ChromaDB `vector_db/` directory built with Google's now-retired embedding models. **v1 indexes cannot be reused** — Relevantr v2 detects a legacy directory and tells you so. Simply point v2 at the same PDF folder and build a fresh index; your PDFs are the source of truth and nothing else is needed. The old `vector_db/` directory can be deleted.

## 📦 Building standalone executables

One PyInstaller path per platform:

```bash
python build_mac.py        # macOS  → dist/Relevantr.app   (uses relevantr.spec)
python build_windows.py    # Windows → dist/Relevantr/      (uses relevantr_windows.spec)
```

Run them inside an environment where `pip install -e ".[local]"` has been done.

## 🧪 Tests

```bash
pip install -e ".[local,test]"
pytest
```

The end-to-end test that uses the real local embedding model is skipped automatically unless the model is already in your Hugging Face cache.

## RESEARCH TOOL DISCLAIMER:
This software is designed as a research tool for academic and scientific purposes. Users are responsible for:
- Verifying the accuracy of AI-generated responses
- Ensuring compliance with their institution's research policies
- Proper citation and attribution of source materials
- Understanding the limitations of AI language models

The author makes no representations about the accuracy, completeness, or suitability of the information provided by this software for any particular purpose. Users assume all risks associated with the use of this software.

EXTERNAL SERVICES DISCLAIMER:
This software can integrate with external services (e.g. GWDG Chat AI, OpenAI, Google Gemini, or any OpenAI-compatible endpoint you configure). The author is not responsible for:
- Changes to external service APIs or availability
- Costs associated with external service usage
- Data privacy practices of external services
- Content or responses generated by external AI models

Note that when an external AI provider is enabled, the retrieved passages from your PDFs are sent to that provider as context. In retrieval-only mode with local embeddings, nothing ever leaves your machine.

## 🛠️ Technical stack

- **Python 3.10+ / Tkinter** — cross-platform desktop GUI
- **PyMuPDF** — PDF text extraction
- **LanceDB** — embedded vector database with native BM25 full-text search and hybrid queries
- **sentence-transformers** — local embeddings (Qwen3-Embedding-0.6B) and cross-encoder reranking (bge-reranker-v2-m3)
- **openai** (the Python client) — one client for every OpenAI-compatible provider
- **keyring / platformdirs / python-dotenv** — safe key storage and sane file locations

## 📄 License

This project is licensed under the **Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License** — see the [LICENSE](LICENSE) file for details.

**Summary:**
- ✅ **Free for academic/research use**
- ✅ **Modifications must be shared under same license**
- ❌ **No commercial use without permission**
- 🔄 **Derivative works encouraged with attribution**

## 🙏 Acknowledgments

- **LanceDB** team for the embedded vector database
- **Qwen** and **BAAI** teams for the open embedding and reranking models
- **GWDG / KISSKI** for the Academic Cloud Chat AI service
- **Scientific community** for inspiring this tool
- **Sriram Anand** for Windows installation, testing and debugging (v1)
- Funded by the **Deutsche Forschungsgemeinschaft (DFG)** under NFDI 38/1 — project 460247524 (**NFDI-MatWerk**)

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/biterik/Relevantr/issues)
- **Discussions**: [GitHub Discussions](https://github.com/biterik/Relevantr/discussions)

---

**Created by Erik Bitzek, 2025–2026**

*Making scientific literature analysis accessible through AI* 🚀

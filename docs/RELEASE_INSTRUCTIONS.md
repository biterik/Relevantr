# Relevantr v2 — Release & installer instructions for Claude Code

Audience: Claude Code, working in `/Users/e.bitzek/DEVEL/Relevantr`.
Precondition: Erik has already merged `v2-modernization` into `main`. Work on
`main`. If the merge has not happened, stop and say so.

## Goal

A GitHub Release v2.0.0 with downloadable installers for macOS, Windows, and
Linux, built automatically by GitHub Actions — plus a CI test workflow so
future changes stay green on all three platforms.

## 1. Housekeeping first

- **Relicense to AGPL-3.0-or-later** (Erik's explicit decision, 2026-08-31,
  replacing CC BY-NC-SA 4.0; he is the sole author so no other consent is
  needed): replace `LICENSE` with the verbatim GNU AGPL v3 text; set
  `license = "AGPL-3.0-or-later"` and the matching classifier in
  `pyproject.toml`; update the `license` field in `CITATION.cff`; rewrite the
  README license section (drop all non-commercial wording; note that the
  bundled PyMuPDF is likewise AGPL). Add the standard short AGPL header
  comment to the source files' module docstrings or a NOTICE line — keep it
  lightweight.
- Create `docs/` and move `MODERNIZATION_INSTRUCTIONS.md` and this file into it;
  commit them (they document the v2 design decisions).
- Add a `build_linux.py` alongside `build_mac.py` / `build_windows.py`, or —
  preferred — consolidate all three into one `build.py` that dispatches on
  `sys.platform`, with one PyInstaller `.spec` per platform. Keep them thin.

## 2. PyInstaller specifics (all platforms)

- **CPU-only torch.** In CI (and in the specs' documented build steps) install
  torch from the CPU wheel index (`--index-url
  https://download.pytorch.org/whl/cpu`) before `pip install .[local]`, and
  exclude CUDA libs in the spec. Otherwise the bundles balloon by gigabytes.
- **Do NOT bundle model weights.** Qwen3-Embedding-0.6B and
  bge-reranker-v2-m3 download to the Hugging Face cache on first use; the app
  already handles that. State in the README that first launch needs network
  once (or that users can pre-populate the cache for offline machines).
- Use one-dir mode (not one-file) — startup speed and antivirus friendliness.
- Known PyInstaller pain points to handle in the specs: `sentence_transformers`
  / `transformers` hidden imports and data files, `lancedb`'s native lib,
  `tiktoken` data, `keyring` backends, tkinter data on Linux.
- Expect ~1.5–2.5 GB unpacked per bundle; that is acceptable, just document it.

## 3. Installer packaging per platform

- **macOS:** PyInstaller `.app` → compressed DMG via `hdiutil create` (no
  extra tooling needed). Unsigned/un-notarized is fine for now — add a README
  note that first launch needs right-click → Open (Gatekeeper), and mention
  `xattr -dr com.apple.quarantine` as fallback. Build on `macos-latest`
  (Apple Silicon). If an Intel build is cheap to add (`macos-13` runner), add
  it as a second artifact `-x86_64`; otherwise skip and note Apple-Silicon-only.
- **Windows:** PyInstaller one-dir → **Inno Setup** installer (`iscc` is
  preinstalled on `windows-latest` runners; write a minimal `.iss` script:
  install to `{autopf}\Relevantr`, Start-menu shortcut, uninstaller). Also
  upload the plain `.zip` of the one-dir as a no-install alternative. Add a
  README note about the SmartScreen "unknown publisher" warning.
- **Linux:** PyInstaller one-dir → **AppImage** (appimagetool, with a minimal
  `.desktop` file and the logo as icon), built on `ubuntu-22.04` for glibc
  compatibility. Also upload a `.tar.gz` of the one-dir. Note in the README
  that pip/pipx install from source remains the recommended path for Linux
  users.
- Name artifacts `Relevantr-2.0.0-macos-arm64.dmg`,
  `Relevantr-2.0.0-windows-x86_64-setup.exe`, `Relevantr-2.0.0-linux-x86_64.AppImage`,
  etc. Derive the version from the git tag, cross-checked against
  `pyproject.toml` (fail the build on mismatch).

## 4. GitHub Actions

Two workflows (keep `.github/workflows/repo-vitals.yml` untouched):

- **`.github/workflows/test.yml`** — on push to `main` and on PRs: pytest on
  `ubuntu-latest`, `macos-latest`, `windows-latest`, Python 3.11 and 3.12.
  Cache pip and the Hugging Face model cache
  (`~/.cache/huggingface`) keyed on the model names so the end-to-end test
  with the real local model runs without re-downloading every time; if the
  download is still too slow/flaky on a platform, mark that test to skip in CI
  there rather than letting it flap. This also finally exercises keyring and
  path handling on Windows/Linux — fix what it uncovers.
- **`.github/workflows/release.yml`** — on tags matching `v*`: three build
  jobs (one per OS) producing the artifacts of section 3, then a job that
  creates the GitHub Release with auto-generated notes plus a short
  hand-written intro (what v2 is, link to README migration note) and attaches
  all artifacts. Use `softprops/action-gh-release` or `gh release create`.

## 5. Verification & rollout order

1. Run the full local macOS build (`python build.py`) on this machine; open
   the produced `.app` from the DMG, index 2 PDFs, run a retrieval-only query.
2. Push `main`, then push a **release-candidate tag `v2.0.0-rc1`** and watch
   the release workflow (`gh run watch`). Fix until all three platform jobs
   are green and the rc release has all artifacts. Mark rc releases as
   pre-release.
3. Do not create the final `v2.0.0` tag yourself. Report back with the rc
   release URL and a checklist of what Erik should manually test (download
   DMG on his Mac; Windows/Linux artifacts as available) — he tags `v2.0.0`
   after that.
4. Delete rc pre-releases and tags once v2.0.0 is out (note this in the
   report; do it only if Erik asks).

## 6. README additions

Add a "Download & install" section at the top (per-platform: what to
download, the Gatekeeper/SmartScreen first-launch notes, first-run model
download), keeping the from-source install section for developers and Linux.
Badge for the test workflow. Update `CITATION.cff` release date when v2.0.0
is tagged.

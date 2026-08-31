"""Settings dialog: storage locations, embeddings, retrieval tuning, and the
LLM provider section (preset dropdown, base URL, model list, API key)."""

from __future__ import annotations

import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from ..config import (
    LLM_PRESETS,
    AppConfig,
    resolve_api_key,
    store_api_key,
)
from ..llm import LLMClient, check_base_url_reachable


class SettingsDialog:
    def __init__(self, parent: tk.Misc, config: AppConfig):
        self.config = config
        self.saved = False

        self.top = tk.Toplevel(parent)
        self.top.title("Relevantr Settings")
        self.top.transient(parent)
        self.top.grab_set()
        self.top.resizable(False, False)

        body = ttk.Frame(self.top, padding=10)
        body.pack(fill=tk.BOTH, expand=True)

        self._build_locations(body)
        self._build_embeddings(body)
        self._build_retrieval(body)
        self._build_llm(body)

        buttons = ttk.Frame(body)
        buttons.pack(fill=tk.X, pady=(10, 0))
        ttk.Button(buttons, text="Cancel", command=self.top.destroy).pack(side=tk.RIGHT)
        ttk.Button(buttons, text="Save", command=self._save).pack(side=tk.RIGHT, padx=6)

    # -------------------------------------------------------------- sections

    def _build_locations(self, parent):
        frame = ttk.LabelFrame(parent, text="Storage locations (independent, any drive)")
        frame.pack(fill=tk.X, pady=(0, 8))
        frame.columnconfigure(1, weight=1)

        ttk.Label(frame, text="PDF (papers) directory:").grid(
            row=0, column=0, sticky="w", padx=5, pady=3
        )
        self.pdf_dir_var = tk.StringVar(value=self.config.pdf_dir)
        ttk.Entry(frame, textvariable=self.pdf_dir_var, width=48).grid(
            row=0, column=1, sticky="we", padx=5
        )
        ttk.Button(
            frame, text="Choose...", command=lambda: self._pick_dir(self.pdf_dir_var)
        ).grid(row=0, column=2, padx=5)

        ttk.Label(frame, text="Database directory:").grid(
            row=1, column=0, sticky="w", padx=5, pady=3
        )
        self.db_dir_var = tk.StringVar(value=self.config.db_dir)
        ttk.Entry(frame, textvariable=self.db_dir_var, width=48).grid(
            row=1, column=1, sticky="we", padx=5
        )
        ttk.Button(
            frame, text="Choose...", command=lambda: self._pick_dir(self.db_dir_var)
        ).grid(row=1, column=2, padx=5)

    def _build_embeddings(self, parent):
        frame = ttk.LabelFrame(parent, text="Embeddings and chunking")
        frame.pack(fill=tk.X, pady=(0, 8))

        ttk.Label(frame, text="Embedding backend:").grid(
            row=0, column=0, sticky="w", padx=5, pady=3
        )
        self.backend_var = tk.StringVar(value=self.config.embedding_backend)
        backend_box = ttk.Combobox(
            frame,
            textvariable=self.backend_var,
            state="readonly",
            width=42,
            values=[
                "local  (Qwen3-Embedding-0.6B on this machine, offline)",
                "gwdg  (qwen3-embedding-4b via GWDG Chat AI, needs GWDG_API_KEY)",
            ],
        )
        backend_box.grid(row=0, column=1, columnspan=3, sticky="w", padx=5)
        backend_box.set(
            backend_box["values"][0 if self.config.embedding_backend == "local" else 1]
        )
        self._backend_box = backend_box

        ttk.Label(frame, text="Chunk size (tokens):").grid(
            row=1, column=0, sticky="w", padx=5, pady=3
        )
        self.chunk_size_var = tk.IntVar(value=self.config.chunk_size)
        ttk.Entry(frame, textvariable=self.chunk_size_var, width=8).grid(
            row=1, column=1, sticky="w", padx=5
        )
        ttk.Label(frame, text="Chunk overlap (tokens):").grid(
            row=1, column=2, sticky="w", padx=5
        )
        self.chunk_overlap_var = tk.IntVar(value=self.config.chunk_overlap)
        ttk.Entry(frame, textvariable=self.chunk_overlap_var, width=8).grid(
            row=1, column=3, sticky="w", padx=5
        )
        ttk.Label(
            frame,
            text="Changing backend or chunk settings requires rebuilding the index.",
            foreground="#777",
        ).grid(row=2, column=0, columnspan=4, sticky="w", padx=5, pady=(2, 3))

    def _build_retrieval(self, parent):
        frame = ttk.LabelFrame(parent, text="Retrieval")
        frame.pack(fill=tk.X, pady=(0, 8))

        self.rerank_var = tk.BooleanVar(value=self.config.use_reranker)
        ttk.Checkbutton(
            frame,
            text="Rerank candidates with a local cross-encoder (BAAI/bge-reranker-v2-m3)",
            variable=self.rerank_var,
        ).grid(row=0, column=0, columnspan=4, sticky="w", padx=5, pady=3)

        ttk.Label(frame, text="Candidates to retrieve (k):").grid(
            row=1, column=0, sticky="w", padx=5, pady=3
        )
        self.retrieve_k_var = tk.IntVar(value=self.config.retrieve_k)
        ttk.Entry(frame, textvariable=self.retrieve_k_var, width=8).grid(
            row=1, column=1, sticky="w", padx=5
        )
        ttk.Label(frame, text="Passages to keep (n):").grid(
            row=1, column=2, sticky="w", padx=5
        )
        self.final_n_var = tk.IntVar(value=self.config.final_n)
        ttk.Entry(frame, textvariable=self.final_n_var, width=8).grid(
            row=1, column=3, sticky="w", padx=5
        )

    def _build_llm(self, parent):
        frame = ttk.LabelFrame(parent, text="AI provider (for 'Answer with LLM')")
        frame.pack(fill=tk.X)
        frame.columnconfigure(1, weight=1)

        ttk.Label(frame, text="Provider preset:").grid(
            row=0, column=0, sticky="w", padx=5, pady=3
        )
        self._preset_ids = list(LLM_PRESETS)
        labels = [LLM_PRESETS[p].label for p in self._preset_ids]
        self.preset_var = tk.StringVar()
        preset_box = ttk.Combobox(
            frame, textvariable=self.preset_var, state="readonly", values=labels, width=40
        )
        preset_box.grid(row=0, column=1, columnspan=2, sticky="w", padx=5)
        current = self.config.llm_provider if self.config.llm_provider in LLM_PRESETS else "custom"
        preset_box.set(LLM_PRESETS[current].label)
        preset_box.bind("<<ComboboxSelected>>", self._on_preset_change)

        self.note_var = tk.StringVar(value=LLM_PRESETS[current].note)
        ttk.Label(frame, textvariable=self.note_var, foreground="#777").grid(
            row=1, column=1, columnspan=2, sticky="w", padx=5
        )

        ttk.Label(frame, text="Base URL:").grid(row=2, column=0, sticky="w", padx=5, pady=3)
        self.base_url_var = tk.StringVar(value=self.config.llm_base_url)
        ttk.Entry(frame, textvariable=self.base_url_var, width=52).grid(
            row=2, column=1, columnspan=2, sticky="we", padx=5
        )

        ttk.Label(frame, text="Model:").grid(row=3, column=0, sticky="w", padx=5, pady=3)
        self.model_var = tk.StringVar(value=self.config.llm_model)
        self.model_box = ttk.Combobox(frame, textvariable=self.model_var, width=40)
        self.model_box.grid(row=3, column=1, sticky="w", padx=5)
        ttk.Button(frame, text="Fetch models", command=self._fetch_models).grid(
            row=3, column=2, sticky="w", padx=5
        )

        ttk.Label(frame, text="API key:").grid(row=4, column=0, sticky="w", padx=5, pady=3)
        self.api_key_var = tk.StringVar()
        ttk.Entry(frame, textvariable=self.api_key_var, width=42, show="*").grid(
            row=4, column=1, sticky="w", padx=5
        )
        ttk.Button(frame, text="Test connection", command=self._test_connection).grid(
            row=4, column=2, sticky="w", padx=5
        )

        _key, source = resolve_api_key(current)
        self.key_status_var = tk.StringVar(
            value=f"Current key: {source}. Keys are stored in the OS keyring, "
            "never in config files."
        )
        ttk.Label(frame, textvariable=self.key_status_var, foreground="#777",
                  wraplength=520, justify=tk.LEFT).grid(
            row=5, column=0, columnspan=3, sticky="w", padx=5, pady=(2, 4)
        )

    # --------------------------------------------------------------- actions

    def _pick_dir(self, var: tk.StringVar):
        chosen = filedialog.askdirectory(
            title="Choose directory", initialdir=var.get() or None, parent=self.top
        )
        if chosen:
            var.set(chosen)

    def _selected_preset_id(self) -> str:
        label = self.preset_var.get()
        for pid in self._preset_ids:
            if LLM_PRESETS[pid].label == label:
                return pid
        return "custom"

    def _on_preset_change(self, _event=None):
        preset = LLM_PRESETS[self._selected_preset_id()]
        self.base_url_var.set(preset.base_url)
        self.model_var.set(preset.default_model)
        self.model_box["values"] = []
        self.note_var.set(preset.note)
        _key, source = resolve_api_key(preset.id)
        self.key_status_var.set(f"Current key: {source}.")

    def _current_client(self) -> LLMClient:
        pid = self._selected_preset_id()
        key = self.api_key_var.get().strip() or resolve_api_key(pid)[0]
        return LLMClient(
            base_url=self.base_url_var.get().strip(),
            api_key=key,
            model=self.model_var.get().strip(),
        )

    def _fetch_models(self):
        base_url = self.base_url_var.get().strip()
        if not base_url:
            messagebox.showerror("Fetch models", "Enter a base URL first.", parent=self.top)
            return

        def work():
            try:
                models = self._current_client().list_models()
                error = None
            except Exception as exc:  # noqa: BLE001
                models, error = None, exc
            self.top.after(0, lambda: done(models, error))

        def done(models, error):
            if error or not models:
                messagebox.showwarning(
                    "Fetch models",
                    "Could not list models from this endpoint - type the model "
                    f"name manually.\n\n({error})",
                    parent=self.top,
                )
                return
            self.model_box["values"] = models
            if self.model_var.get() not in models:
                self.model_var.set(models[0])
            messagebox.showinfo(
                "Fetch models", f"Loaded {len(models)} models.", parent=self.top
            )

        threading.Thread(target=work, daemon=True).start()

    def _test_connection(self):
        base_url = self.base_url_var.get().strip()
        if not base_url:
            messagebox.showerror("Test connection", "Enter a base URL first.", parent=self.top)
            return

        def work():
            reachable, net_msg = check_base_url_reachable(base_url)
            if not reachable:
                self.top.after(0, lambda: messagebox.showerror(
                    "Test connection", net_msg, parent=self.top))
                return
            ok, msg = self._current_client().test_connection()
            show = messagebox.showinfo if ok else messagebox.showerror
            self.top.after(0, lambda: show("Test connection", msg, parent=self.top))

        threading.Thread(target=work, daemon=True).start()

    def _save(self):
        try:
            chunk_size = self.chunk_size_var.get()
            chunk_overlap = self.chunk_overlap_var.get()
            retrieve_k = self.retrieve_k_var.get()
            final_n = self.final_n_var.get()
        except tk.TclError:
            messagebox.showerror("Settings", "Numeric fields must contain numbers.",
                                 parent=self.top)
            return
        if chunk_overlap >= chunk_size:
            messagebox.showerror("Settings", "Chunk overlap must be smaller than "
                                 "chunk size.", parent=self.top)
            return

        cfg = self.config
        cfg.pdf_dir = self.pdf_dir_var.get().strip()
        cfg.db_dir = self.db_dir_var.get().strip()
        cfg.embedding_backend = "gwdg" if self._backend_box.get().startswith("gwdg") else "local"
        cfg.chunk_size = chunk_size
        cfg.chunk_overlap = chunk_overlap
        cfg.use_reranker = self.rerank_var.get()
        cfg.retrieve_k = retrieve_k
        cfg.final_n = final_n
        cfg.llm_provider = self._selected_preset_id()
        cfg.llm_base_url = self.base_url_var.get().strip()
        cfg.llm_model = self.model_var.get().strip()

        new_key = self.api_key_var.get().strip()
        if new_key:
            note = store_api_key(cfg.llm_provider, new_key)
            messagebox.showinfo("API key", note, parent=self.top)

        self.saved = True
        self.top.destroy()

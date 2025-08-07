#!/usr/bin/env python3
"""
Relevantr - A Scientific PDF RAG Application
============================================
A comprehensive RAG (Retrieval-Augmented Generation) application for scientific literature analysis.
Extracts information from PDF documents and provides AI-powered answers using Google's Gemini.

Created by: Erik Bitzek
Date: August 2025
"""

import os
import sys
import json
import logging
import threading
import traceback
from pathlib import Path
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from datetime import datetime

# PyInstaller compatibility
if hasattr(sys, '_MEIPASS'):
    # Running as PyInstaller bundle
    BASE_DIR = sys._MEIPASS
else:
    # Running as normal Python script
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import google.generativeai as genai
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyMuPDFLoader
from langchain_community.vectorstores import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from tqdm import tqdm
import warnings
from dotenv import load_dotenv

warnings.filterwarnings("ignore", category=UserWarning)

@dataclass
class Config:
    """Application configuration"""
    pdf_directory: str = os.path.join(os.getcwd(), "pdfs")  # User's current directory
    persist_directory: str = os.path.join(os.getcwd(), "vector_db")  # User's current directory
    embedding_model: str = "models/text-embedding-004"
    generation_model: str = "gemini-1.5-flash"  # Free tier model
    chunk_size: int = 1000
    chunk_overlap: int = 200
    max_retrieved_docs: int = 7
    window_width: int = 1200
    window_height: int = 800

class Logger:
    """Enhanced logging system"""
    
    def __init__(self):
        # Create logs directory in the current working directory (user's folder)
        self.log_dir = os.path.join(os.getcwd(), "logs")
        os.makedirs(self.log_dir, exist_ok=True)
        
        # Configure logging
        log_file = os.path.join(self.log_dir, f'relevantr_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def info(self, message: str):
        self.logger.info(message)
    
    def error(self, message: str):
        self.logger.error(message)
    
    def warning(self, message: str):
        self.logger.warning(message)

class DocumentProcessor:
    """Handles PDF processing and vector database operations"""
    
    def __init__(self, config: Config, logger: Logger):
        self.config = config
        self.logger = logger
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=config.chunk_size,
            chunk_overlap=config.chunk_overlap,
            length_function=len,
            is_separator_regex=False,
        )
        self.embeddings = None
        self.vector_db = None
    
    def initialize_embeddings(self, api_key: str):
        """Initialize Google embeddings"""
        try:
            # Configure genai with API key first
            genai.configure(api_key=api_key)
            
            # Initialize embeddings with explicit API key
            self.embeddings = GoogleGenerativeAIEmbeddings(
                model=self.config.embedding_model,
                google_api_key=api_key  # Explicitly pass the API key
            )
            
            # Test the embeddings with a simple query
            test_embedding = self.embeddings.embed_query("test")
            
            self.logger.info("Embeddings initialized successfully")
            return True
        except Exception as e:
            self.logger.error(f"Failed to initialize embeddings: {e}")
            
            # Try alternative embedding models for compatibility
            alternative_models = ["models/embedding-001", "models/text-embedding-004"]
            
            for alt_model in alternative_models:
                if alt_model == self.config.embedding_model:
                    continue
                    
                try:
                    self.logger.info(f"Trying alternative embedding model: {alt_model}")
                    self.embeddings = GoogleGenerativeAIEmbeddings(
                        model=alt_model,
                        google_api_key=api_key
                    )
                    
                    # Test the alternative model
                    test_embedding = self.embeddings.embed_query("test")
                    
                    self.logger.info(f"Embeddings initialized with alternative model: {alt_model}")
                    self.config.embedding_model = alt_model
                    return True
                    
                except Exception as alt_error:
                    self.logger.error(f"Alternative embedding model {alt_model} failed: {alt_error}")
                    continue
            
            return False
    
    def load_and_process_pdfs(self, pdf_directory: str, progress_callback=None) -> List[Any]:
        """Load and process PDF files with progress tracking"""
        documents = []
        
        if not os.path.exists(pdf_directory):
            raise FileNotFoundError(f"PDF directory '{pdf_directory}' not found")
        
        pdf_files = [f for f in os.listdir(pdf_directory) if f.endswith(".pdf")]
        if not pdf_files:
            raise ValueError(f"No PDF files found in '{pdf_directory}'")
        
        self.logger.info(f"Found {len(pdf_files)} PDF files to process")
        problematic_files = []
        
        for i, pdf_file in enumerate(pdf_files):
            if progress_callback:
                progress_callback(i, len(pdf_files), f"Processing {pdf_file}")
            
            pdf_path = os.path.join(pdf_directory, pdf_file)
            try:
                loader = PyMuPDFLoader(pdf_path)
                pages_from_pdf = loader.load_and_split(text_splitter=self.text_splitter)
                
                for page in pages_from_pdf:
                    page.metadata["source"] = pdf_file
                    page.metadata['page_number'] = page.metadata.get('page', 'Unknown')
                
                documents.extend(pages_from_pdf)
                self.logger.info(f"Successfully processed {pdf_file} - {len(pages_from_pdf)} chunks")
                
            except Exception as e:
                self.logger.error(f"Failed to process {pdf_file}: {e}")
                problematic_files.append(pdf_file)
        
        if progress_callback:
            progress_callback(len(pdf_files), len(pdf_files), "Processing complete")
        
        self.logger.info(f"Total chunks created: {len(documents)}")
        if problematic_files:
            self.logger.warning(f"Could not process {len(problematic_files)} files: {problematic_files}")
        
        return documents
    
    def create_vector_database(self, documents: List[Any], progress_callback=None) -> bool:
        """Create or update vector database"""
        try:
            if progress_callback:
                progress_callback(0, 1, "Creating vector database...")
            
            # Create directory if it doesn't exist
            os.makedirs(self.config.persist_directory, exist_ok=True)
            
            self.vector_db = Chroma.from_documents(
                documents=documents,
                embedding=self.embeddings,
                persist_directory=self.config.persist_directory
            )
            
            # Note: ChromaDB 0.4.x auto-persists, no need to call persist()
            
            if progress_callback:
                progress_callback(1, 1, "Vector database created successfully")
            
            self.logger.info(f"Vector database created with {len(documents)} documents")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to create vector database: {e}")
            return False
    
    def load_existing_database(self) -> bool:
        """Load existing vector database"""
        try:
            if os.path.exists(self.config.persist_directory) and os.listdir(self.config.persist_directory):
                self.vector_db = Chroma(
                    persist_directory=self.config.persist_directory,
                    embedding_function=self.embeddings
                )
                self.logger.info("Existing vector database loaded successfully")
                return True
            return False
        except Exception as e:
            self.logger.error(f"Failed to load existing database: {e}")
            return False
    
    def get_database_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        if not self.vector_db:
            return {"status": "not_initialized", "count": 0}
        
        try:
            count = self.vector_db._collection.count()
            return {"status": "ready", "count": count}
        except:
            return {"status": "error", "count": 0}

class QueryProcessor:
    """Handles query processing and response generation"""
    
    def __init__(self, config: Config, logger: Logger):
        self.config = config
        self.logger = logger
        self.llm = None
    
    def initialize_llm(self, api_key: str):
        """Initialize Gemini LLM with automatic model detection"""
        try:
            # Configure the API first
            genai.configure(api_key=api_key)
            
            # Test models in order of preference (best to fallback)
            model_preference = [
                ("gemini-1.5-pro", "Premium model (paid tier)"),
                ("gemini-1.5-flash", "Fast model (free tier)"),
                ("gemini-pro", "Legacy model (deprecated)")
            ]
            
            self.logger.info("Testing available models...")
            
            for model_name, description in model_preference:
                try:
                    self.logger.info(f"Testing {model_name} - {description}")
                    
                    # Test with ChatGoogleGenerativeAI and explicit API key
                    test_llm = ChatGoogleGenerativeAI(
                        model=model_name,
                        google_api_key=api_key  # Explicitly pass API key
                    )
                    test_response = test_llm.invoke("Hello")
                    
                    # If we get here, the model works
                    self.llm = test_llm
                    self.config.generation_model = model_name
                    
                    if "pro" in model_name and "flash" not in model_name:
                        self.logger.info(f"✅ SUCCESS: Using premium model {model_name} - You have Pro access!")
                    else:
                        self.logger.info(f"✅ SUCCESS: Using {model_name} - {description}")
                    
                    return True
                    
                except Exception as model_error:
                    error_msg = str(model_error).lower()
                    
                    if "quota exceeded" in error_msg:
                        self.logger.warning(f"❌ {model_name} quota exceeded - trying next model")
                    elif "permission denied" in error_msg or "not found" in error_msg:
                        self.logger.info(f"❌ {model_name} not available (likely requires paid tier)")
                    else:
                        self.logger.warning(f"❌ {model_name} failed: {model_error}")
                    
                    continue
            
            self.logger.error("❌ No working models found. Check your API key and internet connection.")
            return False
            
        except Exception as e:
            self.logger.error(f"Failed to initialize LLM: {e}")
            return False
    
    def process_query(self, query: str, vector_db: Any) -> Dict[str, Any]:
        """Process user query and generate response"""
        try:
            # Retrieve relevant documents
            retrieved_docs = vector_db.similarity_search(query, k=self.config.max_retrieved_docs)
            self.logger.info(f"Retrieved {len(retrieved_docs)} relevant documents for query")
            
            # Prepare context
            structured_context = []
            unique_sources = set()
            
            for i, doc in enumerate(retrieved_docs):
                source_file = doc.metadata.get('source', 'Unknown Source')
                page_num = doc.metadata.get('page_number', doc.metadata.get('page', 'Unknown'))
                
                context_id = f"CONTEXT_ITEM_{i+1}"
                display_source = f"{source_file}"
                if page_num != 'Unknown':
                    display_source += f" (Page: {page_num})"
                
                structured_context.append(
                    f"--- START {context_id}: Source File: {display_source} ---\n"
                    f"{doc.page_content}\n"
                    f"--- END {context_id} ---"
                )
                unique_sources.add(display_source)
            
            context_for_llm = "\n\n".join(structured_context)
            source_list = "Full Source References:\n" + "\n".join(sorted(list(unique_sources)))
            
            # Generate response
            prompt = self._create_prompt(query, context_for_llm, source_list)
            response = self.llm.invoke(prompt)
            
            return {
                "success": True,
                "answer": response.content,
                "sources": list(unique_sources),
                "retrieved_docs": retrieved_docs,  # Include full document objects
                "context": context_for_llm,
                "num_sources": len(retrieved_docs)
            }
            
        except Exception as e:
            self.logger.error(f"Query processing failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "answer": "Sorry, I couldn't process your query at this time."
            }
    
    def _create_prompt(self, query: str, context: str, sources: str) -> str:
        """Create enhanced prompt for Gemini"""
        return f"""
You are an AI assistant specialized in scientific document analysis. Your task is to answer the user's question STRICTLY by referencing the provided document excerpts.

**CRITICAL INSTRUCTIONS:**
1. For EVERY piece of information you provide, you MUST identify its source
2. Format your answer with explicit source attribution
3. Include direct quotes or very close paraphrases from the source material
4. If information is not present in the provided context, clearly state that

**Desired Format:**
Start with a brief overview, then for each specific point:
- State the source: "According to [filename] (Page: X)..."
- Include the relevant information: "The document states: '[quote or paraphrase]'"
- Continue with additional sources as needed

**Context Information:**
{context}

---
**User Question:** {query}

Please provide a comprehensive, well-attributed answer based ONLY on the provided context.

{sources}
"""

class ScientificRAGApp:
    """Main Relevantr GUI application"""
    
    def __init__(self):
        self.config = Config()
        self.logger = Logger()
        self.processor = DocumentProcessor(self.config, self.logger)
        self.query_processor = QueryProcessor(self.config, self.logger)
        
        self.root = tk.Tk()
        self.api_key = None
        self.is_processing = False
        
        # Initialize variables for export functionality
        self._last_query_result = None
        self._last_query = None
        
        self.setup_gui()
    
    def setup_gui(self):
        """Setup the main GUI"""
        self.root.title("Relevantr - Scientific PDF RAG Application")
        self.root.geometry(f"{self.config.window_width}x{self.config.window_height}")
        self.root.minsize(800, 600)
        
        # Create main frames
        self.create_menu()
        self.create_toolbar()
        self.create_main_frames()
        self.create_status_bar()
        
        # Initialize with API key prompt
        self.root.after(100, self.prompt_api_key)
    
    def create_menu(self):
        """Create application menu"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Set PDF Directory", command=self.select_pdf_directory)
        file_menu.add_command(label="Reset Database", command=self.reset_database)
        file_menu.add_separator()
        file_menu.add_command(label="Export Results", command=self.export_results)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        
        # Settings menu
        settings_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Settings", menu=settings_menu)
        settings_menu.add_command(label="Configure API Key", command=self.configure_api_key)
        settings_menu.add_command(label="Advanced Settings", command=self.show_advanced_settings)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="Debug: Force Enable Query", command=self.force_enable_query)
        help_menu.add_separator()
        help_menu.add_command(label="About", command=self.show_about)
    
    def create_toolbar(self):
        """Create toolbar with action buttons"""
        self.toolbar = ttk.Frame(self.root)
        self.toolbar.pack(fill=tk.X, padx=5, pady=2)
        
        # PDF Directory selection
        ttk.Label(self.toolbar, text="PDF Directory:").pack(side=tk.LEFT, padx=5)
        self.pdf_dir_var = tk.StringVar(value=self.config.pdf_directory)
        self.pdf_dir_entry = ttk.Entry(self.toolbar, textvariable=self.pdf_dir_var, width=40)
        self.pdf_dir_entry.pack(side=tk.LEFT, padx=5)
        ttk.Button(self.toolbar, text="Browse", command=self.select_pdf_directory).pack(side=tk.LEFT)
        
        # Process button
        self.process_btn = ttk.Button(self.toolbar, text="Process PDFs", command=self.process_pdfs)
        self.process_btn.pack(side=tk.RIGHT, padx=5)
        
        # Database status
        self.db_status_var = tk.StringVar(value="Database: Not Ready")
        ttk.Label(self.toolbar, textvariable=self.db_status_var).pack(side=tk.RIGHT, padx=10)
    
    def create_main_frames(self):
        """Create main application frames"""
        # Main container
        main_container = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        main_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Left panel - Query and Results
        left_frame = ttk.Frame(main_container)
        main_container.add(left_frame, weight=2)
        
        # Query section
        query_frame = ttk.LabelFrame(left_frame, text="Ask a Question")
        query_frame.pack(fill=tk.X, pady=(0, 5))
        
        self.query_text = scrolledtext.ScrolledText(query_frame, height=3, wrap=tk.WORD, font=("Arial", 12))
        self.query_text.pack(fill=tk.X, padx=5, pady=5)
        
        query_btn_frame = ttk.Frame(query_frame)
        query_btn_frame.pack(fill=tk.X, padx=5, pady=(0, 5))
        
        self.ask_btn = ttk.Button(query_btn_frame, text="Ask Question", command=self.process_query)
        self.ask_btn.pack(side=tk.LEFT)
        ttk.Button(query_btn_frame, text="Clear", command=self.clear_query).pack(side=tk.LEFT, padx=5)
        
        # Results section
        results_frame = ttk.LabelFrame(left_frame, text="Answer")
        results_frame.pack(fill=tk.BOTH, expand=True)
        
        self.results_text = scrolledtext.ScrolledText(results_frame, wrap=tk.WORD, font=("Arial", 12))
        self.results_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Right panel - Sources and Logs
        right_frame = ttk.Frame(main_container)
        main_container.add(right_frame, weight=1)
        
        # Sources section
        sources_frame = ttk.LabelFrame(right_frame, text="Sources")
        sources_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 5))
        
        # Sources tree with scrollbar
        sources_container = ttk.Frame(sources_frame)
        sources_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.sources_tree = ttk.Treeview(sources_container, columns=("File", "Page"), show="tree headings", height=8)
        self.sources_tree.heading("#0", text="Passage")
        self.sources_tree.heading("File", text="File")
        self.sources_tree.heading("Page", text="Page")
        
        # Configure column widths
        self.sources_tree.column("#0", width=100)
        self.sources_tree.column("File", width=200)
        self.sources_tree.column("Page", width=60)
        
        # Add scrollbar for sources tree
        sources_scrollbar = ttk.Scrollbar(sources_container, orient=tk.VERTICAL, command=self.sources_tree.yview)
        self.sources_tree.configure(yscrollcommand=sources_scrollbar.set)
        
        self.sources_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sources_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Bind double-click event to show source content
        self.sources_tree.bind("<Double-1>", self.show_source_content)
        
        # Source content display
        content_frame = ttk.LabelFrame(right_frame, text="Source Content (Double-click source to view)")
        content_frame.pack(fill=tk.BOTH, expand=True, pady=(5, 0))
        
        self.source_content_text = scrolledtext.ScrolledText(content_frame, wrap=tk.WORD, font=("Arial", 11), height=10)
        self.source_content_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Progress and logs
        progress_frame = ttk.LabelFrame(right_frame, text="Progress")
        progress_frame.pack(fill=tk.X, pady=(0, 5))
        
        self.progress_var = tk.StringVar(value="Ready")
        ttk.Label(progress_frame, textvariable=self.progress_var).pack(padx=5, pady=2)
        
        self.progress_bar = ttk.Progressbar(progress_frame, mode='determinate')
        self.progress_bar.pack(fill=tk.X, padx=5, pady=(0, 5))
    
    def create_status_bar(self):
        """Create status bar"""
        self.status_bar = ttk.Frame(self.root)
        self.status_bar.pack(fill=tk.X, side=tk.BOTTOM)
        
        self.status_var = tk.StringVar(value="Ready - Please set your Google API key")
        ttk.Label(self.status_bar, textvariable=self.status_var).pack(side=tk.LEFT, padx=5, pady=2)
        
        # API status indicator
        self.api_status_var = tk.StringVar(value="API: Not Configured")
        ttk.Label(self.status_bar, textvariable=self.api_status_var).pack(side=tk.RIGHT, padx=5, pady=2)
        
        # Model status indicator
        self.model_status_var = tk.StringVar(value="")
        self.model_status_label = ttk.Label(self.status_bar, textvariable=self.model_status_var, font=("Arial", 8))
        self.model_status_label.pack(side=tk.RIGHT, padx=5, pady=2)
    
    def prompt_api_key(self):
        """Prompt user for Google API key"""
        # Try to load from .env first (check current working directory)
        env_path = os.path.join(os.getcwd(), '.env')
        if os.path.exists(env_path):
            load_dotenv(env_path)
        else:
            load_dotenv()  # Try default locations
            
        api_key = os.getenv("GOOGLE_API_KEY")
        
        if not api_key:
            api_key = self.get_api_key_from_user()
        
        if api_key:
            self.set_api_key(api_key)
        else:
            messagebox.showwarning("API Key Required", 
                                 "Google API key is required to use this application. "
                                 "Please configure it in Settings menu.")
    
    def get_api_key_from_user(self):
        """Get API key from user input"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Google API Key Required")
        dialog.geometry("400x200")
        dialog.transient(self.root)
        dialog.grab_set()
        
        ttk.Label(dialog, text="Please enter your Google Gemini API key:").pack(pady=10)
        
        api_key_var = tk.StringVar()
        entry = ttk.Entry(dialog, textvariable=api_key_var, width=50, show="*")
        entry.pack(pady=5)
        entry.focus()
        
        result = {"api_key": None}
        
        def on_ok():
            result["api_key"] = api_key_var.get().strip()
            dialog.destroy()
        
        def on_cancel():
            dialog.destroy()
        
        ttk.Button(dialog, text="OK", command=on_ok).pack(side=tk.LEFT, padx=20, pady=20)
        ttk.Button(dialog, text="Cancel", command=on_cancel).pack(side=tk.RIGHT, padx=20, pady=20)
        
        dialog.wait_window()
        return result["api_key"]
    
    def set_api_key(self, api_key: str):
        """Set and validate API key"""
        self.api_key = api_key
        
        # Initialize components
        embeddings_ok = self.processor.initialize_embeddings(api_key)
        llm_ok = self.query_processor.initialize_llm(api_key)
        
        if embeddings_ok and llm_ok:
            self.api_status_var.set("API: Connected")
            
            # Show which model is being used
            model_name = self.config.generation_model
            if "pro" in model_name and "flash" not in model_name:
                self.model_status_var.set(f"Model: {model_name} (Premium)")
                self.status_var.set("Ready - Using premium model with Pro access!")
            else:
                self.model_status_var.set(f"Model: {model_name}")
                self.status_var.set("Ready - API configured successfully")
            
            # Try to load existing database
            if self.processor.load_existing_database():
                self.update_database_status()
                # Force enable query interface
                self.ask_btn.config(state='normal')
                self.query_text.config(state='normal')
            else:
                self.status_var.set("Ready - Please process PDFs to create database")
        else:
            self.api_status_var.set("API: Error")
            self.model_status_var.set("")
            self.status_var.set("Error - Failed to configure API")
            messagebox.showerror("API Error", "Failed to configure Google API. Please check your API key.")
    
    def select_pdf_directory(self):
        """Select PDF directory"""
        directory = filedialog.askdirectory(title="Select PDF Directory")
        if directory:
            self.pdf_dir_var.set(directory)
            self.config.pdf_directory = directory
    
    def process_pdfs(self):
        """Process PDFs in a separate thread"""
        if self.is_processing:
            return
        
        if not self.api_key:
            messagebox.showerror("Error", "Please configure your Google API key first.")
            return
        
        pdf_directory = self.pdf_dir_var.get().strip()
        if not pdf_directory:
            messagebox.showerror("Error", "Please select a PDF directory.")
            return
        
        self.is_processing = True
        self.process_btn.config(state='disabled')
        
        def progress_callback(current, total, message):
            self.root.after(0, lambda: self.update_progress(current, total, message))
        
        def process_thread():
            try:
                # Process PDFs
                documents = self.processor.load_and_process_pdfs(pdf_directory, progress_callback)
                
                if documents:
                    # Create database
                    success = self.processor.create_vector_database(documents, progress_callback)
                    
                    self.root.after(0, lambda: self.on_processing_complete(success, len(documents)))
                else:
                    self.root.after(0, lambda: self.on_processing_error("No documents were processed"))
                    
            except Exception as e:
                self.root.after(0, lambda: self.on_processing_error(str(e)))
        
        threading.Thread(target=process_thread, daemon=True).start()
    
    def update_progress(self, current: int, total: int, message: str):
        """Update progress bar and message"""
        if total > 0:
            progress_percent = (current / total) * 100
            self.progress_bar['value'] = progress_percent
        
        self.progress_var.set(message)
        self.root.update_idletasks()
    
    def on_processing_complete(self, success: bool, doc_count: int):
        """Handle processing completion"""
        self.is_processing = False
        self.process_btn.config(state='normal')
        
        if success:
            # Force update database status to enable query interface
            self.update_database_status()
            self.progress_var.set(f"Complete - Processed {doc_count} document chunks")
            self.status_var.set("Ready - Database updated successfully")
            
            # Force enable query interface as backup
            self.ask_btn.config(state='normal')
            self.query_text.config(state='normal')
            
            messagebox.showinfo("Success", f"Successfully processed PDFs and created database with {doc_count} chunks.\n\nYou can now ask questions!")
        else:
            self.progress_var.set("Error - Processing failed")
            self.status_var.set("Error - Database creation failed")
            messagebox.showerror("Error", "Failed to create vector database.")
        
        self.progress_bar['value'] = 0
    
    def on_processing_error(self, error_message: str):
        """Handle processing error"""
        self.is_processing = False
        self.process_btn.config(state='normal')
        self.progress_var.set("Error - Processing failed")
        self.status_var.set("Error - Processing failed")
        self.progress_bar['value'] = 0
        messagebox.showerror("Processing Error", f"Failed to process PDFs:\n{error_message}")
    
    def update_database_status(self):
        """Update database status display"""
        stats = self.processor.get_database_stats()
        self.logger.info(f"Database status check: {stats}")
        
        if stats["status"] == "ready":
            self.db_status_var.set(f"Database: Ready ({stats['count']} chunks)")
            self.ask_btn.config(state='normal')
            self.query_text.config(state='normal')
            self.logger.info("Query interface enabled - database ready")
        else:
            self.db_status_var.set("Database: Not Ready")
            self.ask_btn.config(state='disabled')
            self.query_text.config(state='disabled')
            self.logger.warning(f"Query interface disabled - database status: {stats['status']}")
    
    def process_query(self):
        """Process user query"""
        query = self.query_text.get(1.0, tk.END).strip()
        if not query:
            messagebox.showwarning("Warning", "Please enter a question.")
            return
        
        if not self.processor.vector_db:
            messagebox.showerror("Error", "Database not ready. Please process PDFs first.")
            return
        
        self.ask_btn.config(state='disabled')
        self.results_text.delete(1.0, tk.END)
        self.clear_sources()
        
        self.results_text.insert(tk.END, "Processing your question...\n")
        self.root.update_idletasks()
        
        def query_thread():
            result = self.query_processor.process_query(query, self.processor.vector_db)
            self.root.after(0, lambda: self.display_results(result))
        
        threading.Thread(target=query_thread, daemon=True).start()
    
    def display_results(self, result: Dict[str, Any]):
        """Display query results"""
        self.results_text.delete(1.0, tk.END)
        
        # Store result for export and source display
        self._last_query_result = result
        self._last_query = self.query_text.get(1.0, tk.END).strip()
        
        if result["success"]:
            # Display answer
            self.results_text.insert(tk.END, result["answer"])
            
            # Display sources with individual passages
            if "retrieved_docs" in result:
                self.display_sources_detailed(result["retrieved_docs"])
            elif "sources" in result:
                # Fallback for old format
                self.display_sources(result["sources"])
            
            self.status_var.set(f"Query complete - Found {result.get('num_sources', 0)} relevant sources")
        else:
            self.results_text.insert(tk.END, f"Error: {result.get('error', 'Unknown error')}")
            self.status_var.set("Query failed")
        
        self.ask_btn.config(state='normal')
    
    def display_sources_detailed(self, retrieved_docs: List[Any]):
        """Display sources with individual text passages"""
        self.clear_sources()
        
        for i, doc in enumerate(retrieved_docs):
            source_file = doc.metadata.get('source', 'Unknown Source')
            page_num = doc.metadata.get('page_number', doc.metadata.get('page', 'Unknown'))
            
            # Create a unique identifier for each passage
            passage_id = f"Passage {i+1}"
            
            # Insert individual source entry
            item_id = self.sources_tree.insert("", tk.END, 
                                              text=passage_id, 
                                              values=(source_file, page_num),
                                              tags=(str(i),))  # Store index as tag for retrieval
        
        # Clear source content display
        self.source_content_text.delete(1.0, tk.END)
        self.source_content_text.insert(tk.END, "Double-click on a source above to view its content...")
    
    def show_source_content(self, event):
        """Show the content of the selected source passage"""
        selection = self.sources_tree.selection()
        if not selection:
            return
        
        item = selection[0]
        tags = self.sources_tree.item(item, "tags")
        
        if not tags or not self._last_query_result:
            return
        
        try:
            doc_index = int(tags[0])
            retrieved_docs = self._last_query_result.get("retrieved_docs", [])
            
            if doc_index < len(retrieved_docs):
                doc = retrieved_docs[doc_index]
                source_file = doc.metadata.get('source', 'Unknown Source')
                page_num = doc.metadata.get('page_number', doc.metadata.get('page', 'Unknown'))
                content = doc.page_content
                
                # Display the source content
                self.source_content_text.delete(1.0, tk.END)
                
                # Add header with source information
                header = f"Source: {source_file}\n"
                if page_num != 'Unknown':
                    header += f"Page: {page_num}\n"
                header += "=" * 50 + "\n\n"
                
                self.source_content_text.insert(tk.END, header)
                self.source_content_text.insert(tk.END, content)
                
                # Highlight the header
                self.source_content_text.tag_add("header", "1.0", "4.0")
                self.source_content_text.tag_config("header", font=("Arial", 10, "bold"), foreground="blue")
                
        except (ValueError, IndexError) as e:
            self.logger.error(f"Error displaying source content: {e}")
            self.source_content_text.delete(1.0, tk.END)
            self.source_content_text.insert(tk.END, "Error loading source content.")
    
    def display_sources(self, sources: List[str]):
        """Display sources in the tree view"""
        self.clear_sources()
        
        for i, source in enumerate(sources):
            # Parse source string to extract filename and page
            if " (Page: " in source:
                filename, page_part = source.rsplit(" (Page: ", 1)
                page = page_part.rstrip(")")
            else:
                filename = source
                page = "Unknown"
            
            self.sources_tree.insert("", tk.END, text=f"Source {i+1}", values=(filename, page))
    
    def clear_sources(self):
        """Clear sources tree and content display"""
        for item in self.sources_tree.get_children():
            self.sources_tree.delete(item)
        
        # Clear source content display if it exists
        if hasattr(self, 'source_content_text'):
            self.source_content_text.delete(1.0, tk.END)
            self.source_content_text.insert(tk.END, "Double-click on a source above to view its content...")
    
    def clear_query(self):
        """Clear query text"""
        self.query_text.delete(1.0, tk.END)
    
    def reset_database(self):
        """Reset the vector database"""
        if messagebox.askyesno("Confirm Reset", "Are you sure you want to reset the database? This will delete all processed data."):
            try:
                import shutil
                if os.path.exists(self.config.persist_directory):
                    shutil.rmtree(self.config.persist_directory)
                
                self.processor.vector_db = None
                self.update_database_status()
                self.status_var.set("Database reset - Please process PDFs to create new database")
                messagebox.showinfo("Success", "Database reset successfully.")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to reset database: {e}")
    
    def configure_api_key(self):
        """Configure API key"""
        api_key = self.get_api_key_from_user()
        if api_key:
            self.set_api_key(api_key)
    
    def show_advanced_settings(self):
        """Show advanced settings dialog"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Advanced Settings")
        dialog.geometry("400x300")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Settings variables
        chunk_size_var = tk.IntVar(value=self.config.chunk_size)
        chunk_overlap_var = tk.IntVar(value=self.config.chunk_overlap)
        max_docs_var = tk.IntVar(value=self.config.max_retrieved_docs)
        
        # Create form
        ttk.Label(dialog, text="Chunk Size:").pack(pady=5)
        ttk.Entry(dialog, textvariable=chunk_size_var).pack(pady=2)
        
        ttk.Label(dialog, text="Chunk Overlap:").pack(pady=5)
        ttk.Entry(dialog, textvariable=chunk_overlap_var).pack(pady=2)
        
        ttk.Label(dialog, text="Max Retrieved Documents:").pack(pady=5)
        ttk.Entry(dialog, textvariable=max_docs_var).pack(pady=2)
        
        def apply_settings():
            self.config.chunk_size = chunk_size_var.get()
            self.config.chunk_overlap = chunk_overlap_var.get()
            self.config.max_retrieved_docs = max_docs_var.get()
            
            # Recreate text splitter with new settings
            self.processor.text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=self.config.chunk_size,
                chunk_overlap=self.config.chunk_overlap,
                length_function=len,
                is_separator_regex=False,
            )
            
            dialog.destroy()
            messagebox.showinfo("Settings Applied", "Settings updated successfully. You may need to reprocess PDFs for changes to take effect.")
        
        ttk.Button(dialog, text="Apply", command=apply_settings).pack(pady=20)
    
    def export_results(self):
        """Export query results to file"""
        if not hasattr(self, '_last_query_result') or not self._last_query_result:
            messagebox.showwarning("No Results", "No query results to export.")
            return
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("Markdown files", "*.md"), ("All files", "*.*")],
            title="Export Results"
        )
        
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(f"Relevantr - Scientific PDF RAG Application\n")
                    f.write(f"Query Results Report\n")
                    f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write("=" * 50 + "\n\n")
                    
                    f.write(f"Query: {self._last_query}\n\n")
                    f.write(f"Answer:\n{self._last_query_result.get('answer', '')}\n\n")
                    
                    if 'retrieved_docs' in self._last_query_result:
                        f.write("Detailed Sources with Content:\n")
                        for i, doc in enumerate(self._last_query_result['retrieved_docs'], 1):
                            source_file = doc.metadata.get('source', 'Unknown Source')
                            page_num = doc.metadata.get('page_number', doc.metadata.get('page', 'Unknown'))
                            
                            f.write(f"\n{i}. {source_file}")
                            if page_num != 'Unknown':
                                f.write(f" (Page: {page_num})")
                            f.write(f"\n{'-' * 40}\n")
                            f.write(f"{doc.page_content}\n")
                    elif 'sources' in self._last_query_result:
                        f.write("Sources:\n")
                        for i, source in enumerate(self._last_query_result['sources'], 1):
                            f.write(f"{i}. {source}\n")
                
                messagebox.showinfo("Success", f"Results exported to {filename}")
                
            except Exception as e:
                messagebox.showerror("Export Error", f"Failed to export results: {e}")
    
    def show_about(self):
        """Show about information in the main results window"""
        # Get current model info
        current_model = getattr(self.config, 'generation_model', 'Not configured')
        is_premium = "pro" in current_model.lower() and "flash" not in current_model.lower()
        
        about_text = f"""
🔬 RELEVANTR - Scientific PDF RAG Application 📚
======================================================

Version: 1.0
Created by: Erik Bitzek, August 2025

CURRENT CONFIGURATION:
AI Model: {current_model}
Tier: {'Premium (Paid)' if is_premium else 'Free Tier'}
Status: {'🎯 You have Pro access!' if is_premium else '✅ Using free tier'}

ABOUT:
Relevantr is a comprehensive Retrieval-Augmented Generation (RAG) 
application designed for analyzing scientific literature using AI.

FEATURES:
• PDF document processing and indexing
• Vector database storage with ChromaDB
• AI-powered question answering with Google Gemini
• Automatic model detection (Pro/Flash)
• Source attribution and citation tracking
• Advanced chunking and retrieval strategies
• Export functionality for results
• Interactive source content viewing

TECHNICAL STACK:
• Python & Tkinter (GUI)
• LangChain (Document processing)
• Google Gemini AI (Generation)
• ChromaDB (Vector storage)
• PyMuPDF (PDF processing)

USAGE:
1. Set your Google Gemini API key
2. Select your PDF directory
3. Process PDFs to build database
4. Ask scientific questions
5. Explore results with source citations

COPYRIGHT:
© 2025 Erik Bitzek - Relevantr
Licensed under CC BY-NC-SA 4.0

For more information, visit: https://github.com/biterik/Relevantr

======================================================
"""
        
        # Clear the results window and show about info
        self.results_text.delete(1.0, tk.END)
        self.results_text.insert(tk.END, about_text)
        
        # Clear sources panel
        self.clear_sources()
        if hasattr(self, 'source_content_text'):
            self.source_content_text.delete(1.0, tk.END)
            self.source_content_text.insert(tk.END, "About information displayed in main window.")
        
        # Update status
        model_info = f"Premium model" if is_premium else "Free tier model"
        self.status_var.set(f"About displayed - Using {current_model} ({model_info}) - Ask a question to return to normal mode")
    
    def force_enable_query(self):
        """Debug function to force enable query interface"""
        self.ask_btn.config(state='normal')
        self.query_text.config(state='normal')
        self.status_var.set("Debug: Query interface force-enabled")
        messagebox.showinfo("Debug", "Query interface has been force-enabled. You can now try asking questions.")
    
    def run(self):
        """Run the application"""
        try:
            self.logger.info("Starting Relevantr - Scientific PDF RAG Application")
            self.root.mainloop()
        except KeyboardInterrupt:
            self.logger.info("Relevantr interrupted by user")
        except Exception as e:
            self.logger.error(f"Relevantr application error: {e}")
            messagebox.showerror("Application Error", f"An unexpected error occurred: {e}")
        finally:
            self.logger.info("Relevantr closing")


def main():
    """Main entry point"""
    try:
        # Check dependencies
        required_packages = [
            ('tkinter', 'tk'),
            ('google.generativeai', 'google-generativeai'), 
            ('langchain', 'langchain'), 
            ('langchain_community', 'langchain-community'),
            ('langchain_google_genai', 'langchain-google-genai'),
            ('chromadb', 'chromadb'),
            ('tqdm', 'tqdm'),
            ('dotenv', 'python-dotenv')  # Import name is 'dotenv', package name is 'python-dotenv'
        ]
        
        missing_packages = []
        for import_name, install_name in required_packages:
            try:
                __import__(import_name)
            except ImportError:
                missing_packages.append(install_name)
        
        if missing_packages:
            print("Missing required packages for Relevantr. Install with either:")
            print("\nUsing pip:")
            print("pip install " + " ".join(missing_packages))
            print("\nUsing conda:")
            conda_packages = [p for p in missing_packages if p in ['tqdm', 'python-dotenv']]
            pip_packages = [p for p in missing_packages if p not in ['tqdm', 'python-dotenv']]
            
            if conda_packages:
                print("conda install -c conda-forge " + " ".join(conda_packages))
            if pip_packages:
                print("pip install " + " ".join(pip_packages))
            return
        
        # Create and run Relevantr
        app = ScientificRAGApp()
        app.run()
        
    except Exception as e:
        print(f"Failed to start Relevantr: {e}")
        traceback.print_exc()


if __name__ == "__main__":
    main()
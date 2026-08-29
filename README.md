# BookMind 📚⚡

**BookMind** is a State-of-the-Art (SOTA) AI-powered book analysis, structural layout extraction, and interactive chat assistant built with **FastAPI**, **LangGraph**, **PyMuPDF**, **ChromaDB**, and **Ollama / DeepSeek LLMs**.

---

## 🏛️ Enterprise Clean Architecture & DDD Structure

BookMind is structured following strict Domain-Driven Design (DDD) and Clean Architecture principles:

```text
src/bookmind/
│
├── domain/                  # 🧠 1. DOMAIN LAYER (Pure Business Entities & Exceptions)
│   ├── books/               # BookInfo, BookMap, Chapter Entities
│   └── common/              # Custom Domain Exceptions
│
├── application/             # ⚙️ 2. APPLICATION LAYER (CQRS Use Cases, Commands & Queries)
│   ├── books/               # CreateBook, DeleteBook, ListBooks, GetBook Handlers
│   └── qa/                  # AskBook Streaming Query Handler
│
├── ai/                      # 🤖 3. AI CORE LAYER (Agents, Prompts & PDF Services)
│   ├── agents/              # BaseAgent, ChatAgent, HierarchyExtractorAgent
│   ├── prompts/             # System Prompts (chat_agent_prompt.py, hierarchy_extractor_prompt.py)
│   └── services/            # pdf_service.py (TOC/Bookmark Reader) & layout_parser.py (Observer Motor)
│
├── workflows/               # 🔀 4. WORKFLOWS LAYER (LangGraph Orchestration Pipelines)
│   ├── ingestion/           # 4-Node 0-LLM / LLM Ingestion Graph
│   └── qa/                  # Real-Time QA Streaming Graph
│
├── infrastructure/          # 🔌 5. INFRASTRUCTURE LAYER (File Services & Configuration)
│   ├── configuration/       # Settings & LLMProvider (.env Config)
│   └── services/            # file/pdf_file_service.py (JSON Map & Document Persistence)
│
└── web/                     # 🌐 6. WEB PRESENTATION LAYER (FastAPI API & UI)
    ├── api/                 # Endpoint Controllers (/api/books, /api/documents, /api/chat)
    ├── dtos/                # Request/Response Pydantic DTOs (ChatMessage, ChatResponse)
    └── ui/                  # Jinja2 Templates & Static Assets (CSS/JS)
```

---

## 📐 Ingestion Pipeline Flow (SOTA 0-LLM / LLM Smart Router)

```text
                       [ PDF Yüklenir ]
                              │
                              ▼
            [1. Düğüm: label_pdf_layout]           <-- (Fiziki Etiketleme Label)
                              │
                              ▼
            [2. Düğüm: check_toc_type]             <-- (İçindekiler Checker)
                              │
      ┌───────────────────────┼───────────────────────┐
      │                       │                       │
 🟢 1. YOL (BM Var)     🟡 2. YOL (Basılı TOC)   🔴 3. YOL (Düzensiz)
 (0 LLM ÇAĞRISI)         (0 LLM ÇAĞRISI)        (YALNIZCA BURADA LLM)
      │                       │                       │
      ▼                       ▼                       ▼
  [Direkt Geçiş]        [3A. Düğüm:             [3B. Düğüm:
                         extract_toc_page]       map_unstructured_layout]
      │                       │                       │
      └───────────────────────┼───────────────────────┘
                              ▼
            [4. Düğüm: build_hierarchy_list]       <-- (HierarchyExtractorAgent LLM)
```

---

## ⚡ Key Features

- **SOTA Hybrid Layout Engine ("Gözlemci" Motoru)**: 
  - **1. Level (Embedded Bookmarks/Hyperlinks - 0 LLM)**: Instantly extracts sidebar outlines and internal links with 3 smart filters.
  - **2. Level (Physical TOC Parser - 0 LLM)**: Directly extracts printed "İÇİNDEKİLER" / "CONTENTS" pages into structured chapters.
  - **3. Level (Fallback Physical Layout Parsing & Aggregator)**: Parses unstructured PDFs using font sizes, boldness (`is_bold`), bounding box coordinates (`bbox`), images, tables (`page.find_tables()`), and mathematical formulas. Includes rule-based split heading merging and pseudo-heading filtering.
- **HierarchyExtractorAgent**: Specialized LLM agent invoked **ONLY for unstructured PDFs** to construct pristine nested `BookMap` trees specifically from header-tagged elements.
- **Fast Real-Time Streaming Chat**: Token-by-token streaming (TTFT ~1.0s) powered by local Ollama (`qwen3.5:4b`) or Cloud DeepSeek APIs.
- **DDD & CQRS Clean Architecture**: Zero circular dependencies, isolated DTOs, file persistence services, and clear separation of concerns.

---

## 🚀 Quick Start

### 1. Install Dependencies
```bash
uv sync
```

### 2. Configure Environment
Set provider and parameters in `.env`:
```env
LLM_PROVIDER=ollama
OLLAMA_MODEL=qwen3.5:4b
OLLAMA_BASE_URL=http://localhost:11434
```

### 3. Run Application
```bash
uv run bookmind
```
Open `http://localhost:8000` in your browser.

---

## 🧪 Verification

Run python compilation and route checks:
```bash
uv run python -c "from bookmind.main import app; print('App Loaded!')"
```

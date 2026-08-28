# BookMind 📚⚡

**BookMind** is a State-of-the-Art (SOTA) AI-powered book analysis, structural layout extraction, and interactive chat assistant built with **FastAPI**, **LangGraph**, **PyMuPDF**, and **Ollama / DeepSeek LLMs**.

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
├── ai/                      # 🤖 3. AI CORE LAYER (Agents, Prompts & PDF Parsers)
│   ├── agents/              # BaseAgent, ChatAgent, MapperAgent
│   ├── prompts/             # System Prompts (chat_agent_prompt.py, mapper_agent_prompt.py)
│   └── services/            # pdf_parser.py (TOC/Bookmark Extractor) & layout_parser.py (Observer Motor)
│
├── workflows/               # 🔀 4. WORKFLOWS LAYER (LangGraph Orchestration Pipelines)
│   ├── ingestion/           # PDF Ingestion & Fallback Layout Parsing Graph
│   └── qa/                  # Real-Time QA Streaming Graph
│
├── infrastructure/          # 🔌 5. INFRASTRUCTURE LAYER (Persistence & Configuration)
│   ├── configuration/       # Settings & LLMProvider (.env Config)
│   └── database/            # MapRepository (JSON Storage)
│
└── web/                     # 🌐 6. WEB PRESENTATION LAYER (FastAPI API & UI)
    ├── api/                 # Endpoint Controllers (/api/books, /api/documents, /api/chat)
    ├── schemas/             # Request/Response Pydantic DTOs
    └── ui/                  # Jinja2 Templates & Static Assets (CSS/JS)
```

---

## ⚡ Key Features

- **SOTA Hybrid Layout Engine ("Gözlemci" Motoru)**: 
  - **1. Level (Embedded Bookmarks/Hyperlinks)**: Automatically inspects PDF sidebar outlines and internal links with 3 smart filters (location isolation, cross-reference filtering, monotonic page ordering).
  - **2. Level (Fallback Physical Layout Parsing)**: Parses unstructured PDFs using font sizes, boldness (`is_bold`), bounding box coordinates (`bbox`), images, tables (`page.find_tables()`), and mathematical formulas.
- **Fast Real-Time Streaming Chat**: Token-by-token streaming (TTFT ~1.0s) powered by local Ollama (`qwen3.5:4b`) or Cloud DeepSeek APIs.
- **DDD & CQRS Clean Architecture**: Zero circular dependencies, modularized prompt files, and clear separation of concerns.

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

## 🧪 Testing & Verification

Run python compilation and route checks:
```bash
uv run python -c "from bookmind.main import app; print('App Loaded!')"
```

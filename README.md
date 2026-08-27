# BookMind 📚⚡

**BookMind** is an AI-powered book analysis and interactive chat assistant built with **FastAPI**, **LangGraph**, and **Ollama / DeepSeek LLMs**.

---

## 🏗️ Architecture

BookMind uses a **Dual-LangGraph Architecture** designed for modularity and high performance:

```text
src/bookmind/graph/
├── pdf/       # 📄 PDF Processing & Chapter Mapping Graph (Extract TOC -> Map Chapters -> Storage)
└── chat/      # 💬 Real-Time Streaming Chat Graph (Fast, unbuffered Token Streaming)
```

---

## ⚡ Features

- **High-Speed Real-Time Chat**: Sub-second initial token response (TTFT ~1.0s) powered by local Ollama (`qwen3.5:4b`) or cloud DeepSeek APIs with streaming response.
- **PDF Structure Mapping**: Automated table-of-contents extraction and hierarchical chapter mapping.
- **Modular LangGraph Workflows**: Isolated `state.py` and `nodes/` architecture for PDF processing and chat pipelines.

---

## 🚀 Quick Start

### 1. Install Dependencies
```bash
uv sync
```

### 2. Configure Environment
Set provider in `.env`:
```env
LLM_PROVIDER=ollama
OLLAMA_MODEL=qwen3.5:4b
```

### 3. Run Application
```bash
uv run bookmind
```
Open `http://localhost:8000` in your browser.

### 4. Run Test Script
```bash
python test_chat.py
```

# BookMind 📚⚡ — AI Kitap Haritalama ve Agentic RAG Platformu

**BookMind**, karmaşık PDF belgelerini ve kitapları otomatik analiz ederek hiyerarşik haritalarını (`BookMap`) çıkaran, verileri vektörleştirip saklayan ve **Agentic RAG (Tool-Based RAG)** mimarisi ile kullanıcıların kitaplarla etkileşimli sohbet etmesini sağlayan State-of-the-Art (SOTA) bir yapay zeka platformudur.

---

## 🌟 Öne Çıkan Yetenekler ve Mimari (Key Features)

### 1. 🔀 SOTA Hybrid Ingestion Pipeline (LangGraph 0-LLM / LLM Akıllı Yönlendirici)
PDF yüklendiğinde işletilen 4 aşamalı iş akış hattı (Ingestion Workflow):
- **1. Yol (Gömülü Bookmark / Yer İmleri - 0 LLM ÇAĞRISI)**: PDF sidebar yer imlerini ve iç köprülerini anında süzerek 0 maliyetle hiyerarşiyi çıkarır.
- **2. Yol (Fiziki İçindekiler Sayfası - 0 LLM ÇAĞRISI)**: Basılı "İÇİNDEKİLER" / "TABLE OF CONTENTS" sayfalarını etiketleyip ayıklar.
- **3. Yol (Düzensiz PDF Layout Parser - Akıllı LLM)**: Başlık boyutu (`font-size`), kalınlık (`is_bold`), koordinat (`bbox`) ve görsel/tablo analizleriyle hiyerarşiyi oluşturur.

### 2. 🗃️ Çift Veritabanı Mimarisi (SQLite + ChromaDB)
- **SQLite Relational DB**: 250 kelimelik metin parçalarını (chunks), sayfa aralıklarını ve **iki yönlü bağlı liste (`prev_chunk_id`, `next_chunk_id`)** ilişkilerini saklar.
- **ChromaDB Vector DB**: Metin parçalarını ve hiyerarşik bölüm başlıklarını `intfloat/multilingual-e5-base` modeli ile 768-boyutlu vektörlere dönüştürerek indeksler.

### 3. 🎯 Hiyerarşik RAG & Re-Ranking Motoru
- **Vektör Benzerliği ile Başlık Seçimi**: Kullanıcı sorgusu geldiğinde ilk olarak kitabın hiyerarşik bölüm başlıkları arasından en alakalı bölüm (`chapter_id`) seçilir.
- **Cross-Encoder Re-Ranking**: Seçilen bölüm altındaki chunk'lar `cross-encoder/ms-marco-MiniLM-L-6-v2` modeli ile sorguya göre yeniden puanlanır.
- **3-Chunk Genişletilmiş Bağlam**: En yüksek skorlu chunk'ın **bir öncesi + kendisi + bir sonrası** birleştirilerek anlamsal bütünlüğü bozulmamış bağlam penceresi (`expanded context`) elde edilir.

### 4. 🤖 Agentic RAG Sohbet Asistanı (LangChain Tool Calling & DeepSeek)
- **Dinamik Tool Kullanımı (`search_book_context`)**: Model kullanıcı mesajını analiz eder; genel sohbetlerde veritabanı araması yapmaz, kitap sorularında ise `search_book_context` aracını çalıştırır.
- **Çok Adımlı Arama (Multi-Step Retrieval)**: Karmaşık sorularda model farklı arama terimleriyle aracı birden fazla kez çağırıp farklı bölümlerdeki bağlamları sentezleyebilir.
- **Canlı Streaming**: DeepSeek (`deepseek-chat`) ve Ollama modelleri üzerinden kelime kelime (token-by-token) canlı akış yanıtı üretir.

### 5. 🔬 İnteraktif Test Laboratuvarı (`/test`)
- PDF bookmark yapısını ve 0 LLM / LLM teşhislerini anında test imkanı.
- Sorgu girdiğinizde vektör benzerliği ile seçilen başlığı, Cross-Encoder 1. olan target chunk'ı ve Chat modeline beslenen 3'lü birleştirilmiş chunk parçalarını anında gösteren RAG laboratuvarı.

---

## 🏛️ Clean Architecture & DDD Proje Yapısı

BookMind, kurumsal SaaS standartlarında Clean Architecture ve Domain-Driven Design (DDD) prensipleriyle geliştirilmiştir:

```text
src/bookmind/
│
├── domain/                  # 🧠 1. DOMAIN LAYER (Saf İş Modelleri ve Entitiler)
│   ├── books/               # BookInfo, BookMap, Chapter Nesneleri
│   └── common/              # Özel Domain İstisnaları (Exceptions)
│
├── application/             # ⚙️ 2. APPLICATION LAYER (CQRS Use Case'ler)
│   ├── books/               # CreateBook, DeleteBook, ListBooks, GetBook İşleyicileri
│   └── qa/                  # AskBook Streaming Query Handler
│
├── ai/                      # 🤖 3. AI CORE LAYER (Agentic RAG, Tools & Prompts)
│   ├── agents/              # BaseAgent, ChatAgent, HierarchyExtractorAgent
│   ├── tools/               # search_book_context LangChain Tool Wrappers
│   ├── rag/                 # RAGService, Embedder (e5-base), CrossEncoder (ms-marco)
│   ├── prompts/             # System Prompts (chat_agent_prompt.py)
│   └── services/            # ChunkingService, PDFService, LayoutParser Engine
│
├── workflows/               # 🔀 4. WORKFLOWS LAYER (LangGraph Orkestrasyonu)
│   ├── ingestion/           # PDF İşleme ve Haritalama LangGraph Akışı
│   └── qa/                  # Agentic QA Chat LangGraph Akışı
│
├── infrastructure/          # 🔌 5. INFRASTRUCTURE LAYER (Veritabanları ve Konfigürasyon)
│   ├── configuration/       # Settings & LLMProvider (.env Yönetimi)
│   └── services/            # SQLiteService, VectorService (ChromaDB), PDFFileService
│
└── web/                     # 🌐 6. WEB PRESENTATION LAYER (FastAPI API & UI)
    ├── api/                 # REST Endpoints (/api/books, /api/chat, /api/chat/test-rag)
    ├── dtos/                # Request/Response Pydantic Şemaları
    └── ui/                  # Web Arayüzü (Jinja2 Templates & Static Assetler)
```

---

## 🚀 Hızlı Başlangıç (Quick Start)

### 1. Bağımlılıkları Yükleyin
```bash
uv sync
```

### 2. Konfigürasyonu Ayarlayın
`.env` dosyasından LLM sağlayıcınızı (`deepseek` veya `ollama`) ve API anahtarlarınızı seçin:
```env
LLM_PROVIDER=deepseek
DEEPSEEK_API_KEY=sk-your-api-key
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_DEFAULT_MODEL=deepseek-chat
```

### 3. Uygulamayı Başlatın
```bash
uv run bookmind
```
Tarayıcınızdan `http://localhost:8000` adresini açarak uygulamayı kullanmaya başlayabilirsiniz!
Test laboratuvarı için: `http://localhost:8000/test`

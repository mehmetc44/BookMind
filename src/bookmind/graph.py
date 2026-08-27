"""LangGraph pipeline - PDF'den kitap haritası oluşturma."""

from __future__ import annotations

import json
import os
from typing import Any, TypedDict

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langgraph.graph import END, StateGraph

from bookmind.models import BookMap
from bookmind.pdf_utils import extract_toc_text, get_page_count

load_dotenv()


class GraphState(TypedDict):
    """LangGraph state."""

    pdf_path: str
    toc_text: str
    total_pages: int
    book_map: dict[str, Any] | None
    error: str | None


def get_llm() -> ChatOpenAI:
    """DeepSeek LLM instance'ı döndürür."""
    return ChatOpenAI(
        model="deepseek-chat",
        api_key=os.getenv("DEEPSEEK_API_KEY", ""),
        base_url="https://api.deepseek.com",
        temperature=0.1,
        max_tokens=8000,
    )


def extract_toc_node(state: GraphState) -> GraphState:
    """PDF'den içindekiler metnini çıkarır."""
    pdf_path = state["pdf_path"]
    try:
        toc_text = extract_toc_text(pdf_path)
        total_pages = get_page_count(pdf_path)
        return {**state, "toc_text": toc_text, "total_pages": total_pages}
    except Exception as e:
        return {**state, "error": f"PDF okuma hatası: {e!s}"}


def map_chapters_node(state: GraphState) -> GraphState:
    """DeepSeek API ile içindekiler metninden kitap haritası oluşturur."""
    if state.get("error"):
        return state

    toc_text = state["toc_text"]
    total_pages = state["total_pages"]
    llm = get_llm()

    system_prompt = """Sen bir kitap analiz asistanısın. Sana verilen içindekiler bilgisinden kitabın yapısal haritasını JSON formatında çıkarmalısın.

ÇIKTI FORMATI (sadece valid JSON döndür, başka bir şey yazma):
{
  "book_title": "Kitabın başlığı",
  "author": "Yazar adı (bilinmiyorsa 'Bilinmiyor')",
  "total_pages": <toplam sayfa sayısı>,
  "chapters": [
    {
      "id": "chapter_1",
      "title": "1. Bölüm Başlığı",
      "page_start": 1,
      "page_end": 42,
      "summary": "Bu bölüm hakkında kısa bir özet.",
      "topics": ["konu1", "konu2"],
      "keywords": ["anahtar1", "anahtar2"],
      "children": [
        {
          "id": "chapter_1_1",
          "title": "1.1 Alt Bölüm",
          "page_start": 1,
          "page_end": 15,
          "summary": "Alt bölüm özeti.",
          "topics": ["alt_konu1"],
          "keywords": ["alt_anahtar1"],
          "children": []
        }
      ]
    }
  ]
}

KURALLAR:
1. Her bölüm için benzersiz bir id oluştur (chapter_1, chapter_1_1, chapter_2 vb.)
2. Alt bölümleri children array'ine koy
3. Sayfa numaralarını içindekilerden al, bilinmiyorsa tahmin et
4. Her bölüm için kısa ama anlamlı bir summary yaz
5. Topics ve keywords'ü Türkçe ve İngilizce karışık yaz
6. Sadece valid JSON döndür, markdown veya açıklama ekleme
7. total_pages değeri: """ + str(total_pages)

    user_prompt = f"""Aşağıdaki içindekiler bilgisinden kitabın yapısal haritasını oluştur:

{toc_text}

Toplam sayfa sayısı: {total_pages}

Sadece JSON formatında yanıt ver."""

    try:
        response = llm.invoke([
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ])

        response_text = response.content.strip()
        # Markdown code block varsa temizle
        if response_text.startswith("```"):
            lines = response_text.split("\n")
            # İlk ve son satırı kaldır
            lines = [l for l in lines if not l.strip().startswith("```")]
            response_text = "\n".join(lines)

        book_map_dict = json.loads(response_text)
        # Validate with Pydantic
        book_map = BookMap(**book_map_dict)
        return {**state, "book_map": book_map.model_dump()}

    except json.JSONDecodeError as e:
        return {**state, "error": f"JSON parse hatası: {e!s}\nResponse: {response_text[:500]}"}
    except Exception as e:
        return {**state, "error": f"LLM hatası: {e!s}"}


def should_continue(state: GraphState) -> str:
    """Hata varsa durdur, yoksa devam et."""
    if state.get("error"):
        return END
    return "map_chapters"


def build_graph() -> StateGraph:
    """LangGraph pipeline'ı oluşturur."""
    workflow = StateGraph(GraphState)

    workflow.add_node("extract_toc", extract_toc_node)
    workflow.add_node("map_chapters", map_chapters_node)

    workflow.set_entry_point("extract_toc")
    workflow.add_conditional_edges("extract_toc", should_continue)
    workflow.add_edge("map_chapters", END)

    return workflow.compile()


async def process_pdf(pdf_path: str) -> dict[str, Any]:
    """PDF'i işleyip kitap haritası döndürür.

    Args:
        pdf_path: PDF dosya yolu.

    Returns:
        BookMap dict veya hata bilgisi.
    """
    graph = build_graph()
    initial_state: GraphState = {
        "pdf_path": pdf_path,
        "toc_text": "",
        "total_pages": 0,
        "book_map": None,
        "error": None,
    }

    result = await graph.ainvoke(initial_state)

    if result.get("error"):
        return {"success": False, "error": result["error"]}

    return {"success": True, "book_map": result["book_map"]}

"""graph package — LangGraph pipeline public API.

Bu paket altında iki bağımsız LangGraph hattı bulunur:
1. pdf/  : PDF İşleme & Haritalama Akışı
2. chat/ : Sohbet Akışı
"""

from bookmind.graph.chat import ChatGraphState, build_chat_graph, stream_chat_graph
from bookmind.graph.pdf import PDFGraphState, build_pdf_graph, process_pdf

# Geriye dönük uyumluluk takma adı (alias)
build_graph = build_pdf_graph

__all__ = [
    "PDFGraphState",
    "build_pdf_graph",
    "process_pdf",
    "ChatGraphState",
    "build_chat_graph",
    "stream_chat_graph",
    "build_graph",
]

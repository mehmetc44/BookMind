"""ai.rag.cross_encoder — CrossEncoder class using local cross-encoder/ms-marco-MiniLM-L-6-v2 model for re-ranking."""

from __future__ import annotations

from typing import Any
from sentence_transformers import CrossEncoder as STCrossEncoder


class CrossEncoder:
    """Yerelde indirili olan 'cross-encoder/ms-marco-MiniLM-L-6-v2' modeli ile aday chunk'ları yeniden puanlayan ve sıralayan (Re-ranking) servis."""

    MODEL_NAME = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    _model: STCrossEncoder | None = None

    @classmethod
    def get_model(cls) -> STCrossEncoder:
        """CrossEncoder modelini önbellekten (cache) yükler."""
        if cls._model is None:
            print(f"🎯 [CrossEncoder] Yerele indirilmiş '{cls.MODEL_NAME}' re-ranker modeli yükleniyor...")
            cls._model = STCrossEncoder(cls.MODEL_NAME)
            print(f"✅ [CrossEncoder] '{cls.MODEL_NAME}' başarıyla yüklendi!")
        return cls._model

    @classmethod
    def rank(
        cls,
        query: str,
        chunks: list[dict[str, Any]],
        top_k: int = 3,
    ) -> list[dict[str, Any]]:
        """Soru ile aday chunk metinleri ikililerini (query, chunk_content) puanlar ve en yüksek skorlu top_k chunk'ı döndürür."""
        if not chunks:
            return []

        model = cls.get_model()

        # (soru, chunk_metni) ikililerini hazırla
        pairs = [[query, c.get("content", "")] for c in chunks]

        # CrossEncoder skorlarını hesapla
        scores = model.predict(pairs)

        # Chunk nesnelerine rerank_score alanını ekle
        ranked_chunks = []
        for idx, chunk in enumerate(chunks):
            score = float(scores[idx]) if idx < len(scores) else 0.0
            chunk_copy = dict(chunk)
            chunk_copy["rerank_score"] = score
            ranked_chunks.append(chunk_copy)

        # Skora göre büyükten küçüğe sırala
        ranked_chunks.sort(key=lambda x: x["rerank_score"], reverse=True)

        print(f"🎯 [CrossEncoder] {len(chunks)} aday chunk arasından en yüksek skorlu {min(top_k, len(ranked_chunks))} chunk seçildi.")
        return ranked_chunks[:top_k]

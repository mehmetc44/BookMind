"""ai.rag.embedder — Embedder class using local intfloat/multilingual-e5-base model."""

from __future__ import annotations

from sentence_transformers import SentenceTransformer


class Embedder:
    """Yerelde indirili olan 'intfloat/multilingual-e5-base' modeli ile metin ve sorgu embedding üretici servis."""

    MODEL_NAME = "intfloat/multilingual-e5-base"
    _model: SentenceTransformer | None = None

    @classmethod
    def get_model(cls) -> SentenceTransformer:
        """SentenceTransformer modelini önbellekten (cache) yükler."""
        if cls._model is None:
            print(f"🧬 [Embedder] Yerele indirilmiş '{cls.MODEL_NAME}' modeli yükleniyor...")
            cls._model = SentenceTransformer(cls.MODEL_NAME)
            print(f"✅ [Embedder] '{cls.MODEL_NAME}' başarıyla yüklendi!")
        return cls._model

    @classmethod
    def embed_documents(cls, texts: list[str]) -> list[list[float]]:
        """PDF chunk metinlerini 'passage: ' önekiyle 768-boyutlu vektörlere dönüştürür."""
        if not texts:
            return []

        model = cls.get_model()
        prefixed_texts = [f"passage: {t}" for t in texts]

        embeddings = model.encode(
            prefixed_texts,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        return embeddings.tolist()

    @classmethod
    def embed_query(cls, query: str) -> list[float]:
        """Kullanıcının sorusunu 'query: ' önekiyle 768-boyutlu vektöre dönüştürür."""
        model = cls.get_model()
        prefixed_query = f"query: {query}"

        embedding = model.encode(
            prefixed_query,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        return embedding.tolist()

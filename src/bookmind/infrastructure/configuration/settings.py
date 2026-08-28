"""infrastructure.configuration.settings — App configuration loaded from .env environment variables."""

from __future__ import annotations

from enum import Enum
import os
from pathlib import Path

from dotenv import load_dotenv

# Proje kökündeki .env dosyasını bul ve yükle
_ENV_PATH = Path(__file__).resolve().parents[4] / ".env"
load_dotenv(dotenv_path=_ENV_PATH)


class LLMProvider(str, Enum):
    """Desteklenen LLM sağlayıcıları."""

    DEEPSEEK = "deepseek"
    OLLAMA = "ollama"


class Settings:
    """Uygulama genelinde kullanılan tüm konfigürasyon değerleri."""

    # ── LLM Sağlayıcı Seçimi ──────────────────────────────────────────────────
    LLM_PROVIDER: LLMProvider = LLMProvider(
        os.getenv("LLM_PROVIDER", "ollama").lower()
    )

    # ── DeepSeek Ayarları ─────────────────────────────────────────────────────
    DEEPSEEK_API_KEY: str = os.getenv("DEEPSEEK_API_KEY", "")
    DEEPSEEK_BASE_URL: str = os.getenv(
        "DEEPSEEK_BASE_URL", "https://api.deepseek.com"
    )
    DEEPSEEK_DEFAULT_MODEL: str = os.getenv(
        "DEEPSEEK_DEFAULT_MODEL", "deepseek-chat"
    )

    # ── Ollama Ayarları ───────────────────────────────────────────────────────
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "qwen3.5:4b")

    # ── Genel LLM Parametreleri ───────────────────────────────────────────────
    DEEPSEEK_TEMPERATURE: float = float(
        os.getenv("DEEPSEEK_TEMPERATURE", "0.1")
    )
    DEEPSEEK_MAX_TOKENS: int = int(
        os.getenv("DEEPSEEK_MAX_TOKENS", "8000")
    )

    # ── Sunucu ────────────────────────────────────────────────────────────────
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    RELOAD: bool = os.getenv("RELOAD", "true").lower() == "true"

    # ── Dosya Yolları ─────────────────────────────────────────────────────────
    BASE_DIR: Path = Path(__file__).resolve().parents[4]
    DATA_DIR: Path = BASE_DIR / "data"
    PDFS_DIR: Path = DATA_DIR / "pdfs"
    MAPS_DIR: Path = DATA_DIR / "maps"

    # ── PDF İşleme ────────────────────────────────────────────────────────────
    TOC_SCAN_PAGES: int = int(os.getenv("TOC_SCAN_PAGES", "15"))

    @classmethod
    def validate(cls) -> None:
        """Zorunlu değerlerin varlığını kontrol eder."""
        if cls.LLM_PROVIDER == LLMProvider.DEEPSEEK and not cls.DEEPSEEK_API_KEY:
            raise EnvironmentError(
                "LLM_PROVIDER=deepseek seçildi ancak DEEPSEEK_API_KEY bulunamadı. "
                ".env dosyasına 'DEEPSEEK_API_KEY=sk-...' ekleyin."
            )

    def __init_subclass__(cls, **kwargs: object) -> None:
        raise TypeError("Settings sınıfı subclass yapılamaz.")

    def __new__(cls) -> "Settings":
        raise TypeError("Settings bir singleton sınıftır, instance oluşturulamaz.")

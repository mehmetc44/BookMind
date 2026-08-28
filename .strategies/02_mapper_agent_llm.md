# 02. Mapper Agent & LLM İstek Stratejileri 🤖

Bu strateji modülü, ham içindekiler metnini LLM aracılığıyla kusursuz bir JSON harita yapısına dönüştürmeyi hedefler.

---

## 📋 Detaylı Yol Haritası & Checklist

### 2.1 Chunking & Token Yönetimi
- `[ ]` **Akıllı Metin Bölme (Chunking)**: Çok uzun içindekiler metinlerini modelin bağlam penceresini (context window) aşmayacak şekilde bölme.
- `[ ]` **Sistem Prompt Optimizasyonu**: LLM'e sadece JSON döndürmesini emreden sıkı sistem talimatları hazırlama.

### 2.2 Yapılandırılmış Çıktı (Structured Output / Pydantic)
- `[ ]` **Pydantic Şeması ile Garanti**: `book_title`, `author`, `chapters` (title, page_start, page_end, summary, topics, keywords) alanlarını Pydantic ile zorunlu kılma.
- `[ ]` **Çıktı Formatı Doğrulaması**: Model yanıtının geçerli bir JSON olduğunu `json.loads` ve Pydantic validasyonundan geçirme.

### 2.3 Hata Toleransı & Self-Correction (Kendi Kendini Düzeltme)
- `[ ]` **Otomatik Retry & Düzeltme**: Hatalı JSON üretildiğinde hatayı LLM'e geri gönderip "JSON formatını düzelt" deme mekanizması.
- `[ ]` **Eksik Sayfa Tamamlama**: LLM sayfa numaralarını atladıysa hebristik algoritma ile eksik sayfaları otomatik hesaplama.

---

## 📝 Özel Notlar & Beyin Fırtınası
*(Bu madde üzerinde detaylandıracağımız fikirler buraya yazılacaktır)*

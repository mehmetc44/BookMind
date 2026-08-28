# 03. Hiyerarşik Yapı & Ağaç (Tree) Görselleştirme Stratejileri 🌳

Bu strateji modülü, üretilen haritanın hiyerarşik (iç içe geçmiş alt bölümler) yapısını ve önbellekleme sistemini yönetir.

---

## 📋 Detaylı Yol Haritası & Checklist

### 3.1 İç İçe Bölüm Desteği (Nested Chapters)
- `[ ]` **Sonsuz Derinlik Desteği**: Ana Bölüm ➔ Alt Bölüm ➔ Alt-Alt Bölüm ($L_1 \to L_2 \to L_3$) ağaç veri yapısı.
- `[ ]` **Özet & Anahtar Kelime Zenginleştirme**: Her bölüm düğümü için `summary`, `topics` ve `keywords` etiketlerinin tutulması.

### 3.2 Harita Önbellekleme & Depolama (Caching & Storage)
- `[ ]` **JSON Önbellek Kaydı**: Üretilen haritaların `data/maps/{book_id}.json` altında saklanması.
- `[ ]` **Hızlı Erişim API'si**: `/api/books/{book_id}/map` endpoint'i üzerinden saniyeler içinde önbellekten harita okuma.

### 3.3 Arayüz (Tree View) Görselleştirme
- `[ ]` **Dinamik Ağaç Bileşeni**: Frontend `app.js` tarafında genişletilebilir/daraltılabilir (expand/collapse) ağaç görünümü.
- `[ ]` **Tümünü Genişlet / Daralt Butonları**: Kullanıcının tüm bölüm haritasını tek tıkla inceleyebilmesi.

---

## 📝 Özel Notlar & Beyin Fırtınası
*(Bu madde üzerinde detaylandıracağımız fikirler buraya yazılacaktır)*

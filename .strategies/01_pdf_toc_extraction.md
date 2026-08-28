# 01. PDF Metin & İçindekiler (TOC) Çıkarım Stratejileri 📄

Bu strateji modülü, PDF dosyalarından içindekiler tablosunu (TOC), bölüm başlıklarını ve sayfa numaralarını en yüksek hassasiyetle çıkarmayı hedefler.

---

## 📋 Detaylı Yol Haritası & Checklist

### 1.1 Gömülü TOC (Bookmark / Outline) & İç Bağlantı Analizi
- `[x]` **PyMuPDF (`doc.get_toc()`) Kullanımı**: PDF dosyasında kayıtlı olan resmi bookmark seviyelerini (Level 1, Level 2, Level 3) doğrudan okuma.
- `[x]` **İç Sayfa Bağlantıları (Internal Hyperlinks / Annotations)**: Gömülü sidebar bookmark'ı olmayan ancak içindekiler sayfasında tıklanabilir köprü bulunan PDF'lerde `page.get_links()` ile başlık ve hedef sayfa numaralarını ayıklama.
- `[x]` **3 Akıllı Köprü Filtresi (Hyperlink Filters)**:
  1. *Konum İzolasyonu*: Sadece ilk 1-5 sayfadaki bağlantıları tarama.
  2. *Çapraz Referans Filtresi*: "Bkz", "Tablo", "Şekil", "http" gibi metin içi referansları eleme.
  3. *Monotonik Sayfa Sıralaması*: Hedef sayfaların sırayla artmasını ($P_1 \le P_2 \le P_3$) şart koşma.
- `[x]` **Gömülü Bookmark / TOC Kontrol Laboratuvarı (`/test`)**: `/api/test-pdf-preview` üzerinden yüklenen PDF'lerin gömülü TOC ve Köprü varlığını görselleştiren canlı test ekranının kurulması.
- `[ ]` **Sayfa Numarası Doğrulaması**: Bookmark/Köprü içindeki sayfa indekslerinin PDF fiziğiyle birebir uyuşup uyuşmadığını doğrulama (Offset resolver).

### 1.2 Hebristik & Görsel Başlık Tespiti (Fallback Mekanizması)
- `[ ]` **Font Boyutu & Kalınlık Analizi**: Gömülü TOC bulunmayan kitaplarda, sayfa başlarındaki en büyük fontlu (Bold/Large) metinleri bölüm başlığı adayı olarak işaretleme.
- `[ ]` **Regex & Desen Tespiti**: "Bölüm 1", "Chapter 1", "1. Giriş", "Kısım I" gibi standart başlık kalıplarını regex ile tespit etme.
- `[ ]` **İlk N Sayfa Taraması**: Kitabın ilk 15-20 sayfasındaki basılı içindekiler sayfasını OCR veya metin ayıklama ile bulma.

### 1.3 Sayfa Aralığı (Range) & Bitiş Tespiti
- `[ ]` **Bölüm Sınırları Hızalaması**: Bölüm $N$'in bittiği sayfa ile Bölüm $N+1$'in başladığı sayfayı doğru bağlama ($Page_{start} \dots Page_{end}$).
- `[ ]` **Son Bölüm Sınırı**: Kitabın son bölümünün bitiş sayfasını `total_pages` değerine eşitleme.

---

## 📝 Özel Notlar & Beyin Fırtınası
*(Bu madde üzerinde detaylandıracağımız fikirler buraya yazılacaktır)*

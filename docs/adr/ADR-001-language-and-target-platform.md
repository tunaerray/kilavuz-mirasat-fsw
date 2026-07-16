# ADR-001: Uçuş Yazılımı Dili ve Hedef Platformu

- **Durum:** Kabul edildi
- **Tarih:** 2026-07-16
- **Karar veren:** Uçuş Yazılımı Mimarisi
- **İlgili:** CONFLICT-005, EKSİK-001, REQ-SW-001

## Bağlam

PDR (s.80) uçuş yazılımı için "C / C++, VS Code + Arduino IDE" belirtir; yer
istasyonu (s.90) Python + PyQt5'tir. Sistem çift işlemcilidir:

- **Görev Bilgisayarı:** Raspberry Pi 5 4GB (Linux) — durum makinesi, telemetri
  paketleme, kalıcılık, komut işleme, SD kayıt, kamera/video, bonus görev yönetimi.
- **Uçuş Kontrol Kartı:** PixMin V1.0 / STM32F405 — yüksek frekanslı IMU/baro
  stabilizasyon ve motor PID döngüleri, PWM üretimi.

ANA_PROMPT, bu çalışmanın **birincil odağını RPi 5 üzerindeki üst seviye Görev
Yazılımı** olarak tanımlar. Fiziksel donanım ve test ortamı bu oturumda mevcut
değildir; masaüstünde çalışabilen simülasyon hedefi gereklidir.

## Karar

**Üst seviye Görev Yazılımı (bu depo) Python 3 ile yazılır.** Zaman-kritik
stabilizasyon/PID katmanı hedef donanımda C/C++ (PixMin/STM32) olarak kalır ve
Python tarafından soyut bir `FlightControllerLink` (HAL) arayüzü üzerinden sürülür.

## Gerekçe

1. **Hedef platform uyumu:** RPi 5 tam bir Linux bilgisayarıdır; Python birinci
   sınıf desteklenir. Görev yönetimi, telemetri, dosya kalıcılığı ve komut işleme
   için C/C++ zorunluluğu yoktur.
2. **Hızlı geliştirme ve test edilebilirlik:** ANA_PROMPT masaüstü simülasyonu,
   mock sürücüler, deterministik test saati ve saniyeler içinde koşan test süiti
   ister. Python + pytest bunu doğrudan sağlar.
3. **Ekosistem:** pymavlink (FC bağlantısı), pyserial (LoRa/GPS), pyqt (mevcut yer
   istasyonu ile aynı dil) — takımın seçtiği araçlarla uyumlu.
4. **Güvenlik sınırı:** Gerçek zamanlı sabit deadline gerektiren düşük seviye
   motor kontrolü Python'da yapılmaz; o katman FC donanımında kalır. Python yalnız
   üst seviye görev kararlarını verir. Bu, `FlightControllerLink` soyutlamasıyla
   temiz biçimde ayrılır.

## Sonuçlar

- (+) Masaüstünde tam simülasyon, hızlı TDD, düşük giriş engeli.
- (+) Yer istasyonu ile ortak dil (Python) — paylaşılan veri şemaları mümkün.
- (−) RPi'da hard-real-time garantisi yok → zaman-kritik kontrol FC'ye devredilir
  (zaten mimari gereği doğru ayrım).
- (−) PDR'deki "C/C++" ifadesiyle biçimsel tutarsızlık → CDR'da güncellenmesi
  önerilir (rapor edildi).

## Alternatifler

- **Tümü C/C++ (RPi dahil):** Reddedildi — üst seviye görev yönetimi için gereksiz
  karmaşıklık, yavaş test döngüsü, simülasyon zorluğu.
- **MicroPython/STM32'de üst seviye:** Reddedildi — RPi 5'in kaynakları ve Linux
  araçları boşa gider; kalıcılık/dosya/kamera işleri RPi'da çok daha kolay.

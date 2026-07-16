# Varsayımlar ve Çelişkiler (ASSUMPTIONS_AND_CONFLICTS)

Bu belgedeki tüm çelişkiler **kaynak belgelerden birebir okunarak** doğrulanmıştır.
Sayfa referansları PDF sayfa numaralarıdır.

## Çelişkiler (CONFLICT)

### CONFLICT-001 — İniş sonrası telemetri süresi ✅ DOĞRULANDI
- **Kanıt:** Şartname §1.3 s.7: "yere iniş yaptıktan sonra **1 dk boyunca** ... 1
  dakika sonunda veri iletimi otomatik olarak sonlandırılacaktır." — Gereksinim-27
  s.13: "iniş yaptıktan sonra **10 saniye boyunca** telemetri devam etmelidir."
- **Çözüm:** `post_landing_telemetry_seconds` **config parametresi**. Varsayılan =
  **10** (gereksinim tablosu esas). CDR/hakem sürecinde netleştirilmek üzere
  işaretlendi. 60 sn'ye kolayca çekilebilir.

### CONFLICT-002 — Uydu statüsü kodları ✅ DOĞRULANDI
- **Kanıt:** Şartname §2.4 s.16: `2: Model Uydu İniş`, `3: Ayrılma`. PDR s.62
  telemetri tablosu: `2 Ayrılma`, `3 Model Uydu İniş` (**TERS**).
- **Çözüm:** **ŞARTNAME ESAS**. FSW eşleme tablosu: 2=Model Uydu İniş, 3=Ayrılma.
  PDR/CDR'da düzeltilmesi gerektiği raporlanacak. Kod içinde tek doğruluk kaynağı
  `config` + `SatelliteStatus` enum'dur.

### CONFLICT-003 — Hata kodu hane sayısı ✅ DOĞRULANDI
- **Kanıt:** Şartname §2.4 s.16: "<HATA KODU> ... **5 haneli** telemetri verisidir."
  Ancak §2.2 s.13-14 yalnızca **4 denetim koşulu** tanımlar ve örnekler `<0000>`,
  `<0100>`, `<0001>` (**4 hane**). PDR s.63 örnek paketinde de `0000` (4 hane).
- **Çözüm:** `error_code_digits` **config parametresi**. Varsayılan = **4** (ARAS
  bit tanımıyla tutarlı). 5. hane genişletilebilir bırakıldı: kod, bit sayısından
  bağımsız olarak `error_code_digits` genişliğinde sıfır-dolgulu üretir. Hakem
  sürecinde netleştirilecek.

### CONFLICT-004 — Taşıyıcı+GY pasif iniş hızı ✅ DOĞRULANDI
- **Kanıt:** Şartname §1.3 s.7 metin ve Gereksinim-5 s.11: **12–14 m/s**.
  Tablo 1 s.7: **12–16 m/s**.
- **Etki:** FSW pasif fazı doğrudan sürmez; ancak faz tespiti/ARAS için eşik
  gerekir. **Çözüm:** `carrier_descent_speed_range = (12.0, 16.0)` (toleranslı üst
  sınır) config'e alındı; işaretlendi. ARAS Bit-1 yalnızca **görev yükü** 8–10 m/s
  aralığını denetler (şartname §2.2 açık) — bu çelişkiden etkilenmez.

### CONFLICT-005 — Programlama dili / hedef platform ✅ DOĞRULANDI
- **Kanıt:** PDR s.80 FSW: "Programlama Dilleri: **C / C++**, VS Code + Arduino
  IDE." PDR s.90 yer istasyonu: **Python + PyQt5**. Görev bilgisayarı RPi 5 (s.6).
- **Çözüm (ADR-001):** Hedef, **RPi 5 üzerindeki üst seviye Görev Yazılımıdır** →
  **Python 3** seçildi (hızlı geliştirme, masaüstü simülasyon, güçlü test
  ekosistemi, pymavlink uyumu). Zaman-kritik stabilizasyon PID'i PixMin/STM32'de
  C/C++ kalır ve `FlightControllerLink` HAL'i üzerinden sürülür. Gerekçe ADR-001.

## Eksik Bilgiler (EKSİK)

### EKSİK-001 — RPi 5 ↔ PixMin protokolü ✅ DOĞRULANDI (belgede yok)
- **Kanıt:** PDR'de "MAVLink" / "MSP" / "pymavlink" **hiç geçmiyor** (arama: 0
  eşleşme). İşlemciler arası bağ için yalnızca üst seviye kutu diyagramları var.
- **Çözüm:** Soyut `FlightControllerLink` arayüzü tanımlandı. Protokol
  **ASSUMPTION-001** ile MAVLink önerildi; veri sözleşmesi HAL'de netleştirildi.

### EKSİK-002 — Düşük seviye parametreler ✅ DOĞRULANDI (belgede yok)
- LoRa E22 baud/air-rate/kanal, sensör I2C adresleri, SD dosya sistemi düzeni
  kaynaklarda yok. **Çözüm:** Makul varsayımlarla config'e parametre olarak kondu
  (ASSUMPTION-002..005). Mock/simülasyon bunları kullanır.

### EKSİK-003 — Kalkış irtifası / basınç referansı
- Uçuş günü bırakma irtifası değişebilir (Şartname s.7 dipnot). Yükseklik
  kalkışta sıfırlanır (PDR s.90). **Çözüm:** başlangıç barometre sıfırlama
  prosedürü config + runtime'da (ASSUMPTION-006).

## Mühendislik Varsayımları (ASSUMPTION)

| ID | Varsayım | Gerekçe | Nerede |
|----|----------|---------|--------|
| ASSUMPTION-001 | RPi↔PixMin protokolü MAVLink | Endüstri standardı, pymavlink | `FlightControllerLink`, config |
| ASSUMPTION-002 | LoRa E22 baud=9600, air-rate=2.4k | E22 tipik varsayılanı | config `telemetry` |
| ASSUMPTION-003 | Ana döngü 20 Hz (0.05 s), telemetri 1 Hz | 1 Hz TLM zorunlu; kontrol daha yüksek | config `loop_hz` |
| ASSUMPTION-004 | İniş fazı tespiti: yükseklik azalıyor + faz≥ayrılma | APAM'ı yükselmede kilitlemek için | failsafe |
| ASSUMPTION-005 | Batarya düşük eşiği 3.5 V/hücre (4S=14.0 V) | LiPo güvenli alt sınır | config `power` |
| ASSUMPTION-006 | Kalkışta baro sıfırlanır; 0 m referansı kaydedilir | Şartname yükseklik tanımı | persistence/config |
| ASSUMPTION-007 | Simülasyonda GPS 6+ uydu kilidi nominal | Test kriteri (açık alan min 6) | mock GPS |
| ASSUMPTION-008 | İniş sonrası "yere temas" eşiği: yükseklik≤2 m ve \|hız\|<1 m/s, kısa süre | Kurtarma statüsü (5) geçişi | state machine |
| ASSUMPTION-009 | Sensör veri yaşı eşiği 0.5 s (2× TLM periyodu değil, daha sıkı) | Bayat veri tespiti | health monitor |
| ASSUMPTION-010 | Hovering hedef irtifa 200 m AGL, ±? band config | BONUS-1 tanımı | config `mission` |

Not: Tüm sabitler koda GÖMÜLMEDİ; `config/` altında parametre olarak tutulur.

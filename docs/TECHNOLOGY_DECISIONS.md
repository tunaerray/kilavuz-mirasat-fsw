# Teknoloji Kararları (TECHNOLOGY_DECISIONS)

| Alan | Karar | Gerekçe | Referans |
|------|-------|---------|----------|
| FSW dili | Python 3 (≥3.10) | RPi 5 üst seviye görev yazılımı; hızlı geliştirme/test | ADR-001, CONFLICT-005 |
| Test | pytest (+ pytest-timeout) | Standart, hızlı, deterministik saat ile | REQ-TEST-* |
| Statik analiz | pyflakes / py_compile (min. bağımlılık) | Ortamda garanti; ruff varsa tercih | coding standards |
| Kalıcılık | Atomik JSON dosyası (tmp+os.replace) | RPi'da SD üstünde restart-güvenli; DB gereksiz | REQ-TLM-003/004 |
| Telemetri kaydı | CSV (başlık+birim satırı) | Şartname §2.4 CSV; %2 kesinti önlemi | REQ-TLM-005/006 |
| FC bağlantısı | Soyut `FlightControllerLink`, öneri MAVLink | Protokol PDR'de yok (EKSİK-001) | ASSUMPTION-001 |
| Eşzamanlılık | Tek iş parçacıklı sabit periyotlu döngü | Determinizm, test edilebilirlik | REQ-SW-003 |
| Bağımlılık ilkesi | Çekirdek yalnız stdlib; sürücüler opsiyonel | Masaüstü/CI'da kurulumsuz çalışır | REQ-SW-002 |

## Çalışma Profilleri
- **SIMULATION_ONLY (varsayılan):** Tüm sürücüler mock; hiçbir GPIO/PWM/motor
  çıkışı üretilmez. Masaüstü/CI'da çalışır.
- **HARDWARE_IN_THE_LOOP / FLIGHT:** İleride gerçek sürücüler etkinleştirilir.
  Bu oturumda yalnız SIMULATION_ONLY uygulanmıştır; diğerleri config'de tanımlı
  ama sürücüleri Aşama HAL/4'e bırakılmıştır (TASK_TRACKER).

## Bağımlılıklar
- Çekirdek FSW: yalnızca Python standart kütüphanesi.
- Geliştirme: `pytest`, `pytest-timeout` (bkz. `requirements-dev.txt`).
- Gerçek donanım (ileride): `pyserial`, `pymavlink`, `smbus2`, `picamera2`
  (bkz. `requirements-hardware.txt`, henüz kullanılmıyor).

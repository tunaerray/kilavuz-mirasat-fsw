# Test Planı (TEST_PLAN)

## İlke
- Testlerde **gerçek zaman beklemesi yok**; `FakeClock` ile deterministik.
- Tüm süit saniyeler içinde tamamlanır. `pytest-timeout` (`--timeout=30`) ile korunur.

## Aşama 1 Birim & Entegrasyon Testleri
| Test dosyası | Kapsam | İlgili REQ |
|--------------|--------|-----------|
| `test_config.py` | Profil yükleme, SIMULATION_ONLY varsayılan, eşik parametreleri | REQ-SW-002 |
| `test_clock.py` | FakeClock ilerletme; monoton artış | REQ-SW-004 |
| `test_result.py` | Result ok/err; ErrorCode; sessiz başarısızlık yok | REQ-SW-005 |
| `test_persistence.py` | Paket no artışı; **restart senaryosu** (kaldığı yerden) | REQ-TLM-003/004, REQ-TEST-002 |
| `test_telemetry_packet.py` | 17 alan sırası; birimler; **örnek paketle karşılaştırma**; CSV başlık | REQ-TLM-001/006, REQ-TEST-003 |
| `test_error_code.py` (ARAS) | Bit1..Bit4; hane sayısı config; `<0000>/<0100>/<0001>` | REQ-TLM-011..015, CONFLICT-003 |
| `test_state_machine.py` | Faz geçişleri; statü kodu 0..5 eşlemesi; CONFLICT-002 | REQ-TLM-007 |
| `test_mock_sensors.py` | Nominal/aykırı/timeout üretimi | REQ-FUNC-001 |
| `test_actuators.py` | Arm olmadan hareket reddi; safe state; SIMULATION_ONLY çıkış yok | REQ-SAFE-001/002 |
| `test_failsafe_apam.py` | 16 m/s×10 sn eşik; **sayaç sıfırlama**; >100 m; **motor-kill→paraşüt** sıralaması; link-loss tek başına tetiklemez | REQ-SAFE-003..008, CONFLICT |
| `test_health_monitor.py` | Veri yaşı/pil/link/döngü bayrakları | REQ-SAFE-009 |
| `test_app_integration.py` | Sınırlı döngü (--max-cycles); paket üretimi; CSV yazımı; determinizm | REQ-SW-003/006 |

## Çalıştırma Komutları
```
python -m pytest -q --timeout=30
python -m py_compile <tüm src>        # derleme/statik doğrulama
python -m pyflakes src tests          # statik analiz (varsa)
python -m src.app.main --config simulation --max-cycles 100
```

## İleri Aşama Sistem Testleri (FRR — Aşama 5)
- 10G şok dayanımı sırasında sistem açık ve veri iletiyor (Şartname G-12).
- 150–200 Hz titreşim testi boyunca telemetri kesintisiz.
- Düşme testi: sistem açık, veri iletiyor.
- Yer istasyonundan ayrılma komutu testi (Şartname §4.2).
- Z.I.R.H kesinti bölgesi senaryosu: kayıp veriler store-and-forward ile iletiliyor.
Bunlar donanım gerektirir; Aşama 1'de **kapsam dışıdır** (planlandı).

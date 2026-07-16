# KILAVUZ MİRASAT — Uçuş Yazılımı (FSW)

[![CI](https://github.com/tunaerray/kilavuz-mirasat-fsw/actions/workflows/ci.yml/badge.svg)](https://github.com/tunaerray/kilavuz-mirasat-fsw/actions/workflows/ci.yml)

11. TÜRKSAT Model Uydu Yarışması 2026 — Konsept **SİGMA**. Takım No: **947450**.

**Depo:** https://github.com/tunaerray/kilavuz-mirasat-fsw (private)

> Not: Depo private olduğundan rozet görseli yalnız erişimi olan/oturum açmış
> kullanıcılara render olur.

Bu depo, görev yükünün **Raspberry Pi 5** üzerindeki üst seviye **Görev
Yazılımıdır** (durum makinesi, telemetri, kalıcılık, güvenlik/APAM mantığı, komut
ve bonus görev yönetimi). Zaman-kritik stabilizasyon PID'i uçuş kontrol kartında
(PixMin/STM32) kalır ve `FlightControllerLink` HAL'i üzerinden sürülür (ADR-001).

> ⚠️ **Güvenlik:** Varsayılan profil `SIMULATION_ONLY`. Bu profilde hiçbir gerçek
> motor/servo/APAM çıkışı üretilmez; aktüatörler yalnız komut loglar.

## Hızlı Başlangıç
```bash
# Geliştirme bağımlılıkları
python -m pip install -r requirements-dev.txt

# Testler (deterministik, saniyeler içinde)
python -m pytest -q --timeout=30

# Simülasyonu sınırlı çevrimle çalıştır (asla sonsuz döngü)
python -m src.app.main --config simulation --max-cycles 100
python -m src.app.main --config simulation --duration 5
```

## Klasör Yapısı
| Yol | Amaç |
|-----|------|
| `config/` | Çalışma profilleri ve parametreler (SIMULATION varsayılan) |
| `docs/` | Kaynak analizi, gereksinimler, mimari, ADR, güvenlik, test planı |
| `src/common/` | Result/ErrorCode, Clock (cross-cutting çekirdek) |
| `src/app/` | Sınırlı ana uygulama döngüsü |
| `src/mission/` | Görev orkestrasyonu (iskelet) |
| `src/state_machine/` | Uçuş durum makinesi + statü kodu eşlemesi |
| `src/control/` | Kontrol/navigasyon (Aşama 2 iskeleti) |
| `src/telemetry/` | 17 alanlı paket, ARAS hata kodu, CSV/telemetri servisi |
| `src/services/` | Kalıcılık, sağlık izleme, failsafe/APAM |
| `src/hal/` | Donanım soyutlama arayüzleri |
| `src/drivers/` | Mock sensör/aktüatör + deterministik uçuş profili |
| `tests/` | Birim ve entegrasyon testleri |
| `simulation/` | Simülasyon senaryo yardımcıları |
| `tools/` | Yardımcı betikler |

## Belgeler
Başlangıç: [`docs/SOURCE_ANALYSIS.md`](docs/SOURCE_ANALYSIS.md),
[`docs/REQUIREMENTS.md`](docs/REQUIREMENTS.md),
[`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md),
[`docs/ASSUMPTIONS_AND_CONFLICTS.md`](docs/ASSUMPTIONS_AND_CONFLICTS.md),
[`docs/adr/ADR-001-language-and-target-platform.md`](docs/adr/ADR-001-language-and-target-platform.md),
[`docs/DEVELOPMENT_PLAN.md`](docs/DEVELOPMENT_PLAN.md).

Donanıma geçiş: [`docs/HARDWARE_BRINGUP.md`](docs/HARDWARE_BRINGUP.md) ·
[`docs/PREFLIGHT_CHECKLIST.md`](docs/PREFLIGHT_CHECKLIST.md) ·
[`docs/FRR_TEST_PROCEDURES.md`](docs/FRR_TEST_PROCEDURES.md).

## Durum
Aşama 1 (çekirdek iskelet) uygulanmıştır. Yol haritası: `docs/DEVELOPMENT_PLAN.md`.
Açık işler: `TASK_TRACKER.md`.

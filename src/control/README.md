# src/control

Kontrol & Navigasyon katmanı (Aşama 2 — uygulandı):
- `estimator.py` — sensör füzyonu (baro AGL irtifa, filtreli dikey hız, IMU
  yönelim, baro↔GPS tutarlılık ve aykırı reddi). REQ-CTRL-001.
- `pid.py` — anti-windup + türev-ölçüm-üzerinden genel PID. REQ-CTRL-002 temeli.
- `descent_controller.py` — faz bazlı hedef hız seçimi ve PID→throttle üretimi;
  aktif iniş (8–10 m/s), askı (0 m/s) ve son yaklaşma (son 50 m, RPM artışı).
  REQ-CTRL-002/005, Gereksinim-14.

Bu katman `StateEstimator` çıktısını üretir; ana döngü bunu failsafe, durum
makinesi ve telemetriye dağıtır. Motor komutları arm interlock ile mock
aktüatörlere ve `SimulatedFlightControllerLink`'e uygulanır (SIMULATION_ONLY).

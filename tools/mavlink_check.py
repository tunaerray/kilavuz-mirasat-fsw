"""
Görevi        : Mini Pix (Pixhawk/ArduPilot) MAVLink veri akışı DOĞRULAMA aracı.
                RPi üzerinde çalıştırılır; MavlinkSource ile bağlanır, akışı boşaltır
                (pump) ve baro/IMU/GPS/batarya + yönelim değerlerini periyodik basar.
Neden Gerekli : Tam uçuş döngüsüne girmeden "Mini Pix → RPi verisi geliyor mu?"
                sorusunu tek başına cevaplar (devreye alma Aşama A, HARDWARE_BRINGUP).
                Üretim FSW ile AYNI sürücüyü (src/drivers/mavlink_source.py) kullanır;
                yani burada çalışan veri yolu uçuşta da çalışır.
Nasıl Çalışır : python -m tools.mavlink_check [--port /dev/ttyACM0] [--baud 115200]
                                              [--hz 2] [--duration 0]
                --duration 0 → Ctrl+C'ye kadar sürer. Donanım/pymavlink yoksa açık
                hata basıp çıkar (sessiz başarı yok).
DÜRÜSTLÜK NOTU: Gerçek MAVLink G/Ç fiziksel Mini Pix + pymavlink gerektirir; bu ortamda
                cihaz YOKTUR. Veri gelmiyorsa her alan "—" (UNAVAILABLE) gösterir; bu,
                ArduPilot stream/GPS/battery ayarını veya kabloyu işaret eder.
"""
from __future__ import annotations

import argparse
import time

from config.default import PixhawkConfig
from src.common.clock import RealClock
from src.drivers.mavlink_source import (
    MavlinkBarometer,
    MavlinkBattery,
    MavlinkFlightControllerLink,
    MavlinkGps,
    MavlinkImu,
    MavlinkSource,
)


def _fmt(result, render) -> str:
    """Result okunur satıra çevirir; hata ise '—' + hata kodu gösterir."""
    if result.is_ok:
        return render(result.unwrap())
    return f"— ({result.code.value})"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Mini Pix MAVLink sensör akışı doğrulama aracı")
    parser.add_argument("--port", default=None,
                        help="Seri port (varsayılan: config PixhawkConfig.port)")
    parser.add_argument("--baud", type=int, default=None,
                        help="Baud (varsayılan: config PixhawkConfig.baud)")
    parser.add_argument("--hz", type=float, default=2.0,
                        help="Ekrana basma frekansı (varsayılan 2 Hz)")
    parser.add_argument("--duration", type=float, default=0.0,
                        help="Süre (sn); 0 = Ctrl+C'ye kadar")
    args = parser.parse_args(argv)

    cfg = PixhawkConfig()
    if args.port is not None:
        cfg = PixhawkConfig(port=args.port, baud=args.baud or PixhawkConfig().baud)
    elif args.baud is not None:
        cfg = PixhawkConfig(port=PixhawkConfig().port, baud=args.baud)

    clock = RealClock()
    source = MavlinkSource(cfg, clock)
    opened = source.open()
    if opened.is_err:
        print(f"HATA: MAVLink kaynağı açılamadı — {opened.message}")
        print(f"  Port: {cfg.port}  Baud: {cfg.baud}")
        print("  Kontrol: kablo, doğru port (ls /dev/tty*), pymavlink kurulu mu, "
              "başka program portu tutuyor mu (Mission Planner vb.).")
        return 1

    print(f"Bağlandı: {cfg.port} @ {cfg.baud}. Veri bekleniyor... (Ctrl+C ile çık)")
    baro = MavlinkBarometer(source)
    imu = MavlinkImu(source)
    gps = MavlinkGps(source)
    batt = MavlinkBattery(source)
    fc = MavlinkFlightControllerLink(source, clock)

    period = 1.0 / args.hz if args.hz > 0 else 0.5
    t0 = clock.now_monotonic()
    total = 0
    try:
        while True:
            total += source.pump()   # akışı boşalt → cache güncelle
            line = " | ".join([
                _fmt(baro.read(), lambda r: f"Baro {r.pressure_pa/100:.1f}hPa {r.temperature_c:.1f}C"),
                _fmt(imu.read(), lambda r: f"Att p{r.pitch_deg:+.1f} r{r.roll_deg:+.1f} y{r.yaw_deg:+.1f}"),
                _fmt(gps.read(), lambda r: f"GPS {r.latitude:.5f},{r.longitude:.5f} {r.altitude_m:.0f}m sat{r.satellites} fix{r.fix_valid}"),
                _fmt(batt.read(), lambda r: f"Bat {r.voltage_v:.2f}V"),
                _fmt(fc.read_telemetry(), lambda r: f"FC ok{r.healthy}"),
            ])
            print(f"[{clock.now_monotonic()-t0:6.1f}s | msg {total:5d}] {line}")

            if args.duration > 0 and (clock.now_monotonic() - t0) >= args.duration:
                break
            time.sleep(period)
    except KeyboardInterrupt:
        print("\nDurduruldu.")
    finally:
        source.close()

    if total == 0:
        print("UYARI: Hiç MAVLink mesajı alınmadı. ArduPilot akış hızları (SR* / "
              "SET_MESSAGE_INTERVAL), doğru baud ve kabloyu kontrol et.")
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

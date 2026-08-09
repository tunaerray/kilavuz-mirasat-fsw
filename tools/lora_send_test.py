"""
Görevi        : LoRa E22 gönderim DOĞRULAMA aracı. RPi'den, FSW ile AYNI formatta
                (17 alan CSV + CRC16 çerçeve) örnek telemetri paketleri yollar; yer
                istasyonu bunları alıp arayüzde gösteriyor mu diye test edilir.
Neden Gerekli : Tam uçuş döngüsüne girmeden "RPi → LoRa → yer istasyonu" hattını tek
                başına doğrular (devreye alma, HARDWARE_BRINGUP). Üretim FSW ile aynı
                TelemetryPacketBuilder + build_frame kullanır; yani burada geçen format
                uçuşta da geçer.
Nasıl Çalışır : python -m tools.lora_send_test [--port /dev/serial0] [--baud 9600]
                                              [--count 0] [--interval 1.0]
                --count 0 → Ctrl+C'ye kadar. Yer istasyonunda paketler görünmeli.
DÜRÜSTLÜK NOTU: Gerçek seri G/Ç + pyserial gerektirir. Port açılamazsa açık hata basar.
                Değerler örnektir (sensör değil); amaç RF taşıma + format uyumu testi.
"""
from __future__ import annotations

import argparse
import math
import time
from datetime import datetime, timezone

from config.default import TelemetryConfig
from src.telemetry.framing import build_frame
from src.telemetry.packet import (
    SatelliteStatus,
    TelemetryFields,
    TelemetryPacketBuilder,
)


def _sample_fields(cfg: TelemetryConfig, n: int) -> TelemetryFields:
    """Değişen (canlı görünsün diye) örnek 17 alan üretir."""
    return TelemetryFields(
        packet_number=n,
        status=SatelliteStatus.READY,
        error_code="0000".rjust(cfg.error_code_digits, "0"),
        send_time=datetime.now(timezone.utc),
        pressure_pa=101325.0 + 50.0 * math.sin(n / 5.0),
        altitude_m=max(0.0, 100.0 * math.sin(n / 10.0)),
        descent_speed_mps=0.0,
        temperature_c=25.0,
        battery_v=16.4 - n * 0.001,
        gps_lat=39.9255,
        gps_lon=32.8663,
        gps_alt_m=850.0,
        pitch_deg=10.0 * math.sin(n / 4.0),
        roll_deg=5.0 * math.cos(n / 4.0),
        yaw_deg=(n * 3) % 360,
        rhrhrh="",
        team_number=947450,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="LoRa E22 gönderim doğrulama (FSW formatıyla örnek paket)")
    parser.add_argument("--port", default=None,
                        help="Seri port (varsayılan: config lora_port = /dev/serial0)")
    parser.add_argument("--baud", type=int, default=None,
                        help="Baud (varsayılan: config lora_baud = 9600)")
    parser.add_argument("--count", type=int, default=0,
                        help="Gönderilecek paket sayısı; 0 = Ctrl+C'ye kadar")
    parser.add_argument("--interval", type=float, default=1.0,
                        help="Paketler arası süre (sn); şartname 1 Hz")
    args = parser.parse_args(argv)

    cfg = TelemetryConfig()
    port = args.port or cfg.lora_port
    baud = args.baud or cfg.lora_baud

    try:
        import serial  # type: ignore
    except ImportError:
        print("HATA: pyserial kurulu değil (pip install -r requirements-hardware.txt)")
        return 1
    try:
        ser = serial.Serial(port, baud, timeout=1)
    except Exception as exc:
        print(f"HATA: LoRa portu açılamadı ({port} @ {baud}): {exc}")
        print("  Kontrol: doğru port (ls -l /dev/serial*), UART etkin mi "
              "(raspi-config), başka program tutuyor mu.")
        return 1

    builder = TelemetryPacketBuilder(decimal_places=cfg.decimal_places,
                                     separator=cfg.field_separator)
    print(f"Gönderiliyor: {port} @ {baud}  (Ctrl+C ile çık)")
    print("Yer istasyonunda paketlerin göründüğünü doğrula.")
    n = 0
    try:
        while args.count == 0 or n < args.count:
            n += 1
            payload = builder.build(_sample_fields(cfg, n))
            frame = build_frame(payload)               # <payload>*<CRC>
            ser.write((frame + "\n").encode("utf-8"))  # RealLoraE22Link ile aynı
            print(f"[{n:4d}] {frame}")
            time.sleep(args.interval)
    except KeyboardInterrupt:
        print("\nDurduruldu.")
    finally:
        ser.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

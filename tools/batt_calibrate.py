"""
Görevi        : ArduPilot batarya voltaj çarpanı (BATT_VOLT_MULT) kalibrasyon aracı.
                Multimetreyle ölçülen gerçek voltajı alır, FC'nin okuduğu voltajla
                karşılaştırıp yeni çarpanı hesaplar ve yazar (reboot gerekmez).
Neden Gerekli : Power module varsayılan çarpanı gerçek donanımda sapabilir; şartname
                PIL_GERILIMI alanı doğru olmalı (batarya güvenliği + puan). Mission
                Planner yoksa RPi'den kalibrasyon için pratik yol.
Nasıl Çalışır : python -m tools.batt_calibrate --real-volts 16.37
                                              [--port /dev/ttyACM0] [--baud 115200]
                BATT_MONITOR kapalıysa (voltaj 0) önce açılmalı; araç uyarır.
DÜRÜSTLÜK NOTU: Gerçek MAVLink/pymavlink ve fiziksel FC gerektirir. Voltaj okunamazsa
                (0) veya çarpan alınamazsa açık hata basıp çıkar (sessiz başarı yok).
"""
from __future__ import annotations

import argparse
import time


def _read_param(m, name: str, timeout_s: float = 6.0):
    """Bir parametreyi okur (birkaç kez ister; ArduPilot yanıtı gecikebilir)."""
    deadline = time.time() + timeout_s
    m.mav.param_request_read_send(m.target_system, m.target_component,
                                  name.encode(), -1)
    last_req = time.time()
    while time.time() < deadline:
        msg = m.recv_match(type="PARAM_VALUE", blocking=True, timeout=1)
        if msg and msg.param_id == name:
            return float(msg.param_value)
        if time.time() - last_req > 1.5:   # yanıt yoksa tekrar iste
            m.mav.param_request_read_send(m.target_system, m.target_component,
                                          name.encode(), -1)
            last_req = time.time()
    return None


def _read_voltage(m, timeout_s: float = 5.0):
    """SYS_STATUS'tan güncel batarya voltajını (V) okur."""
    from pymavlink import mavutil
    m.mav.request_data_stream_send(m.target_system, m.target_component,
                                   mavutil.mavlink.MAV_DATA_STREAM_ALL, 5, 1)
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        msg = m.recv_match(type="SYS_STATUS", blocking=True, timeout=1)
        if msg and msg.voltage_battery not in (0, 65535):
            return msg.voltage_battery / 1000.0
    return None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="BATT_VOLT_MULT kalibrasyon aracı (ArduPilot)")
    parser.add_argument("--real-volts", type=float, required=True,
                        help="Multimetreyle ölçülen GERÇEK batarya voltajı (ör. 16.37)")
    parser.add_argument("--port", default="/dev/ttyACM0")
    parser.add_argument("--baud", type=int, default=115200)
    args = parser.parse_args(argv)

    from pymavlink import mavutil
    m = mavutil.mavlink_connection(args.port, baud=args.baud)
    print("Heartbeat bekleniyor...")
    if m.wait_heartbeat(timeout=10) is None:
        print("HATA: heartbeat yok — FC bağlı değil / yanlış port.")
        return 1
    print(f"FC bağlı (sys {m.target_system}).")

    old_mult = _read_param(m, "BATT_VOLT_MULT")
    if old_mult is None:
        print("HATA: BATT_VOLT_MULT okunamadı (FC yanıt vermedi).")
        return 1

    read_v = _read_voltage(m)
    if read_v is None or read_v <= 0:
        print("HATA: FC voltaj okumuyor (BATT_MONITOR kapalı olabilir). "
              "Önce BATT_MONITOR=4 yapıp FC'yi yeniden başlat.")
        return 2

    new_mult = old_mult * (args.real_volts / read_v)
    print(f"eski mult = {old_mult:.3f}")
    print(f"FC okuyor = {read_v:.3f} V")
    print(f"gerçek    = {args.real_volts:.3f} V")
    print(f"YENİ mult = {new_mult:.3f}")

    m.mav.param_set_send(m.target_system, m.target_component,
                         b"BATT_VOLT_MULT", new_mult,
                         mavutil.mavlink.MAV_PARAM_TYPE_REAL32)
    time.sleep(1.0)

    # Yazıldı mı + yeni voltaj ne?
    check_mult = _read_param(m, "BATT_VOLT_MULT")
    check_v = _read_voltage(m)
    print("-" * 40)
    print(f"yazılan mult (teyit) = {check_mult}")
    print(f"yeni okunan voltaj   = {check_v} V")
    if check_v is not None and abs(check_v - args.real_volts) < 0.5:
        print("✓ Kalibrasyon başarılı (gerçek voltajla uyumlu).")
        return 0
    print("UYARI: değer hâlâ sapıyorsa power module/pin ayarını kontrol et.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

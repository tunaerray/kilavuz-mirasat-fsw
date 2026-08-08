"""
Görevi        : Taşıyıcı→görev yükü AYRILMA mekanizması tezgah testi (RPi + PCA9685).
                İki zıt yönlü ayrılma servosunu EŞZAMANLI açar, ayrılma onayından
                sonra `SEP_TO_WINGS_DELAY_S` gecikmeyle 3. servo (kanat açma) sürer.
                Uçuş yazılımından BAĞIMSIZ; yalnız mekanizmayı doğrulamak içindir.
Neden Gerekli : docs/HARDWARE_BRINGUP Aşama B — servolar (ayrılma, kol/kanat) PCA9685
                üzerinde tek tek ve dizi olarak doğrulanmalı. FSW artık ayrılmayı 2 zıt
                servo + geri bildirimle modelliyor (SeparationSequencer); bu betik aynı
                diziyi FİZİKSEL PCA9685'te doğrular (eşzamanlılık + gecikme ölçümü).
İlişkiler     : smbus2 ile PCA9685'e (0x40) doğrudan PWM yazar (requirements-hardware).
                Gerçek FSW'ye dokunmaz. Mock/dry-run modunda donanımsız da çalışır.
DÜRÜSTLÜK NOTU: Gerçek I²C/PWM fiziksel PCA9685 ve smbus2 gerektirir. Bu ortamda
                cihaz YOKTUR. smbus2/bus yoksa SESSİZCE ÇÖKMEZ; açık hata verir ya da
                --dry-run ile yalnız komut planını yazar (RPi'de gerçek doğrulama şart).

GÜVENLİK:
  - Test sırasında taşıyıcı-yük bağını masaya SABİTLE; ayrılma parçalarını elle tut.
  - Önce endpoint'leri (LOCKED/OPEN PWM) DÜŞÜK açı farkıyla dene; mekaniği zorlama.
  - Betik başlangıçta ve çıkışta tüm servoları GÜVENLİ (LOCKED) konuma alır.

KULLANIM (RPi'de):
  python tools/separation_bench_test.py --lock                 # hepsini güvenli konuma al
  python tools/separation_bench_test.py --channel 0 --us 1500  # tek servo elle konumla
  python tools/separation_bench_test.py --separate             # tam ayrılma dizisi (1 kez)
  python tools/separation_bench_test.py --separate --repeat 20 # güvenilirlik (20 tekrar)
  python tools/separation_bench_test.py --separate --dry-run   # donanımsız komut planı (laptop)

AYAR: Aşağıdaki KANAL ve PWM sabitlerini KENDİ mekaniğine göre ölçüp güncelle.
"""
from __future__ import annotations

import argparse
import sys
import time

# ─────────────────────────── AYARLANACAK SABİTLER ───────────────────────────
# PCA9685 kanal numaraları (0..15). Servolarını hangi çıkışa taktıysan.
CH_SEP_LEFT = 0        # sol ayrılma servosu
CH_SEP_RIGHT = 1       # sağ ayrılma servosu (zıt yön)
CH_WINGS = 2           # 3. servo — kanat açma (kod: SİGMA kol mekanizması)

# Her servo için LOCKED (kilitli/güvenli) ve OPEN (açık) darbe genişliği [mikrosaniye].
# Tipik servo: 1000–2000 µs. ZIT servolar için OPEN yönleri ters olabilir — ölçerek gir.
SERVO_US = {
    CH_SEP_LEFT:  {"locked": 1000, "open": 2000},
    CH_SEP_RIGHT: {"locked": 2000, "open": 1000},   # zıt yön → ters uçlar
    CH_WINGS:     {"locked": 1000, "open": 2000},
}

SEP_TO_WINGS_DELAY_S = 1.5     # ayrılma → kanat açma gecikmesi (kod: arm_deploy_duration_s)
SETTLE_S = 0.6                 # bir hareketin oturması için bekleme
REPEAT_GAP_S = 1.0            # tekrarlar arası bekleme

# PCA9685 I²C
I2C_BUS = 1
PCA9685_ADDR = 0x40
PWM_FREQ_HZ = 50.0            # analog servo standardı
# ─────────────────────────────────────────────────────────────────────────────

# PCA9685 register haritası
_MODE1 = 0x00
_PRESCALE = 0xFE
_LED0_ON_L = 0x06
_PERIOD_US = 1_000_000.0 / PWM_FREQ_HZ    # 50 Hz → 20000 µs


def _us_to_counts(pulse_us: float) -> int:
    """Darbe genişliğini (µs) 12-bit PCA9685 sayımına (0..4095) çevirir."""
    counts = int(round(4096.0 * pulse_us / _PERIOD_US))
    return max(0, min(4095, counts))


class Pca9685:
    """
    Minimal PCA9685 servo sürücüsü (smbus2). `open()` çağrılana dek bağlı değildir;
    smbus2/bus yoksa SESSİZCE ÇÖKMEZ, açık hata metni tutar (real_lora deseni).
    Dry-run modunda donanıma hiç dokunmadan komutları planlar.
    """

    def __init__(self, dry_run: bool = False, log=print) -> None:
        self._dry = dry_run
        self._log = log
        self._bus = None
        self.error: str | None = None

    def open(self) -> bool:
        if self._dry:
            self._log(f"[DRY] PCA9685 @0x{PCA9685_ADDR:02X}, {PWM_FREQ_HZ:.0f} Hz (donanım yok)")
            return True
        try:
            from smbus2 import SMBus  # type: ignore  # yalnız RPi/donanım profilinde
        except ImportError:
            self.error = "smbus2 kurulu değil (pip install -r requirements-hardware.txt)"
            return False
        try:
            self._bus = SMBus(I2C_BUS)
            self._init_chip()
        except Exception as exc:  # I²C/bus hataları — açık raporla, çökme yok
            self.error = f"PCA9685 açılamadı (I2C-{I2C_BUS} @0x{PCA9685_ADDR:02X}): {exc}"
            return False
        return True

    def _init_chip(self) -> None:
        prescale = int(round(25_000_000.0 / (4096.0 * PWM_FREQ_HZ)) - 1)
        self._bus.write_byte_data(PCA9685_ADDR, _MODE1, 0x10)          # SLEEP
        self._bus.write_byte_data(PCA9685_ADDR, _PRESCALE, prescale)   # frekans
        self._bus.write_byte_data(PCA9685_ADDR, _MODE1, 0x00)          # WAKE
        time.sleep(0.005)
        self._bus.write_byte_data(PCA9685_ADDR, _MODE1, 0xA0)          # AI + RESTART

    def set_us(self, channel: int, pulse_us: float) -> None:
        """Bir kanala darbe genişliği uygular (dry-run'da yalnız loglar)."""
        counts = _us_to_counts(pulse_us)
        if self._dry or self._bus is None:
            self._log(f"[{'DRY' if self._dry else '??'}] CH{channel} <- {pulse_us:.0f} us "
                      f"({counts} sayim)")
            return
        base = _LED0_ON_L + 4 * channel
        # ON=0, OFF=counts → darbe 0'dan başlar, counts'ta biter.
        self._bus.write_byte_data(PCA9685_ADDR, base + 0, 0)
        self._bus.write_byte_data(PCA9685_ADDR, base + 1, 0)
        self._bus.write_byte_data(PCA9685_ADDR, base + 2, counts & 0xFF)
        self._bus.write_byte_data(PCA9685_ADDR, base + 3, counts >> 8)

    def off(self, channel: int) -> None:
        """
        Kanala PWM sinyalini tamamen keser (LEDn_OFF 'full-off' biti). Sinyal
        gidince servo komut almaz → sürekli dönen servo DURUR, normal servo gevşer.
        Kart komutu 'hatırladığından', durdurmanın tek temiz yolu sinyali kesmektir.
        """
        if self._dry or self._bus is None:
            self._log(f"[{'DRY' if self._dry else '??'}] CH{channel} sinyal KESILDI (off)")
            return
        base = _LED0_ON_L + 4 * channel
        self._bus.write_byte_data(PCA9685_ADDR, base + 0, 0)      # ON_L
        self._bus.write_byte_data(PCA9685_ADDR, base + 1, 0)      # ON_H
        self._bus.write_byte_data(PCA9685_ADDR, base + 2, 0)      # OFF_L
        self._bus.write_byte_data(PCA9685_ADDR, base + 3, 0x10)   # OFF_H: full-off biti

    def close(self) -> None:
        if self._bus is not None:
            try:
                self._bus.close()
            except Exception:
                pass


def all_locked(pca: Pca9685) -> None:
    """Tüm servoları GÜVENLİ (LOCKED) konuma alır — başlangıç ve çıkış için."""
    for ch, ends in SERVO_US.items():
        pca.set_us(ch, ends["locked"])


def all_off(pca: Pca9685) -> None:
    """Tüm kanallarda PWM sinyalini keser (tüm servoları durdurur)."""
    for ch in SERVO_US:
        pca.off(ch)


def separate_sequence(pca: Pca9685, log=print) -> None:
    """
    Tam ayrılma dizisi:
      1) İki zıt ayrılma servosunu EŞZAMANLI OPEN'a al (art arda, minimum gecikme).
      2) SEP_TO_WINGS_DELAY_S bekle (ayrılmanın tamamlanması).
      3) 3. servo (kanat) OPEN → kanatları aç.
    Eşzamanlılık kritik: iki servo arası komut farkını da ölçüp raporlar.
    """
    t0 = time.perf_counter()
    log("AYRILMA: iki servo eşzamanlı OPEN...")
    pca.set_us(CH_SEP_LEFT, SERVO_US[CH_SEP_LEFT]["open"])
    t_left = time.perf_counter()
    pca.set_us(CH_SEP_RIGHT, SERVO_US[CH_SEP_RIGHT]["open"])
    t_right = time.perf_counter()
    skew_ms = (t_right - t_left) * 1000.0
    log(f"  -> sol/sağ komut farkı (skew): {skew_ms:.2f} ms "
        f"({'İYİ' if skew_ms < 5 else 'YÜKSEK — servoları eşle!'})")

    time.sleep(SEP_TO_WINGS_DELAY_S)
    log(f"KANAT: {SEP_TO_WINGS_DELAY_S:.1f} sn sonra 3. servo OPEN...")
    pca.set_us(CH_WINGS, SERVO_US[CH_WINGS]["open"])
    time.sleep(SETTLE_S)
    log(f"DİZİ TAMAM ({time.perf_counter() - t0:.2f} sn). Kontrol: 2 servo açıldı mı, "
        "yük ayrıldı mı, kanatlar açıldı mı?")


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Ayrılma mekanizması tezgah testi (RPi/PCA9685)")
    p.add_argument("--lock", action="store_true", help="Tüm servoları güvenli konuma al ve çık")
    p.add_argument("--separate", action="store_true", help="Ayrılma + kanat açma dizisini çalıştır")
    p.add_argument("--repeat", type=int, default=1, help="Diziyi N kez tekrarla (güvenilirlik)")
    p.add_argument("--channel", type=int, help="Tek kanala elle PWM (--us ile)")
    p.add_argument("--us", type=float, help="Elle darbe genişliği (mikrosaniye)")
    p.add_argument("--off", action="store_true",
                   help="PWM sinyalini kes (servo durur). --channel ile tek kanal, yoksa tümü")
    p.add_argument("--dry-run", action="store_true", help="Donanımsız: yalnız komut planını yaz")
    args = p.parse_args(argv)

    pca = Pca9685(dry_run=args.dry_run)
    if not pca.open():
        print(f"HATA: {pca.error}", file=sys.stderr)
        print("İpucu: RPi'de 'pip install -r requirements-hardware.txt' ve I2C açık mı "
              "('sudo raspi-config' → I2C ON, 'i2cdetect -y 1' 0x40 görmeli). "
              "Laptopta mantığı denemek için --dry-run kullan.", file=sys.stderr)
        return 1

    # Elle konumlama (--channel) ve sinyal-kesme (--off) modlarında servo, olduğu
    # gibi BIRAKILIR; güvenli-sıfırlama (all_locked) UYGULANMAZ, yoksa servo hemen
    # geri çekilir / sinyal tekrar verilir.
    manual = args.channel is not None
    hold = manual or args.off

    try:
        if args.off:
            if args.channel is not None:
                pca.off(args.channel)
                print(f"CH{args.channel} sinyal KESILDI — servo durur.")
            else:
                all_off(pca)
                print("TUM kanallarda sinyal kesildi — servolar durur.")
            return 0

        if manual:
            if args.us is None:
                print("HATA: --channel ile --us de vermelisin.", file=sys.stderr)
                return 2
            pca.set_us(args.channel, args.us)
            print(f"CH{args.channel} <- {args.us:.0f} us uygulandi ve KONUMDA BIRAKILDI.")
            return 0

        # GÜVENLİK: dizi/lock modlarında önce güvenli konum.
        all_locked(pca)
        time.sleep(SETTLE_S)

        if args.lock:
            print("Tüm servolar GÜVENLİ (LOCKED) konumda.")
            return 0

        if args.separate:
            ok = 0
            for i in range(1, args.repeat + 1):
                print(f"\n=== TEKRAR {i}/{args.repeat} ===")
                separate_sequence(pca)
                ok += 1
                if i < args.repeat:
                    all_locked(pca)          # bir sonraki tekrar için kur
                    time.sleep(REPEAT_GAP_S)
            print(f"\nÖZET: {ok}/{args.repeat} dizi tamamlandı. "
                  "Her tekrarda başarı/başarısızlığı ELLE kaydet (video öner).")
            return 0

        p.print_help()
        return 0
    finally:
        # Çıkışta güvenli konuma dön (mekaniği kur, yükü tut). Elle konumlama
        # modunda İSTİSNA: servo ölçüm için konumda kalmalı, sıfırlanmaz.
        if not hold:
            all_locked(pca)
        pca.close()


if __name__ == "__main__":
    raise SystemExit(main())

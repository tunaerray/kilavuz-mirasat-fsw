"""
Görevi        : DHT22 ortam sıcaklığı sürücüsü ve barometre sarmalayıcısı.
                MAVLink'ten gelen BASINÇ korunur, SICAKLIK alanı DHT22'den
                gelen ortam ölçümüyle değiştirilir.
Neden Gerekli : Gereksinim-15 ortam sıcaklığı istiyor. Uçuş kontrol kartının
                SCALED_PRESSURE.temperature alanı barometre ÇİPİNİN ısısını
                verir, ortamın değil. Sahada ölçüldü: kart 53.7 °C okurken
                ortam 27.3 °C idi — 26 °C sapma. Hakem telemetride 50+ °C
                görürse bu değerin gerçek olmadığını fark eder.
İlişkiler     : main.py FLIGHT profilinde MavlinkBarometer'ı bu sarmalayıcıyla
                sarar. Barometer arayüzü değişmez; çağıran taraf farkı görmez.
Nasıl Test    : tests/test_dht22.py — sysfs yokken güvenli degrade, önbellek
                tazeliği, okuma hatasında son geçerli değerin korunması.

Pi 5 NOTU
---------
DHT22 için Python kütüphaneleri (Adafruit Blinka, pigpio) Pi 5'te güvenilir
DEĞİL; GPIO altyapısı değişti ve protokol mikrosaniye hassasiyeti istiyor.
Bunun yerine ÇEKİRDEK SÜRÜCÜSÜ kullanılır:

    /boot/firmware/config.txt:  dtoverlay=dht11,gpiopin=4

('dht11' overlay'i DHT22'yi de destekler; isim yanıltıcıdır.)

Çekirdek bit zamanlamasını üstlenir, kullanıcı alanında yalnız dosya okunur.
Bu, yazılımsal H.264 kodlaması CPU'yu yüklerken bile okuma güvenilirliğini
korur.

Donanım: DATA ile VCC arasına 10k pull-up direnci ŞART.

NEDEN ARKA PLAN THREAD'İ
-------------------------
DHT22 en fazla 0.5 Hz okunabilir ve okuma bazen zaman aşımına uğrar. sysfs
okuması bloke edicidir; 20 Hz uçuş döngüsünden doğrudan çağrılırsa döngüyü
duraklatır. Bu yüzden okuma ayrı bir thread'de yapılır, uçuş döngüsü yalnız
önbellekten okur ve ASLA beklemez.

YERLEŞİM UYARISI
----------------
Sensör dış hava ile temas etmeli. Görev yükünün içine kapatılırsa Pi ve uçuş
kartının ısısını okur; o zaman aynı sorunu farklı bir sensörle yaşarız.
"""
from __future__ import annotations

import glob
import os
import threading
import time

from src.common.result import ErrorCode, Result
from src.hal.interfaces import BarometerReading


# DHT22 iki saniyeden sık okunamaz; 2.5 s güvenli aralık.
OKUMA_ARALIGI_S = 2.5

# Bu süreden eski ölçüm bayat sayılır ve kullanılmaz. Üç okuma denemesi
# kadar tolerans: ara sıra zaman aşımı normaldir, sürekli olması arıza.
BAYATLAMA_S = 10.0

# Makul ortam aralığı. Dışındaki değerler bozuk okuma sayılır.
# Yarışma sahası ve 1600 m irtifa bu aralığın rahat içindedir.
MIN_MAKUL_C = -40.0
MAKS_MAKUL_C = 80.0


def _dht_cihazi_bul() -> str | None:
    """
    IIO cihazları arasında DHT sensörünü bulur. Cihaz numarası açılışta
    değişebileceği için sabit yol kullanılmaz.
    """
    for yol in sorted(glob.glob("/sys/bus/iio/devices/iio:device*")):
        ad_dosyasi = os.path.join(yol, "name")
        temp_dosyasi = os.path.join(yol, "in_temp_input")
        if not os.path.exists(temp_dosyasi):
            continue
        try:
            with open(ad_dosyasi) as f:
                if "dht" in f.read().strip().lower():
                    return temp_dosyasi
        except OSError:
            continue
        # Adı okunamadıysa yine de sıcaklık dosyası varsa aday kabul et
        return temp_dosyasi
    return None


class Dht22Temperature:
    """
    Arka planda DHT22 okur, son geçerli değeri önbellekte tutar.

    `start()` çağrılmadan değer üretmez. `close()` ile thread durdurulur.
    """

    def __init__(self, temp_yolu: str | None = None) -> None:
        self._yol = temp_yolu or _dht_cihazi_bul()
        self._deger_c: float | None = None
        self._zaman: float = 0.0
        self._kilit = threading.Lock()
        self._thread: threading.Thread | None = None
        self._calisiyor = False

        self.basarili_okuma = 0
        self.basarisiz_okuma = 0

    @property
    def is_available(self) -> bool:
        return self._yol is not None

    def start(self) -> Result[None]:
        if not self.is_available:
            return Result.err(ErrorCode.UNAVAILABLE,
                              "DHT sensörü bulunamadı — dtoverlay=dht11 eklenmiş mi?")
        if self._thread is not None:
            return Result.ok(None)

        self._calisiyor = True
        self._thread = threading.Thread(target=self._dongu, daemon=True)
        self._thread.start()

        # İlk ölçümün gelmesi için kısa süre bekle; boot logunda değer görünsün.
        for _ in range(30):
            if self.read().is_ok:
                return Result.ok(None)
            time.sleep(0.1)

        return Result.ok(None)   # okuma gelmese de thread çalışıyor, uçuşu bloke etme

    def close(self) -> None:
        self._calisiyor = False
        if self._thread is not None:
            self._thread.join(timeout=2.0)
            self._thread = None

    def read(self) -> Result[float]:
        """Önbellekteki sıcaklığı döndürür. Bloke ETMEZ."""
        with self._kilit:
            deger, zaman = self._deger_c, self._zaman

        if deger is None:
            return Result.err(ErrorCode.UNAVAILABLE, "DHT22 henüz ölçüm vermedi")

        yas = time.monotonic() - zaman
        if yas > BAYATLAMA_S:
            return Result.err(ErrorCode.UNAVAILABLE,
                              f"DHT22 ölçümü bayat ({yas:.1f} s)")
        return Result.ok(deger)

    # ------------------------------------------------------------------

    def _dongu(self) -> None:
        while self._calisiyor:
            self._bir_okuma()
            # Küçük dilimlerle uyu ki close() hızlı dönsün
            bitis = time.monotonic() + OKUMA_ARALIGI_S
            while self._calisiyor and time.monotonic() < bitis:
                time.sleep(0.1)

    def _bir_okuma(self) -> None:
        try:
            with open(self._yol) as f:
                ham = f.read().strip()
        except OSError:
            # Zaman aşımı DHT22'de normaldir; son geçerli değer korunur.
            self.basarisiz_okuma += 1
            return

        try:
            derece = int(ham) / 1000.0     # çekirdek milidereceyle verir
        except ValueError:
            self.basarisiz_okuma += 1
            return

        if not (MIN_MAKUL_C <= derece <= MAKS_MAKUL_C):
            self.basarisiz_okuma += 1
            return

        with self._kilit:
            self._deger_c = derece
            self._zaman = time.monotonic()
        self.basarili_okuma += 1


class AmbientTemperatureBarometer:
    """
    Barometre sarmalayıcısı: BASINÇ iç kaynaktan (MAVLink), SICAKLIK
    DHT22'den gelir.

    DHT22 okunamazsa iç kaynağın sıcaklığına düşülür — telemetri alanı boş
    kalmaz. Bu durumda değerin çip ısısı olduğu bilinmelidir; `using_ambient`
    ile sorgulanabilir ve telemetri/loglamada belirtilebilir.
    """

    def __init__(self, inner, dht: Dht22Temperature) -> None:
        self._inner = inner
        self._dht = dht
        self._son_ortam_kullanildi = False

    @property
    def using_ambient(self) -> bool:
        """Son okumada gerçek ortam sıcaklığı kullanıldı mı?"""
        return self._son_ortam_kullanildi

    def read(self) -> Result[BarometerReading]:
        ic = self._inner.read()
        if ic.is_err:
            return ic

        okuma = ic.unwrap()
        ortam = self._dht.read()

        if ortam.is_err:
            self._son_ortam_kullanildi = False
            return ic     # çip ısısıyla devam — alan boş kalmasın

        self._son_ortam_kullanildi = True
        return Result.ok(BarometerReading(
            pressure_pa=okuma.pressure_pa,
            temperature_c=ortam.unwrap(),
            timestamp_s=okuma.timestamp_s,
        ))

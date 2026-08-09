"""
Görevi        : BONUS-2 S2D-IOT istasyonu bağı. Doğrulanmış RHRHRH şifresini
                görev yükünden IoT istasyonuna iletir. IotLink arayüzünü uygular.
Neden Gerekli : Gereksinim-37 / Şartname §2.3. SIMULATION_ONLY'de MockIotLink
                kullanılır; FLIGHT/HIL profilinde gerçek aktarım gerekir.
İlişkiler     : S2dIotService şifreyi doğrulayıp SD'ye yazdıktan sonra bu bağın
                `forward()` metodunu çağırır. Aktarım, telemetriyle AYNI LoRa
                linki üzerinden yapılır (aşağıya bakınız).

MİMARİ NOTU — NEDEN AYRI MODÜL YOK
-----------------------------------
hal/interfaces.py IotLink docstring'i "ayrı LoRa bağlantısı" varsayıyor. Saha
donanımında ikinci bir E22 ve ikinci bir UART YOK; üç düğüm (görev yükü, yer
istasyonu, IoT istasyonu) aynı kanalda, transparan modda çalışıyor.

Ayrım ÖNEK ile yapılır:

    Yer istasyonu -> Görev yükü    #ID,KOMUT,CRC
    Görev yükü    -> Yer istasyonu $ID,SONUC,CRC   (ACK)
    Görev yükü    -> IoT           @KOMUT,CRC
    Görev yükü    -> Yer istasyonu 1,4,0000,...    (telemetri, öneksiz)

'@' önekini YALNIZCA görev yükü kullanır. IoT istasyonu bu sayede yer
istasyonunu duymaz, yalnız görev yükünü dinler — şartnamenin istediği
GY→S2D akışı transparan modda da gerçekten sağlanmış olur. Aksi halde IoT,
komutu doğrudan yer istasyonundan alır ve akış şartnameye uymaz.

Bu yaklaşım fixed (adresli) moda geçmeden çalışır; ikinci modül maliyeti ve
ek UART ihtiyacı doğurmaz.

CRC: src/telemetry/framing.crc16_ccitt kullanılır — telemetri çerçevelemesiyle
AYNI algoritma. IoT istasyonundaki (ESP32) doğrulayıcı bununla eşleşir.
Ayraç farkı bilinçlidir: telemetri '<payload>*<CRC>', IoT '@<KOMUT>,<CRC>'.

DÜRÜSTLÜK NOTU: Bu bağ kendi seri portunu AÇMAZ; mevcut LoRa linkini paylaşır.
                Link kapalıysa forward() açık UNAVAILABLE döndürür. Gönderimin
                IoT istasyonuna ULAŞTIĞI burada doğrulanamaz — IoT yalnız alıcıdır
                (Şartname Tablo 2: Rx) ve geri bildirim göndermez. Ulaştığının
                kanıtı, telemetrideki RHRHRH alanının yer istasyonunda görülmesidir.
"""
from __future__ import annotations

from src.common.result import ErrorCode, Result
from src.telemetry.framing import crc16_ccitt


IOT_ONEK = "@"
IOT_AYRAC = ","


class LoraIotLink:
    """
    IoT istasyonu bağı. Telemetriyle aynı LoRa linkini paylaşır.

    Kurulum sırası önemlidir: LoRa linki `open()` edilmiş olmalıdır. Link
    nesnesi paylaşıldığı için bu sınıf onu açmaz ve kapatmaz — yaşam döngüsü
    telemetri tarafına aittir.
    """

    def __init__(self, telemetry_link) -> None:
        """
        telemetry_link: `send(str) -> Result` ve `is_connected() -> bool`
                        sağlayan LoRa bağı (RealLoraE22Link).
        """
        self._link = telemetry_link
        self._forwarded: list[str] = []

    def is_connected(self) -> bool:
        try:
            return bool(self._link.is_connected())
        except Exception:
            return False

    def forward(self, password: str) -> Result[None]:
        """
        Şifreyi '@<KOMUT>,<CRC>' biçiminde IoT istasyonuna iletir.

        Şifre doğrulaması S2dIotService'te yapılır; burada yalnız aktarım vardır.
        Yine de boş/bozuk girdi RF'e çıkmasın diye asgari kontrol yapılır.
        """
        if not password or not isinstance(password, str):
            return Result.err(ErrorCode.INVALID_DATA, "IoT şifresi boş")

        if not self.is_connected():
            return Result.err(ErrorCode.UNAVAILABLE, "LoRa linki açık değil")

        govde = password.strip().upper()
        cerceve = f"{IOT_ONEK}{govde}{IOT_AYRAC}{crc16_ccitt(govde):04X}"

        sonuc = self._link.send(cerceve)
        if not sonuc.is_ok:
            return sonuc

        self._forwarded.append(govde)
        return Result.ok(None)

    @property
    def forwarded(self) -> list[str]:
        """Bu koşuda iletilen şifreler (tanılama/test amaçlı)."""
        return list(self._forwarded)

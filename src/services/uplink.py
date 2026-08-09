"""
Görevi        : Yer istasyonundan gelen telekomutları LoRa üzerinden alır,
                bütünlüğünü doğrular, CommandService'e yönlendirir ve sonucu
                ACK olarak geri bildirir.
Neden Gerekli : Gereksinim-7 (manuel ayrılma) ve Gereksinim-10 (manuel APAM)
                uçuş sırasında yer istasyonundan komut gönderilebilmesini
                zorunlu tutar. Öncesinde komutlar yalnız `--command T:CMD`
                bayrağıyla ENJEKTE ediliyordu; gerçek RF uplink yolu yoktu.
İlişkiler     : RealLoraE22Link.receive() ham satırları verir; CommandService
                komutu yorumlar; ACK aynı link üzerinden geri gönderilir.
Nasıl Test    : tests/test_uplink.py — CRC hatası, tekrar eden ID, bilinmeyen
                komut, biçim hatası, başarılı akış.

PROTOKOL
--------
    Gelen   #<ID>,<KOMUT>,<CRC>     ornek: #7,2R0G1B,93EC
    Giden   $<ID>,<SONUC>,<CRC>     ornek: $7,OK,EEFE

    SONUC   OK   komut uygulandı
            DUP  bu ID daha önce işlendi, TEKRAR UYGULANMADI
            ERR  CRC hatası, biçim hatası veya bilinmeyen komut

CRC, önek hariç gövde üzerinden hesaplanır (framing.crc16_ccitt — telemetri
çerçevelemesiyle aynı algoritma).

NEDEN KOMUT KİMLİĞİ VE TEKRAR KORUMASI
---------------------------------------
Yer istasyonu ACK almazsa komutu tekrar gönderir. Kimlik olmadan görev yükü
aynı komutu ikinci kez uygular. Manuel APAM'da bu, paraşütün iki kez
tetiklenmesi demektir. Bu yüzden işlenen ID'ler tutulur; tekrar gelen ID
uygulanmaz, yalnız DUP yanıtı döner. Yer istasyonu böylece "ulaştı" bilgisini
alır, komut ikinci kez çalışmaz.

CommandService zaten latch mantığı kullanıyor (bir kez set edilen bayrak geri
alınmaz), yani ikinci uygulama pratikte zararsız olurdu. Yine de tekrar
koruması korunuyor: ileride latch'siz komutlar eklenirse (ör. kalibrasyon,
mod değiştirme) bu katman onları da güvenceye alır.

ZAMANLAMA NOTU
--------------
ACK, komut alındığı çevrimde gönderilir. LoRa yarı çift yönlü olduğu için
gönderim sırası RealLoraE22Link'in AUX beklemesiyle seri hale gelir; telemetri
ile ACK aynı anda havaya çıkamaz. 4.8 kbps'de ACK ~60 ms sürer, telemetriler
arasındaki ~775 ms'lik sessiz pencereye rahat sığar.
"""
from __future__ import annotations

from src.common.result import ErrorCode, Result
from src.telemetry.framing import crc16_ccitt


KOMUT_ONEK = "#"
ACK_ONEK = "$"

SONUC_OK = "OK"
SONUC_DUP = "DUP"
SONUC_ERR = "ERR"

# Kaç komut kimliğinin geçmişi tutulacak. Uçuş boyunca gönderilecek komut
# sayısı onlarla ifade edilir; 64 fazlasıyla yeterli ve bellek sabit kalır.
ISLENEN_ID_LIMITI = 64


class UplinkService:
    """
    LoRa uplink komut alıcısı.

    `tick()` her çevrimde çağrılır; bekleyen satır yoksa hiçbir şey yapmaz.
    Link `receive()` desteklemiyorsa (mock/simülasyon) sessizce devre dışı
    kalır — çağıran tarafın profil kontrolü yapmasına gerek yoktur.
    """

    def __init__(self, link, commander, log=None) -> None:
        self._link = link
        self._commander = commander
        self._log = log if log else (lambda m: None)

        self._islenen_idler: list[str] = []
        self.received_count = 0
        self.rejected_count = 0

    @property
    def is_available(self) -> bool:
        """Link gerçek uplink destekliyor mu?"""
        return hasattr(self._link, "receive")

    def tick(self) -> int:
        """
        Bekleyen uplink satırlarını işler. İşlenen komut sayısını döndürür.
        Hiçbir durumda istisna fırlatmaz — uplink hatası uçuşu durdurmamalı.
        """
        if not self.is_available:
            return 0

        try:
            satirlar = self._link.receive()
        except Exception as exc:
            self._log(f"UPLINK: alım hatası: {exc}")
            return 0

        islenen = 0
        for satir in satirlar:
            if self._satir_isle(satir):
                islenen += 1
        return islenen

    # ------------------------------------------------------------------

    def _satir_isle(self, satir: str) -> bool:
        satir = (satir or "").strip()

        # Bize ait olmayan trafik: kendi telemetrimiz, kendi ACK'imiz,
        # IoT'ye ilettiğimiz mesajlar. Sessizce geç.
        if not satir.startswith(KOMUT_ONEK):
            return False

        parcalar = satir[1:].split(",")
        if len(parcalar) != 3:
            self._log(f"UPLINK: biçim hatası: {satir}")
            self.rejected_count += 1
            return False

        cmd_id, komut, gelen_crc = (p.strip() for p in parcalar)

        beklenen = f"{crc16_ccitt(f'{cmd_id},{komut}'):04X}"
        if gelen_crc.upper() != beklenen:
            self._log(f"UPLINK: CRC uyuşmazlığı (beklenen {beklenen}, "
                      f"gelen {gelen_crc})")
            self.rejected_count += 1
            self._ack(cmd_id, SONUC_ERR)
            return False

        self.received_count += 1

        if cmd_id in self._islenen_idler:
            self._log(f"UPLINK: ID {cmd_id} zaten işlendi, tekrar uygulanmadı")
            self._ack(cmd_id, SONUC_DUP)
            return False

        sonuc = self._commander.handle(komut)

        self._islenen_idler.append(cmd_id)
        if len(self._islenen_idler) > ISLENEN_ID_LIMITI:
            self._islenen_idler.pop(0)

        if sonuc.is_ok:
            self._log(f"UPLINK #{cmd_id} '{komut}': {sonuc.unwrap().detail}")
            self._ack(cmd_id, SONUC_OK)
            return True

        self._log(f"UPLINK #{cmd_id} '{komut}': RED - {sonuc.message}")
        self.rejected_count += 1
        self._ack(cmd_id, SONUC_ERR)
        return False

    def _ack(self, cmd_id: str, sonuc: str) -> Result[None]:
        govde = f"{cmd_id},{sonuc}"
        cerceve = f"{ACK_ONEK}{govde},{crc16_ccitt(govde):04X}"
        try:
            return self._link.send(cerceve)
        except Exception as exc:
            return Result.err(ErrorCode.IO_ERROR, f"ACK gönderilemedi: {exc}")

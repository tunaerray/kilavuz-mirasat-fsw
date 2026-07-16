# Kaynak Analizi (SOURCE_ANALYSIS)

Bu belge, uçuş yazılımı (FSW) gereksinimlerinin dayandığı birincil kaynakların
gerçekten okunarak doğrulanmış özetidir. Her satır `Kaynak | Bölüm | Sayfa | Tür`
referansıyla verilmiştir. Sayfa numaraları PDF sayfa numaralarıdır (belge içi
basılı numara parantez içinde belirtilmiştir).

## Kaynak Envanteri

| # | Dosya | Tür | Rol |
|---|-------|-----|-----|
| 1 | `2026_Model_Uydu_Yarışması_Şartnamesi_xu1ZC.pdf` (29 sf) | Şartname V4.0 | **Birincil ve bağlayıcı** yarışma/görev gereksinimleri |
| 2 | `KILAVUZ_MİRASAT_PDR (1).pdf` (118 sf) | Takım PDR | Takımın sistem/tasarım kararları |
| 3 | `KILAVUZ_MİRASAT_PDR (1).pptx` | Takım PDR (sunum) | PDF ile aynı rapor; şekil/tablo görselleri |
| 4 | `ANA_PROMPT.md` | Yönerge | Önceden hazırlanmış özet (belgelerden teyit edildi) |

Kaynak kullanım önceliği: **Şartname > PDR > ANA_PROMPT özetleri.**

> Not: PDF metni `pypdf` ile çıkarıldı (ortamda `pdftoppm` yok). PPTX görselleri
> aynı raporun farklı formatı olarak kabul edildi; bağımsız ikinci kaynak sayılmadı.

## Şartnameden Doğrulanan Gerçekler (sayfa referanslı)

| Konu | Bulgu | Kaynak | Tür |
|------|-------|--------|-----|
| Görev profili | Model uydu 1500–1800 m (~1600 m) irtifadan bırakılır | Şartname §1.3 s.7 | Zorunlu |
| Pasif iniş | Taşıyıcı+GY pasif sistemle **12–14 m/s** ile 1000 m'ye iner (metin) | Şartname §1.3 s.7; Gereksinim-5 s.11 | Zorunlu |
| Pasif iniş (Tablo 1) | Tablo 1 aynı fazı **12–16 m/s** verir → CONFLICT-004 | Şartname Tablo 1 s.7 | Zorunlu (çelişkili) |
| Ayrılma | 1000 m (±10 m) otonom ayrılma; ayrılmazsa manuel komut | Gereksinim-6,7 s.11 | Zorunlu |
| Ayrılma yöntemi | Patlayıcı/kimyasal YASAK | Gereksinim-8 s.11 | Zorunlu |
| Aktif iniş | Ayrılma sonrası SİGMA ile **8–10 m/s** iner | Gereksinim-9 s.11 | Zorunlu |
| APAM | 16 m/s üzeri **10 sn'den fazla** → APAM; **100 m üzerinde** açılır; paraşütten hemen önce **motorlar durdurulur**; manuel komutla da açılabilir | Gereksinim-10 s.11 | Zorunlu |
| Son 50 m | Hasarsız iniş için aktüatör RPM'i artırılabilir | Gereksinim-14 s.12 | Öneri |
| Sensör seti | Sıcaklık, basınç, yükseklik, iniş hızı, konum, pil, eksen | Gereksinim-15 s.12 | Zorunlu |
| Telemetri 1 Hz | Her saniye (1 Hz) formata uygun paket | Gereksinim-16 s.12 | Zorunlu |
| Görev zamanı kalıcılığı | İşlemci yeniden başlasa bile zaman korunur | Gereksinim-17 s.12 | Zorunlu |
| Paket sayacı kalıcılığı | 1'den başlar, her pakette artar, restart'ta kaldığı yerden | Gereksinim-18 s.12 | Zorunlu |
| SD kayıt | Telemetri SD karta yazılır | Gereksinim-19 s.13 | Zorunlu |
| Video | Yanal, ufka bakan ≥720p kamera; SD'ye kayıt + canlı iletim | Gereksinim-20,21,22 s.13 | Zorunlu |
| Pil | 1 saat çalışma (SİGMA hariç); açma/kapama düğmesi | Gereksinim-23,24,25 s.13 | Zorunlu |
| İniş sonrası TLM | Gereksinim-27: **10 sn**; §1.3 s.7: **1 dk** → CONFLICT-001 | Gereksinim-27 s.13; §1.3 s.7 | Zorunlu (çelişkili) |
| Buzzer | İniş sonrası kurtarılana kadar sesli ikaz | Gereksinim-28 s.13 | Zorunlu |
| Gyro simülasyon | Yer istasyonunda en az x-y düzleminde duruş | Gereksinim-34 s.13 | Zorunlu (yer ist.) |
| ARAS | İniş hızı, konum, ayrılma, APAM denetlenir; hata kodu üretilir | Gereksinim-35 s.13; §2.2 s.13-14 | Zorunlu |
| BONUS-1 | 200 m (AGL), 10 sn askı, 0–1 m/s; sonra 8–10 m/s | Gereksinim-36 s.13 | Bonus |
| BONUS-2 | S2D-IOT: 6 haneli RHRHRH komut al→SD kaydet→IoT'a aktar | Gereksinim-37 s.13; §2.3 s.14-15 | Bonus |
| BONUS-3 | Z.I.R.H: karıştırmaya dayanıklı haberleşme | Gereksinim-38 s.13 | Bonus |
| Telemetri formatı | 17 alan, TAM sıra (§2.4) | Şartname §2.4 s.15-16 | Zorunlu |
| Uydu statüsü | 0..5 kodları (aşağıda) | Şartname §2.4 s.16 | Zorunlu |
| Hata kodu | §2.4 "**5 haneli**" der; §2.2 ve örnekler 4 hane → CONFLICT-003 | Şartname §2.4 s.16; §2.2 s.14 | Zorunlu (çelişkili) |
| Puan kesintisi | Sıra/başlık/birim düzeni yanlışsa %2 kesinti | Şartname §2.4 s.16 NOT | Zorunlu |

### Uydu Statüsü Kodları (Şartname §2.4 s.16 — BAĞLAYICI)
```
0: Uçuşa Hazır (roket ateşlenmeden önce)
1: Yükselme
2: Model Uydu İniş
3: Ayrılma
4: Görev Yükü İniş
5: Kurtarma (yere temas)
```

### ARAS Hata Kodu Bit Tanımları (Şartname §2.2 s.13-14 — BAĞLAYICI)
```
Bit-1: İniş hızı 8–10 m/s aralığı DIŞINDA → 1, içinde → 0
Bit-2: Görev yükü konum verisi ALINAMIYOR → 1, alınıyor → 0
Bit-3: Taşıyıcıdan ayrılma GERÇEKLEŞMEDİ → 1, gerçekleşti → 0
Bit-4: APAM aktifleştirildi → 1, değil → 0
Örnekler (§2.2): <0000> sorunsuz, <0100> konum yok, <0001> APAM aktif  (4 hane)
```

### Telemetri Format Alanları (Şartname §2.4 s.15-16 — TAM SIRA)
```
1 PAKET NUMARASI  2 UYDU STATÜSÜ  3 HATA KODU  4 GÖNDERME SAATİ
5 BASINÇ(Pa)  6 YÜKSEKLİK(m)  7 İNİŞ HIZI(m/s)  8 SICAKLIK(°C)  9 PİL(V)
10 GPS LAT  11 GPS LON  12 GPS ALT(m)  13 PITCH  14 ROLL  15 YAW(derece)
16 RHRHRH*  17 TAKIM NO
```
Yükseklik: kalkış noktası 0 m. GÖNDERME SAATİ: Gün/Ay/Yıl Saat:Dakika:Saniye.

## PDR'den Doğrulanan Takım Kararları (sayfa referanslı)

| Konu | Bulgu | Kaynak | Tür |
|------|-------|--------|-----|
| Takım No | **947450** (her sayfa altbilgisi) | PDR tüm sayfalar | Kesin |
| Görev bilgisayarı | Raspberry Pi 5 4GB (yedek RPi 4) | PDR s.6 | Karar |
| Uçuş kontrol kartı | PixMin V1.0 (yedek Pixhawk 4 mini) | PDR s.7 | Karar |
| FC işlemcisi | STM32F405VGT6 (yedek F407VGT6) | PDR s.6 | Karar |
| Sıcaklık/Basınç/IMU | BME280/BMP280, LPS22HB(pixhawk)/BME280, MPU6500(pixhawk)/ICM-20948 | PDR s.6 | Karar |
| Manyetometre | IST8310 / QMC5883L | PDR s.6 | Karar |
| Kamera | Pi Kamera V2 NoIR / V1.3 | PDR s.6 | Karar |
| Haberleşme | LoRa E22 900T22D (yedek XBee SX/XR 868); GY 5 dBi, Yİ 9 dBi Yagi | PDR s.6, s.64 | Karar |
| PWM sürücü | PCA9685 16 kanal I2C | PDR s.6 | Karar |
| Motorlar | 4× Emax ECO II 2207 1700KV | PDR s.7 | Karar |
| ESC | BlHeli 45A ESC (4in1) | PDR s.7 | Karar |
| Servolar | SG90 / Emax ES08MA2 | PDR s.6 | Karar |
| Güç | SİGMA: 4S 14.8V 2200mAh LiPo; aviyonik: 18650 3.7V Li-ion | PDR s.6-7 | Karar |
| IoT işlemcisi | ESP32 / Arduino Uno | PDR s.7 | Karar |
| Örnek telemetri paketi | `152,4,0000,04/05/2026 14:32:10, 91234.5, 748.2, 8.7, 28.4, 11.4, 39.9255, 32.8662, 985.3, 5.2, -3.1, 120.6, 2R0G1B, #####` | PDR s.63 | Referans |
| PDR statü kodları | s.62: 2=Ayrılma, 3=Model Uydu İniş (**şartnameye göre TERS**) → CONFLICT-002 | PDR s.62 | Çelişkili |
| FSW dili | "C / C++, VS Code + Arduino IDE" | PDR s.80 | Karar (çelişkili) |
| Yer istasyonu | Python + PyQt5; XCTU ile modül konfig. | PDR s.90 | Karar |
| Kalibrasyon | Barometre başlangıçta sıfırlanır; zaman UTC 1 sn çözünürlük | PDR s.90 | Karar |

## FSW'nin Hedef İşlemcisi
ANA_PROMPT ve PDR'ye göre **birincil odak Raspberry Pi 5 üzerindeki üst seviye
Görev Yazılımı**dır (durum makinesi, telemetri, kalıcılık, komut, bonus yönetimi,
kayıt). PixMin/STM32 tarafındaki yüksek frekanslı stabilizasyon PID döngüsü, RPi
tarafından bir soyut `FlightControllerLink` (HAL) üzerinden sürülür. Bu ayrım
CONFLICT-005 ve ADR-001'de gerekçelendirilmiştir.

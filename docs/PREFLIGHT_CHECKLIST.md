# Uçuş Öncesi Kontrol Listesi (PREFLIGHT_CHECKLIST)

FRR (Şartname §4.2) ve uçuş günü operasyonu için. Yazılım tarafı `--preflight`
komutuyla otomatik denetlenir (`src/services/preflight.py`); mekanik/operasyonel
maddeler el ile onaylanır.

## A. Otomatik Yazılım Kontrolleri (`python -m src.app.main --preflight`)
Go/no-go kapısı — hepsi GO olmadan uçuşa izin verilmez:
- [ ] Barometre okunabilir
- [ ] IMU okunabilir
- [ ] GPS okunabilir
- [ ] Batarya okunabilir
- [ ] Batarya dolu (≥ `preflight_min_voltage_v` = 15.0 V, 4S)
- [ ] GPS kilidi (fix + ≥ `preflight_min_satellites` = 6 uydu)
- [ ] Aktüatörler Safe State (motorlar disarm/0, servolar kilitli, APAM kapalı, kollar kilitli)
- [ ] Kalıcılık yüklü (paket sayacı / görev zamanı erişilebilir)

## B. Operasyonel / Mekanik (el ile)
- [ ] Görev yükü ve taşıyıcı ağırlığı 1800 ±90 g (Gereksinim-2) — tartıldı
- [ ] Açma/kapama düğmesi erişilebilir (taşıyıcı içindeyken de) (Gereksinim-25)
- [ ] SİGMA kolları başlangıçta gövde içinde kapalı/kilitli (PDR)
- [ ] Acil paraşüt katlanmış, APAM pimi güvenli, kapak kapalı
- [ ] Ayrılma mekanizması (kremayer-dişli) kurulu, patlayıcısız (Gereksinim-8)
- [ ] Kamera yanal, ufka bakan, lens temiz (Gereksinim-20)
- [ ] SD kart takılı ve yazılabilir (telemetri + video)
- [ ] Antenler bağlı (GY 5 dBi, Yİ 9 dBi Yagi)
- [ ] Piller şarjlı: SİGMA 4S LiPo, aviyonik 18650; yer istasyonu ≥2 saat (Gereksinim-33)
- [ ] Yer istasyonu barometresi ile saha basıncı kontrolü; UTC saat senkron
- [ ] Buzzer sesli ikaz çalışıyor (Gereksinim-28)

## C. Saha Kalibrasyonu
- [ ] Barometre çok örnekli sıfırlama yapıldı (`BaroCalibrator`, kalkış = 0 m) —
      referans kalıcı depoya yazıldı ve restart'a dayanıklı.
- [ ] Bırakma irtifası (uçuş günü) teyit edildi (~1600 m, hava koşullarına göre).

## D. Haberleşme Testi
- [ ] 1 Hz telemetri yer istasyonunda alınıyor, CRC doğrulanıyor
- [ ] Canlı video yer istasyonunda görüntüleniyor
- [ ] Manuel ayrılma ve manuel APAM komutları test edildi (Gereksinim-7/10)
- [ ] (Bonus) S2D-IOT RHRHRH komutu IoT istasyonunu tetikliyor
- [ ] (Bonus) Z.I.R.H kesinti senaryosu: kayıp veriler geri-aktarılıyor

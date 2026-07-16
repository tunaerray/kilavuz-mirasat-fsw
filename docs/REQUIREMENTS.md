# Gereksinimler (REQUIREMENTS)

Kimlik şeması: `REQ-<ALAN>-XXX`. Her gereksinim kaynak referansı taşır.
Alanlar: MISSION, FUNC, HW, SW, TLM, CTRL, SAFE, TEST.
"Faz" sütunu, gereksinimin ilk kez hangi geliştirme aşamasında ele alındığını
gösterir (bkz. `DEVELOPMENT_PLAN.md`). ✅ = Aşama 1 kapsamında uygulandı.

## REQ-MISSION — Görev Gereksinimleri
| ID | Gereksinim | Kaynak | Faz |
|----|-----------|--------|-----|
| REQ-MISSION-001 | Model uydu = taşıyıcı + görev yükü, iki parça | Şartname G-1 s.11 | — |
| REQ-MISSION-002 | Toplam ağırlık 1800 ±90 g | Şartname G-2 s.11 | — |
| REQ-MISSION-003 | 1500–1800 m (~1600 m) irtifadan bırakılır | Şartname §1.3 s.7 | 1 (sim profili) |
| REQ-MISSION-004 | Taşıyıcı pasif iniş 12–14 m/s ile 1000 m'ye | Şartname G-5 s.11 | 2 |
| REQ-MISSION-005 | 1000 m ±10 m otonom ayrılma | Şartname G-6 s.11 | 2 |
| REQ-MISSION-006 | Ayrılmazsa manuel ayrılma komutu | Şartname G-7 s.11 | 3 |
| REQ-MISSION-007 | Ayrılma patlayıcısız/kimyasalsız | Şartname G-8 s.11 | HW |
| REQ-MISSION-008 | Ayrılma sonrası SİGMA ile 8–10 m/s iniş | Şartname G-9 s.11 | 2 |
| REQ-MISSION-009 | Son 50 m'de RPM artırılabilir | Şartname G-14 s.12 | 2 |
| REQ-MISSION-010 | İniş sonrası buzzer ile sesli ikaz | Şartname G-28 s.13 | 3 |

## REQ-FUNC — Fonksiyonel
| ID | Gereksinim | Kaynak | Faz |
|----|-----------|--------|-----|
| REQ-FUNC-001 | Sıcaklık, basınç, yükseklik, iniş hızı, konum, pil, eksen toplanır | Şartname G-15 s.12 | 1 ✅ (mock) |
| REQ-FUNC-002 | Açma/kapama düğmesi (taşıyıcı içindeyken erişilebilir) | Şartname G-25 s.13 | HW |
| REQ-FUNC-003 | 1 saat çalışma (SİGMA hariç) yeterli pil | Şartname G-24 s.13 | HW |
| REQ-FUNC-004 | Barometre başlangıçta sıfırlanır (kalkış = 0 m) | PDR s.90; Şartname §2.4 s.16 | 1 ✅ |

## REQ-HW — Donanım (bkz. HARDWARE profili SOURCE_ANALYSIS)
| ID | Gereksinim | Kaynak | Faz |
|----|-----------|--------|-----|
| REQ-HW-001 | Görev bilgisayarı RPi 5 4GB | PDR s.6 | HAL |
| REQ-HW-002 | Uçuş kontrol kartı PixMin V1.0 / STM32F405 | PDR s.6-7 | HAL |
| REQ-HW-003 | LoRa E22 900T22D telemetri (UART) | PDR s.6 | HAL |
| REQ-HW-004 | 4× Emax ECO II 2207 + BlHeli 45A ESC | PDR s.7 | HAL |
| REQ-HW-005 | PCA9685 I2C PWM sürücü (servo endpoint limiti) | PDR s.6 | HAL |
| REQ-HW-006 | ≥720p yanal ufka bakan kamera | Şartname G-20,21 s.13 | 4 |
| REQ-HW-007 | 10G şok dayanımı, titreşim uyumu | Şartname G-12 s.12 | Test |

## REQ-SW — Yazılım
| ID | Gereksinim | Kaynak | Faz |
|----|-----------|--------|-----|
| REQ-SW-001 | Katmanlı, modüler, test edilebilir mimari | ANA_PROMPT; iyi mühendislik | 1 ✅ |
| REQ-SW-002 | SIMULATION_ONLY varsayılan profil | ANA_PROMPT güvenlik | 1 ✅ |
| REQ-SW-003 | Sabit periyotlu ana döngü + döngü aşımı tespiti | ANA_PROMPT F.10 | 1 ✅ |
| REQ-SW-004 | Deterministik test saati (gerçek saatten bağımsız) | ANA_PROMPT F.2 | 1 ✅ |
| REQ-SW-005 | Açık hata/sonuç modeli (sessiz başarısızlık yok) | ANA_PROMPT F.3 | 1 ✅ |
| REQ-SW-006 | `--max-cycles` / `--duration` ile sınırlı koşu | ANA_PROMPT F.10 | 1 ✅ |

## REQ-TLM — Telemetri ve Haberleşme
| ID | Gereksinim | Kaynak | Faz |
|----|-----------|--------|-----|
| REQ-TLM-001 | 17 alanlı paket, TAM sıra ve birimler | Şartname §2.4 s.15-16 | 1 ✅ |
| REQ-TLM-002 | 1 Hz gönderim | Şartname G-16 s.12 | 1 ✅ (üretim); 4 (RF) |
| REQ-TLM-003 | Paket no 1'den başlar, artar, restart'ta devam | Şartname G-18 s.12 | 1 ✅ |
| REQ-TLM-004 | Görev zamanı restart'a dayanıklı | Şartname G-17 s.12 | 1 ✅ |
| REQ-TLM-005 | Telemetri SD karta CSV | Şartname G-19 s.13 | 1 ✅ (dosya) |
| REQ-TLM-006 | Başlık+birim düzeni (aksi halde %2 kesinti) | Şartname §2.4 NOT s.16 | 1 ✅ |
| REQ-TLM-007 | Uydu statüsü kodları 0..5 | Şartname §2.4 s.16 | 1 ✅ |
| REQ-TLM-008 | CRC/checksum doğrulama | PDR test planı | 4 |
| REQ-TLM-009 | Store-and-forward (Z.I.R.H) tamponlama | Şartname G-38 s.13; PDR | 4 (arayüz Aşama1) |
| REQ-TLM-010 | Canlı video 5 GHz Wi-Fi + SD | Şartname G-20,22 s.13 | 4 |

## REQ-CTRL — Kontrol / Navigasyon
| ID | Gereksinim | Kaynak | Faz |
|----|-----------|--------|-----|
| REQ-CTRL-001 | Sensör füzyonu ile irtifa/iniş hızı/yönelim kestirimi | ANA_PROMPT §context | 2 |
| REQ-CTRL-002 | PID ile 8–10 m/s kontrollü alçalma | Şartname G-9 s.11 | 2 |
| REQ-CTRL-003 | SİGMA kol açma/kilitleme (ayrılma→aktif iniş arası) | PDR SİGMA | 2 |
| REQ-CTRL-004 | BONUS-1 Hovering: 200 m, 10 sn, 0–1 m/s | Şartname G-36 s.13 | 3 |
| REQ-CTRL-005 | Motor/servo komut üretimi (endpoint limitli) | PDR s.6 | 2 |

## REQ-SAFE — Güvenlik / APAM / Failsafe
| ID | Gereksinim | Kaynak | Faz |
|----|-----------|--------|-----|
| REQ-SAFE-001 | Başlangıçta ve hata halinde aktüatörler Safe State | ANA_PROMPT güvenlik | 1 ✅ |
| REQ-SAFE-002 | Aktüatörler arm edilmeden çalışmaz | ANA_PROMPT güvenlik | 1 ✅ |
| REQ-SAFE-003 | APAM: 16 m/s üzeri 10 sn KESİNTİSİZ → tetik | Şartname G-10 s.11 | 1 ✅ (mantık) |
| REQ-SAFE-004 | APAM paraşütü >100 m'de açılır | Şartname G-10 s.11 | 1 ✅ (mantık) |
| REQ-SAFE-005 | Paraşütten HEMEN ÖNCE motor kill | Şartname G-10 s.11 | 1 ✅ (sıralama) |
| REQ-SAFE-006 | Manuel APAM komutu | Şartname G-10 s.11 | 3 |
| REQ-SAFE-007 | APAM sadece iniş fazında; hız düşerse sayaç sıfırlanır | ANA_PROMPT APAM | 1 ✅ |
| REQ-SAFE-008 | Link loss TEK BAŞINA APAM tetiklemez | ANA_PROMPT APAM | 1 ✅ |
| REQ-SAFE-009 | Sağlık izleme: veri yaşı, pil, link, döngü gecikmesi | ANA_PROMPT F.9 | 1 ✅ |
| REQ-SAFE-010 | Motor PWM/RPM tutarsızlığı → motor arıza tespiti | ANA_PROMPT APAM | 2 |

## REQ-TLM (ARAS) — Hata Kodu
| ID | Gereksinim | Kaynak | Faz |
|----|-----------|--------|-----|
| REQ-TLM-011 | ARAS hata kodu FSW'de üretilir, her pakete eklenir | Şartname §2.2 s.13-14 | 1 ✅ |
| REQ-TLM-012 | Bit1 iniş hızı 8–10 dışı | Şartname §2.2 s.14 | 1 ✅ |
| REQ-TLM-013 | Bit2 konum alınamama | Şartname §2.2 s.14 | 1 ✅ |
| REQ-TLM-014 | Bit3 ayrılmama | Şartname §2.2 s.14 | 1 ✅ |
| REQ-TLM-015 | Bit4 APAM aktif | Şartname §2.2 s.14 | 1 ✅ |

## REQ-BONUS — Bonus Görevler
| ID | Gereksinim | Kaynak | Faz |
|----|-----------|--------|-----|
| REQ-BONUS-001 | BONUS-1 İrtifa koruma (Hovering) | Şartname G-36 s.13 | 3 |
| REQ-BONUS-002 | BONUS-2 S2D-IOT RHRHRH al→SD→IoT | Şartname §2.3 s.14-15 | 3 |
| REQ-BONUS-003 | BONUS-3 Z.I.R.H store-and-forward | Şartname G-38 s.13 | 4 |

## REQ-TEST — Test / Doğrulama
| ID | Gereksinim | Kaynak | Faz |
|----|-----------|--------|-----|
| REQ-TEST-001 | Birim testleri (config, saat, durum makinesi, kalıcılık, TLM, APAM) | ANA_PROMPT test | 1 ✅ |
| REQ-TEST-002 | Kalıcılık restart senaryosu testi | Şartname G-17,18; ANA_PROMPT | 1 ✅ |
| REQ-TEST-003 | TLM paketi örnek paketle karşılaştırma | ANA_PROMPT test | 1 ✅ |
| REQ-TEST-004 | Deterministik saat (gerçek zaman beklemesi yok) | ANA_PROMPT test | 1 ✅ |
| REQ-TEST-005 | FRR: 10G şok, 150–200 Hz titreşim, düşme, ayrılma sistem testleri | Şartname §4.2; G-12 | Test fazı |

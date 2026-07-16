# Güvenlik Konsepti (SAFETY_CONCEPT)

## 1. Güvenlik Sınırları (Aşama 1'de zorunlu)
- Varsayılan profil **SIMULATION_ONLY**: hiçbir gerçek GPIO/PWM/motor/servo/APAM
  çıkışı ÜRETİLMEZ. Mock aktüatörler yalnızca komutları loglar.
- Aktüatörler **disarmed & Safe State** başlar:
  - Motorlar: 0 throttle / disarm.
  - Servolar (ayrılma, APAM): kilitli/güvenli pozisyon.
  - SİGMA kolları: mevcut konumda kilitli.
- **Arm edilmeden** hiçbir aktüatör hareket komutu kabul etmez (`SAFETY_INTERLOCK`).
- Yazılım başlarken ve herhangi bir hata/exception'da aktüatörler Safe State'e
  zorlanır (`enter_safe_state()`).

## 2. Failsafe Mimarisi (genişletilebilir)
Failsafe girdileri: sensör zaman aşımı, telemetri link loss, düşük batarya, kontrol
döngüsü gecikmesi, motor PWM/RPM tutarsızlığı (Aşama 2), APAM koşulları.

### 2.1 APAM (Acil Paraşüt Açma) — DOĞRULANMIŞ kurallar (Şartname G-10 s.11)
Tetikleme (hepsi sağlanmalı):
1. Sistem **iniş fazında** olmalı (ASSUMPTION-004: faz ≥ ayrılma ve irtifa azalıyor).
   Yükselmede APAM **tetiklenmez**.
2. İniş hızı **16 m/s üzerinde 10 sn KESİNTİSİZ**. Hız güvenli seviyeye düşerse
   sayaç **sıfırlanır** (kısa/anlık artışlar tetiklemez).
3. Açılım yüksekliği **> 100 m** olmalı; irtifa ≤100 m ise mekanik açılım yapılmaz
   (paraşüt etkisiz kalır — güvenlik gereği yalnız motor-kill/uyarı).

Sıralama (kesin):
```
APAM kararı (algoritma VEYA manuel komut)
   → 1) MOTOR KILL (tüm motorlar 0 throttle / disarm)
   → 2) APAM servosu ile paraşüt kapağı açılır
```
Manuel: yer istasyonundan **manuel APAM** komutuyla da açılabilir (Aşama 3).

### 2.2 False-trigger önlemleri
- Tek sensöre göre karar verilmez; farklı sensör verileri karşılaştırılır (Aşama 2
  füzyon). Aşama 1'de iniş hızı kestirimi tek kaynaklı ama sayaç/faz/irtifa
  kilitleriyle korunur.
- **Link loss TEK BAŞINA APAM tetiklemez** (Şartname/ANA_PROMPT). Link loss yalnız
  sağlık bayrağı üretir; manuel komut gönderilemeyebileceği tasarımda dikkate alınır.
- Motor PWM komutları RPM geri bildirimiyle karşılaştırılır; tutarsızlıkta önce
  motor komutları düzeltilir, düşüremiyorsa APAM (Aşama 2, motor arıza tespiti).

## 3. Sağlık İzleme (Health Monitor) — Aşama 1
| Kontrol | Eşik (config) | Sonuç |
|---------|---------------|-------|
| Sensör veri yaşı | > `max_sensor_age_s` (0.5 s) | STALE_SENSOR bayrağı |
| Batarya gerilimi | < `low_voltage_v` (14.0 V, 4S) | LOW_BATTERY bayrağı |
| Link | son iletişimden bu yana > `link_timeout_s` | LINK_LOSS bayrağı |
| Döngü gecikmesi | çevrim süresi > `loop_period * (1+tol)` | LOOP_OVERRUN bayrağı |

Sağlık bayrakları failsafe ve telemetri (dolaylı) tarafından tüketilir; APAM
kararını yalnız §2.1 koşulları verir.

## 4. Safe State Tanımı
`SafeState`: motors=DISARMED(0), separation_servo=LOCKED, apam_servo=CLOSED,
arms=LOCKED. Sistem başlangıcı, FAULT, SAFE_MODE ve kapanışta uygulanır.

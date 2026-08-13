#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TEZGAH GOSTERIMI YAMASI
=======================
Son GitHub push'undan sonra sahada yapilan tum degisiklikleri tek seferde
uygular. Yeni kart kurulumundan sonra bir kez calistirilir.

    cd ~/kilavuz-mirasat-fsw
    source .venv/bin/activate
    python3 yama_uygula.py

Betik AYNI DEGISIKLIGI IKI KEZ UYGULAMAZ; tekrar calistirilabilir.
Her degisiklik icin uygulandi/atlandi bilgisi basar.

!!! UCUS ONCESI GERI ALINMASI GEREKENLER !!!
--------------------------------------------
Asagidaki uc degisiklik SARTNAMEYE AYKIRIDIR ve yalnizca tezgah gosterimi
icindir. Ucustan once mutlaka geri alinmalidir:

  1. status=0          -> Sartname 2.4 statu gecislerini (0..5) ZORUNLU tutar
                          ve telemetride bu alan puanlanir.
  2. if False and ...  -> Sartname madde 27 inis sonrasi 10 sn telemetri ister.
  3. AUX beklemesi     -> Paket cakisma korumasi devre disi kalir.

Ayrica ucus kartinda:
  ARMING_CHECK = 1      (GPS/pusula kontrolleri geri acilmali)
  BRD_SAFETYENABLE = 1  (guvenlik anahtari geri acilmali)
"""

import os
import re
import sys


def oku(yol):
    with open(yol, encoding="utf-8") as f:
        return f.read()


def yaz(yol, icerik):
    with open(yol, "w", encoding="utf-8") as f:
        f.write(icerik)


def degistir(yol, eski, yeni, ad, imza=None):
    """
    Tek bir degisikligi uygular. `imza` metinde varsa degisiklik zaten
    yapilmis kabul edilir ve atlanir.
    """
    k = oku(yol)
    kontrol = imza if imza is not None else yeni

    if kontrol in k:
        print(f"  [atlandi] {ad} — zaten uygulanmis")
        return True

    if eski not in k:
        print(f"  [HATA]    {ad} — hedef metin bulunamadi")
        return False

    yaz(yol, k.replace(eski, yeni, 1))
    print(f"  [tamam]   {ad}")
    return True


# =============================================================================

def yama_1_lora_mod_gecisi():
    """
    E22 mod gecis suresi 0.20 -> 0.35 sn.

    Modul konfigurasyon moduna gecerken AUX sinyal VERMIYOR; sabit bekleme
    sart. 0.20 sn sahada yetmedi, modul "parametreler okunamadi" dondu.
    """
    yol = "src/drivers/real_lora.py"
    k = oku(yol)
    m = re.search(r"^MOD_GECIS_S\s*=\s*([\d.]+).*$", k, re.M)
    if not m:
        print("  [HATA]    LoRa mod gecis suresi — satir bulunamadi")
        return False
    if m.group(1) == "0.35":
        print("  [atlandi] LoRa mod gecis suresi — zaten 0.35")
        return True
    yaz(yol, k[:m.start()] +
        "MOD_GECIS_S           = 0.35   # E22 mod gecisinde AUX sinyal vermiyor; "
        "0.20 sahada yetmedi" + k[m.end():])
    print("  [tamam]   LoRa mod gecis suresi -> 0.35")
    return True


def yama_2_aux_devre_disi():
    """
    AUX beklemesi devre disi.

    AUX kablosu temassiz: ardisik okumalarda LOW/HIGH degisiyor. Bekleme
    aktifken her gonderim zaman asimina ugruyor ve telemetri hic akmiyor.

    BEDELI: paket cakisma korumasi YOK. Kablo lehimlendikten sonra bu
    degisiklik GERI ALINMALI.
    """
    return degistir(
        "src/drivers/real_lora.py",
        "    def _aux_bekle(self, zaman_asimi: float) -> bool:",
        '''    def _aux_bekle(self, zaman_asimi: float) -> bool:
        # GECICI: AUX kablosu temassiz (ardisik okumalarda LOW/HIGH degisiyor).
        # AUX beklemesi yerine sabit gecikme kullaniliyor.
        #
        # BEDELI: paket cakisma korumasi YOK. Modul mesgulken uzerine yazilabilir
        # ve paket kaybolabilir. Kablo lehimlendikten sonra bu iki satir
        # KALDIRILMALI.
        time.sleep(0.05)
        return True

    def _aux_bekle_gercek(self, zaman_asimi: float) -> bool:''',
        "AUX beklemesi devre disi",
        imza="_aux_bekle_gercek")


def yama_3_mavlink_akis_tekrari():
    """
    MAVLink akis istegi 3 kez tekrarlanir.

    ArduPilot ilk REQUEST_DATA_STREAM'i kacirabiliyor; sahada birden cok kez
    gozlendi. Tek istek gonderildiginde sensorler hic veri vermiyor ve
    barometre kalibrasyonu calismiyordu.
    """
    yol = "src/drivers/mavlink_source.py"
    k = oku(yol)
    if "for _ in range(3):" in k:
        print("  [atlandi] MAVLink akis tekrari — zaten uygulanmis")
        return True

    m = re.search(r"( +)self\._conn\.mav\.request_data_stream_send\(\n"
                  r"( +)([^\n]+)\n( +)([^\n]+)\n", k)
    if not m:
        print("  [HATA]    MAVLink akis tekrari — cagri bulunamadi")
        return False

    g = m.group(1)
    yeni = (f"{g}# ArduPilot ilk akis istegini KACIRABILIYOR; sahada birden cok kez\n"
            f"{g}# gozlendi. Tek istek yeterli degil - 3 kez tekrarlanir, aksi\n"
            f"{g}# halde sensorler hic veri vermiyor.\n"
            f"{g}import time as _t\n"
            f"{g}for _ in range(3):\n"
            f"{g}    self._conn.mav.request_data_stream_send(\n"
            f"{g}        {m.group(3)}\n"
            f"{g}        {m.group(5)}\n"
            f"{g}    _t.sleep(0.1)\n")
    yaz(yol, k[:m.start()] + yeni + k[m.end():])
    print("  [tamam]   MAVLink akis tekrari (3x)")
    return True


def yama_4_telemetri_sonlandirma():
    """
    Telemetri sonlandirmasi devre disi.

    Arac yerde oldugu icin parasut komutu sonrasi sistem inisi tamamlanmis
    sayip telemetriyi kesiyordu.

    UCUS ONCESI GERI ALINMALI - sartname madde 27 inis sonrasi 10 sn
    telemetri ISTIYOR.
    """
    return degistir(
        "src/app/main.py",
        "        if rec.landed and not telemetry_terminated and not rec.telemetry_active:",
        """        # GECICI (tezgah gosterimi): telemetri sonlandirmasi DEVRE DISI.
        # Arac yerde oldugu icin parasut sonrasi sistem inisi tamamlanmis
        # sayip telemetriyi kesiyordu.
        #
        # UCUS ONCESI 'False and' KALDIRILMALI - sartname madde 27 inis
        # sonrasi 10 sn telemetri sonlandirmasini ISTIYOR.
        if False and rec.landed and not telemetry_terminated and not rec.telemetry_active:""",
        "Telemetri sonlandirmasi devre disi",
        imza="if False and rec.landed")


def yama_5_statu_sabit():
    """
    Telemetri statusu 0'da sabitlenir.

    Arac yerde oldugu icin parasut sonrasi statu 5'e (Kurtarma) ciiyordu.

    UCUS ONCESI GERI ALINMALI - sartname 2.4 statu gecislerini ZORUNLU
    tutuyor ve bu alan dogrudan puanlaniyor.
    """
    return degistir(
        "src/app/main.py",
        "                status=state.status_code(),",
        """                # GECICI (tezgah gosterimi): statu 0'da sabit.
                # UCUS ONCESI GERI ALINMALI - sartname 2.4 statu gecislerini
                # (0->1->2->3->4->5) ZORUNLU tutuyor ve bu alan puanlaniyor.
                # Geri almak icin: status=state.status_code()
                status=0,""",
        "Telemetri statusu sabit (0)",
        imza="status=0,")


def yama_6_motor_stop_komutu():
    """
    MOTOR_STOP / acil durdur komutu.

    Yer istasyonundaki ACIL DURDUR butonu bu komutu gonderiyor; onceden
    'bilinmeyen komut' olarak reddediliyordu.
    """
    yol = "src/services/command_service.py"
    k = oku(yol)
    if "_SIGMA_STOP_ALIASES" in k:
        print("  [atlandi] MOTOR_STOP komutu — zaten uygulanmis")
        return True

    adimlar = [
        ('_SIGMA_ALIASES = {"SIGMA", "SIGMA_TEST", "MOTOR", "MOTOR_TEST", "SIGMA_TETIK"}',
         '_SIGMA_ALIASES = {"SIGMA", "SIGMA_TEST", "MOTOR", "MOTOR_TEST", "SIGMA_TETIK"}\n'
         '_SIGMA_STOP_ALIASES = {"MOTOR_STOP", "SIGMA_STOP", "ESTOP", "DUR"}'),

        ('    MANUAL_SIGMA = "MANUAL_SIGMA"',
         '    MANUAL_SIGMA = "MANUAL_SIGMA"\n'
         '    MANUAL_SIGMA_STOP = "MANUAL_SIGMA_STOP"'),

        ('        self._sigma_count = 0',
         '        self._sigma_count = 0\n'
         '        self._sigma_stop_count = 0'),

        ('        return self._sigma_count',
         '        return self._sigma_count\n\n'
         '    @property\n'
         '    def sigma_stop_count(self) -> int:\n'
         '        """Acil durdurma sayaci. Ana dongu kenar tespiti icin okur."""\n'
         '        return self._sigma_stop_count'),

        ('        if token in _SIGMA_ALIASES:',
         '        if token in _SIGMA_STOP_ALIASES:\n'
         '            # Acil durdurma LATCH DEGIL: her komutta sayac artar.\n'
         '            # Operator arka arkaya basabilmeli.\n'
         '            self._sigma_stop_count += 1\n'
         '            self.handled_count += 1\n'
         '            return Result.ok(CommandResult(CommandKind.MANUAL_SIGMA_STOP,\n'
         '                                           f"SIGMA motor DURDURMA '
         '(#{self._sigma_stop_count})"))\n\n'
         '        if token in _SIGMA_ALIASES:'),
    ]

    for eski, yeni in adimlar:
        if eski not in k:
            print(f"  [HATA]    MOTOR_STOP komutu — hedef bulunamadi: {eski[:40]}...")
            return False
        k = k.replace(eski, yeni, 1)

    yaz(yol, k)
    print("  [tamam]   MOTOR_STOP komutu")
    return True


def yama_7_main_sigma_ve_servo():
    """
    main.py: acil durdur baglantisi + servolarin gecikmeli geri surulmesi.

    Servolar acik konumda ZORLANIR ve surekli akim ceker; bu, gerilim dususune
    ve telemetri kesilmesine yol aciyor (sahada gozlendi). Ayrilmadan ve
    parasuttan 3 sn sonra guvenli konuma dondurulur.

    to_safe() ayrilma sonrasi hicbir sey yapmaz (real_actuators.py'deki
    "ayrilma geri donussuz" korumasi), bu yuzden PWM DOGRUDAN suruluyor.
    """
    yol = "src/app/main.py"
    k = oku(yol)
    if "sep_geri_surme_at" in k:
        print("  [atlandi] main.py sigma/servo — zaten uygulanmis")
        return True

    eski_d = "    sigma_seen = commander.sigma_request_count"
    if eski_d not in k:
        print("  [HATA]    main.py sigma/servo — sigma_seen bulunamadi")
        return False

    k = k.replace(eski_d,
        "    sigma_seen = commander.sigma_request_count\n"
        "    sigma_stop_seen = commander.sigma_stop_count\n"
        "    sigma_aktif = False\n"
        "    # Servolar acik konumda ZORLANIR ve surekli akim ceker; gerilim\n"
        "    # dusup telemetriyi kesiyor (sahada gozlendi). Kisa sure sonra\n"
        "    # guvenli konuma dondurulur - o sureye kadar gorev yuku zaten\n"
        "    # uzaklasmis olur, mandal onu yakalayamaz.\n"
        "    sep_geri_surme_at = 0.0\n"
        "    sep_geri_surme_yapildi = False\n"
        "    apam_geri_surme_at = 0.0\n"
        "    apam_geri_surme_yapildi = False\n"
        "    SEP_GERI_SURME_S = 3.0", 1)

    eski_b = "        if commander.sigma_request_count > sigma_seen:"
    if eski_b not in k:
        print("  [HATA]    main.py sigma/servo — sigma tetik blogu bulunamadi")
        return False

    yeni_b = '''        # --- Acil durdurma ---
        if commander.sigma_stop_count > sigma_stop_seen:
            sigma_stop_seen = commander.sigma_stop_count
            sigma_aktif = False
            ms = sigma_actuator.stop()
            log("ACIL DURDUR: motor STOP "
                + ("gonderildi" if ms.is_ok else f"BASARISIZ: {ms.message}"))

        # --- Ayrilma servolarini gecikmeli guvenli konuma al ---
        if (actuators.separation.released and sep_geri_surme_at == 0.0
                and not sep_geri_surme_yapildi):
            sep_geri_surme_at = clk.now_monotonic() + SEP_GERI_SURME_S
        elif sep_geri_surme_at > 0.0 and clk.now_monotonic() >= sep_geri_surme_at:
            sep_geri_surme_at = 0.0
            sep_geri_surme_yapildi = True
            try:
                # to_safe() ayrilma sonrasi HICBIR SEY YAPMAZ (real_actuators.py
                # "ayrilma geri donussuz" korumasi). PWM dogrudan suruluyor.
                from src.drivers.real_actuators import (
                    CH_SEP_LEFT, CH_SEP_RIGHT, CH_WINGS, CH_APAM,
                    _SEP_LEFT_US, _SEP_RIGHT_US, _WINGS_US, _APAM_US)
                _pca = getattr(actuators.separation, "_pca", None)
                if _pca is not None:
                    _pca.set_us(CH_SEP_LEFT, _SEP_LEFT_US["locked"])
                    _pca.set_us(CH_SEP_RIGHT, _SEP_RIGHT_US["locked"])
                    _pca.set_us(CH_WINGS, _WINGS_US["locked"])
                    _pca.set_us(CH_APAM, _APAM_US["closed"])
                    log(f"SEPARATION: {SEP_GERI_SURME_S:.0f} sn sonra servolar "
                        f"guvenli konuma alindi (akim tasarrufu)")
            except Exception as exc:
                log(f"SEPARATION: servo geri surme hatasi: {exc}")

        # --- Parasut servosunu gecikmeli guvenli konuma al ---
        if (failsafe.parachute_deployed and apam_geri_surme_at == 0.0
                and not apam_geri_surme_yapildi):
            apam_geri_surme_at = clk.now_monotonic() + SEP_GERI_SURME_S
        elif apam_geri_surme_at > 0.0 and clk.now_monotonic() >= apam_geri_surme_at:
            apam_geri_surme_at = 0.0
            apam_geri_surme_yapildi = True
            try:
                from src.drivers.real_actuators import CH_APAM, _APAM_US
                _pca = getattr(actuators.separation, "_pca", None)
                if _pca is not None:
                    _pca.set_us(CH_APAM, _APAM_US["closed"])
                    log(f"APAM: {SEP_GERI_SURME_S:.0f} sn sonra parasut servosu "
                        f"guvenli konuma alindi (akim tasarrufu)")
            except Exception as exc:
                log(f"APAM: servo geri surme hatasi: {exc}")

        if commander.sigma_request_count > sigma_seen:'''

    k = k.replace(eski_b, yeni_b, 1)

    # SIGMA tetiklenince bayragi kaldir
    k = k.replace("            sigma_seen = commander.sigma_request_count\n",
                  "            sigma_seen = commander.sigma_request_count\n"
                  "            sigma_aktif = True\n", 1)

    # APAM sonrasi motorlar yeniden arm edilmemeli
    k = k.replace("            res = failsafe.execute_apam(actuators)",
                  "            sigma_aktif = False   # APAM sonrasi motorlar YENIDEN arm edilmemeli\n"
                  "            res = failsafe.execute_apam(actuators)", 1)

    yaz(yol, k)
    print("  [tamam]   main.py acil durdur + servo geri surme")
    return True


def yama_8_sigma_arm_yolu():
    """
    SIGMA motor testi: DO_MOTOR_TEST yerine ARM + RC override.

    ArduCopter 3.5.8 TOPLU motor testini DESTEKLEMEZ: param5 (motor sayisi) ve
    param6 (sira bayragi) YOK SAYILIR, yalnizca param1'deki motor doner.
    Sahada dogrulandi - dort ayri komut gonderilince de sonuncusu oncekini
    iptal etti (1,4,3 gibi karisik ve eksik donus).

    Dort motoru ES ZAMANLI dondurmenin tek yolu arm edip RC override ile gaz
    vermek. RC override 0.1 sn araliklarla SUREKLI gonderilmeli; seyrek
    gonderimde veya ayri thread'de ArduPilot gazi dusuruyor (ikisi de denendi).

    Bu metot ANA DONGUYU BLOKLAR - bu yuzden sigma_test_seconds kisa tutulur.
    """
    yol = "src/drivers/sigma_actuator.py"
    k = oku(yol)
    if "rc_channels_override_send" in k:
        print("  [atlandi] SIGMA arm yolu — zaten uygulanmis")
        return True

    bas = k.find("    def _send(self, conn: object, pct: float, secs: float) -> Result[None]:")
    if bas < 0:
        print("  [HATA]    SIGMA arm yolu — _send bulunamadi")
        return False
    son = k.find("\n    def ", bas + 10)
    if son < 0:
        son = len(k)

    yeni = '''    def _send(self, conn: object, pct: float, secs: float) -> Result[None]:
        """
        Dort motoru AYNI ANDA dondurur: STABILIZE + ARM + RC override gaz.

        NEDEN DO_MOTOR_TEST DEGIL: ArduCopter 3.5.8 toplu motor testini
        desteklemez; param5/param6 yok sayilir ve yalnizca tek motor doner.
        Dort ayri komut gonderildiginde de sonuncusu oncekini IPTAL EDER
        (sahada gozlendi: 1,4,3 gibi karisik ve eksik donus).

        BU METOT ANA DONGUYU BLOKLAR. RC override 0.1 sn araliklarla SUREKLI
        gonderilmeli; seyrek gonderimde veya ayri thread'de ArduPilot gazi
        dusuruyor (ikisi de sahada denendi, calismadi). Bloklama suresince
        telemetri duraklar - bu yuzden sigma_test_seconds KISA tutulmali.
        Daha uzun calisma icin butona tekrar basilir.

        ONKOSUL - UCUS ONCESI GERI ALINMALI:
            ARMING_CHECK = 0      (GPS/pusula kalibrasyonu yok)
            BRD_SAFETYENABLE = 0  (guvenlik anahtari devre disi)
        Bu iki parametre KALICIDIR; acik kalirsa ucus gunu GPS fix olmadan
        arm olur ve pervane takiliyken fiziksel koruma kalmaz.

        NOT: arm dogrulamasi YAPILAMIYOR - MavlinkSource.pump() ayni
        baglantidan okudugu icin recv_match bos donebiliyor.
        """
        pwm = int(1000 + (pct / 100.0) * 1000)

        try:
            conn.set_mode_apm("STABILIZE")
            time.sleep(2.0)
            conn.mav.command_long_send(
                conn.target_system, conn.target_component,
                MAV_CMD_COMPONENT_ARM_DISARM, 0,
                1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
            time.sleep(2.5)

            for _ in range(int(secs * 10)):
                conn.mav.rc_channels_override_send(
                    conn.target_system, conn.target_component,
                    1500, 1500, pwm, 1500, 0, 0, 0, 0)
                time.sleep(0.1)

            conn.mav.rc_channels_override_send(
                conn.target_system, conn.target_component,
                1500, 1500, 1000, 1500, 0, 0, 0, 0)
            time.sleep(0.3)
            conn.mav.command_long_send(
                conn.target_system, conn.target_component,
                MAV_CMD_COMPONENT_ARM_DISARM, 0,
                0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)

        except Exception as exc:  # pragma: no cover - donanima ozgu G/C hatalari
            self._log(f"SIGMA ACTUATOR: komut gonderilemedi: {exc}")
            return Result.err(ErrorCode.IO_ERROR, f"motor komutu gonderilemedi: {exc}")

        self._log(f"SIGMA ACTUATOR: {MOTOR_COUNT} motor ES ZAMANLI dondu "
                  f"(%{pct:.0f} = {pwm} us, {secs:.1f} sn) + DISARM")
        return Result.ok(None)
'''

    k = k[:bas] + yeni + k[son:]

    basi = k[:k.find("class ")]
    if "MAV_CMD_COMPONENT_ARM_DISARM" not in basi:
        k = k.replace("MOTOR_COUNT = 4",
                      "MAV_CMD_COMPONENT_ARM_DISARM = 400   # param1=1 ARM, 0 DISARM\n"
                      "MOTOR_COUNT = 4", 1)
    if "\nimport time" not in basi:
        k = k.replace("from __future__ import annotations",
                      "from __future__ import annotations\n\nimport time", 1)

    yaz(yol, k)
    print("  [tamam]   SIGMA arm yolu (es zamanli 4 motor)")
    return True


def yama_9_config_degerleri():
    """
    Gaz %20, sure 5 sn.

    %8-12 MOT_SPIN_ARM esiginin (%10) altinda/sinirinda kaliyor, motorlar
    donmuyor. 5 sn ana dongu bloklamasini kabul edilebilir tutar.
    """
    yol = "config/default.py"
    k = oku(yol)
    ok = True

    m = re.search(r"^(\s+sigma_test_percent: float = )([\d.]+)(.*)$", k, re.M)
    if m and m.group(2) != "20.0":
        k = k[:m.start()] + m.group(1) + "20.0" + \
            "         # MOT_SPIN_ARM esigi %10; altinda motorlar donmuyor" + k[m.end():]
        print("  [tamam]   sigma_test_percent -> 20.0")
    elif m:
        print("  [atlandi] sigma_test_percent — zaten 20.0")
    else:
        print("  [HATA]    sigma_test_percent bulunamadi")
        ok = False

    m = re.search(r"^(\s+sigma_test_seconds: float = )([\d.]+)(.*)$", k, re.M)
    if m and m.group(2) != "5.0":
        k = k[:m.start()] + m.group(1) + "5.0" + \
            "         # ana dongu bloklanir - KISA tut" + k[m.end():]
        print("  [tamam]   sigma_test_seconds -> 5.0")
    elif m:
        print("  [atlandi] sigma_test_seconds — zaten 5.0")
    else:
        print("  [HATA]    sigma_test_seconds bulunamadi")
        ok = False

    yaz(yol, k)
    return ok


# =============================================================================

YAMALAR = [
    ("LoRa mod gecis suresi",        yama_1_lora_mod_gecisi),
    ("AUX beklemesi devre disi",     yama_2_aux_devre_disi),
    ("MAVLink akis tekrari",         yama_3_mavlink_akis_tekrari),
    ("Telemetri sonlandirma kapali", yama_4_telemetri_sonlandirma),
    ("Statu 0'da sabit",             yama_5_statu_sabit),
    ("MOTOR_STOP komutu",            yama_6_motor_stop_komutu),
    ("Acil durdur + servo geri",     yama_7_main_sigma_ve_servo),
    ("SIGMA arm yolu",               yama_8_sigma_arm_yolu),
    ("Config degerleri",             yama_9_config_degerleri),
]


def main():
    if not os.path.exists("src/app/main.py"):
        print("HATA: depo kokunde calistirilmali.")
        print("      cd ~/kilavuz-mirasat-fsw && python3 yama_uygula.py")
        return 1

    print("Tezgah gosterimi yamasi uygulaniyor...\n")

    basarili = 0
    for ad, fn in YAMALAR:
        try:
            if fn():
                basarili += 1
        except Exception as exc:
            print(f"  [HATA]    {ad} — {exc}")

    print(f"\n{basarili}/{len(YAMALAR)} yama tamam.")

    # Sozdizimi dogrulamasi
    import ast
    print("\nSozdizimi kontrolu:")
    hatali = False
    for yol in ("src/app/main.py", "src/drivers/real_lora.py",
                "src/drivers/sigma_actuator.py", "src/drivers/mavlink_source.py",
                "src/services/command_service.py", "config/default.py"):
        try:
            ast.parse(oku(yol))
            print(f"  OK    {yol}")
        except SyntaxError as e:
            print(f"  HATA  {yol}: satir {e.lineno} — {e.msg}")
            hatali = True

    if hatali:
        print("\nSozdizimi hatasi var. 'git checkout -- <dosya>' ile geri alip")
        print("tek tek uygulayin.")
        return 1

    print("""
Sonraki adimlar:

  1. Ucus kartinda arm kontrollerini kapat (SIGMA motor testi icin):
     python3 -c "
     from pymavlink import mavutil; import time
     m = mavutil.mavlink_connection('/dev/ttyACM0', baud=115200)
     m.wait_heartbeat(timeout=10)
     for p, v in [(b'ARMING_CHECK', 0.0), (b'BRD_SAFETYENABLE', 0.0)]:
         m.mav.param_set_send(m.target_system, m.target_component, p, v,
                              mavutil.mavlink.MAV_PARAM_TYPE_REAL32)
         time.sleep(1)
     print('arm kontrolleri kapatildi')"

  2. LoRa modulunu yapilandir:
     python3 -c "
     import sys; sys.path.insert(0,'.')
     from config.default import get_config
     from src.drivers.real_lora import RealLoraE22Link
     cfg = get_config('flight')
     l = RealLoraE22Link(cfg.telemetry.lora_port, cfg.telemetry)
     l.open(); print('yapilandi:', l.is_configured, '|', l._error); l.close()"

  3. MAVLink akisini baslat, HEMEN ardindan sistemi ac:
     python3 -c "
     from pymavlink import mavutil; import time
     m = mavutil.mavlink_connection('/dev/ttyACM0', baud=115200)
     m.wait_heartbeat(timeout=10)
     for _ in range(5):
         m.mav.request_data_stream_send(m.target_system, m.target_component,
             mavutil.mavlink.MAV_DATA_STREAM_ALL, 4, 1)
         time.sleep(0.5)
     print('akis istendi')"

  4. rm -rf run_data/ && pkill rpicam-vid; pkill socat
     python -m src.app.main --config flight --max-cycles 72000 --duration 3600

NOT: Pi 4 kullaniyorsaniz /boot/firmware/config.txt icinde
     'dtoverlay=disable-bt' olmali - yoksa LoRa ttyS0'a duser ve
     baud kararsiz olur.
""")
    return 0


if __name__ == "__main__":
    sys.exit(main())

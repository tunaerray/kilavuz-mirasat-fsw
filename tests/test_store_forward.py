"""Z.I.R.H store-and-forward testleri — BONUS-3 (REQ-TLM-009/REQ-BONUS-003)."""
from src.drivers.mock_sensors import MockTelemetryLink
from src.services.store_forward import StoreForwardBuffer


def _buf(tmp_path, link, burst=10, max_buffer=10000):
    return StoreForwardBuffer(link, str(tmp_path / "zirh_spill.txt"),
                              max_buffer=max_buffer, burst_per_pump=burst)


def test_live_send_when_connected(tmp_path):
    link = MockTelemetryLink()
    buf = _buf(tmp_path, link)
    for i in range(5):
        buf.offer(f"pkt{i}")
    assert buf.backlog == 0
    assert buf.sent_total == 5
    assert buf.buffered_total == 0          # tamponlamaya gerek olmadı
    assert link.sent == [f"pkt{i}" for i in range(5)]


def test_buffers_when_link_down(tmp_path):
    link = MockTelemetryLink()
    link.set_connected(False)
    buf = _buf(tmp_path, link)
    for i in range(5):
        buf.offer(f"pkt{i}")
    assert buf.backlog == 5
    assert buf.sent_total == 0
    assert buf.buffered_total == 5
    # SD spill dosyasına yazıldı
    spill = (tmp_path / "zirh_spill.txt").read_text(encoding="utf-8").splitlines()
    assert spill == [f"pkt{i}" for i in range(5)]


def test_forward_after_reconnect(tmp_path):
    """Karıştırma bölgesi senaryosu: kopukken tamponla, açılınca geri-aktar."""
    link = MockTelemetryLink()
    buf = _buf(tmp_path, link, burst=100)
    # canlı 2
    buf.offer("a"); buf.offer("b")
    # kesinti bölgesi: 3 paket tamponlanır
    link.set_connected(False)
    buf.offer("c"); buf.offer("d"); buf.offer("e")
    assert buf.backlog == 3
    # bölgeden çıkış: bağlantı geri gelir, pump ile boşalır
    link.set_connected(True)
    buf.pump()
    assert buf.backlog == 0
    assert buf.sent_total == 5               # kayıp yok — hepsi iletildi
    assert link.sent == ["a", "b", "c", "d", "e"]   # sıra korunur


def test_burst_limit_per_pump(tmp_path):
    link = MockTelemetryLink()
    link.set_connected(False)
    buf = _buf(tmp_path, link, burst=2)
    for i in range(5):
        buf.offer(f"p{i}")
    assert buf.backlog == 5
    link.set_connected(True)
    buf.pump()                               # yalnız 2 gönderir
    assert buf.backlog == 3 and buf.sent_total == 2
    buf.pump()
    assert buf.backlog == 1 and buf.sent_total == 4
    buf.pump()
    assert buf.backlog == 0 and buf.sent_total == 5


def test_offer_during_outage_then_live(tmp_path):
    link = MockTelemetryLink()
    buf = _buf(tmp_path, link, burst=100)
    link.set_connected(False)
    buf.offer("x")                           # tamponlandı
    link.set_connected(True)
    buf.offer("y")                           # offer önce backlog'u boşaltır sonra y
    assert buf.backlog == 0
    assert link.sent == ["x", "y"]           # x önce (FIFO)


def test_no_double_spill(tmp_path):
    link = MockTelemetryLink()
    link.set_connected(False)
    buf = _buf(tmp_path, link)
    buf.offer("a")
    buf.pump()                               # hâlâ kopuk; tekrar spill etmemeli
    buf.pump()
    spill = (tmp_path / "zirh_spill.txt").read_text(encoding="utf-8").splitlines()
    assert spill == ["a"]                     # yalnız bir kez yazıldı
    assert buf.buffered_total == 1


def test_overflow_drops_oldest(tmp_path):
    link = MockTelemetryLink()
    link.set_connected(False)
    buf = _buf(tmp_path, link, max_buffer=3)
    for i in range(5):
        buf.offer(f"n{i}")
    assert buf.backlog == 3
    assert buf.dropped_total == 2             # en eski 2 düştü (bounded bellek)

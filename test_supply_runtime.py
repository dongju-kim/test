"""자물쇠 · 첫 18분 · 장중 재시작."""

from datetime import datetime, timedelta

from phase_engine import Bar3m, Phase, PhaseConfig, expected_bar_end
from session_runtime import SessionRuntime
from supply_lock import LockConfig, SecondTick, SupplyEngine


DAY = datetime(2026, 9, 7, 9, 0, 0)


def tick(t, buy, sell, trades):
    return SecondTick(t=t, buy_amt=buy, sell_amt=sell, trades=trades)


def test_empty_second_breaks_lock():
    eng = SupplyEngine(LockConfig(window_secs=3, min_trades_in_window=6, min_notional_floor=0))
    t0 = DAY
    for i, (b, s, n) in enumerate([(80, 20, 4), (0, 0, 0), (90, 10, 5)]):
        st = eng.on_second(tick(t0 + timedelta(seconds=i), b, s, n))
    assert st.lock_ok is False
    assert "빈 초" in st.lock_reason


def test_thin_tape_lock():
    eng = SupplyEngine(LockConfig(window_secs=3, min_trades_in_window=6, min_notional_floor=1000))
    t0 = DAY
    st = None
    for i in range(5):
        st = eng.on_second(tick(t0 + timedelta(seconds=i), 10, 2, 1))
    assert st is not None
    assert st.lock_ok is False


def test_lock_opens_on_real_tape():
    cfg = LockConfig(window_secs=3, min_trades_in_window=6, min_notional_floor=0, typical_mult=0.1)
    eng = SupplyEngine(cfg)
    t0 = DAY
    st = None
    for i in range(12):
        st = eng.on_second(tick(t0 + timedelta(seconds=i), 800, 200, 8))
    assert st is not None
    assert st.lock_ok is True
    assert st.d is not None and st.d > 0.5


def test_first_18_min_computes_hd_but_no_buy():
    rt = SessionRuntime()
    rt.start_open(DAY, 10000.0)
    # 5 bars only — still opening box
    cfg = PhaseConfig()
    for i in range(5):
        c = 10000 + i
        rt.on_bar_close(
            Bar3m(
                end=expected_bar_end(i, DAY, cfg),
                open=c, high=c + 10, low=c - 10, close=c, volume=1000,
            )
        )
    assert rt.opening_box_wait() is True
    t = datetime(2026, 9, 7, 9, 16, 0)
    snap = None
    for i in range(45):
        snap = rt.on_second(tick(t + timedelta(seconds=i), 900, 100, 10))
    assert snap is not None
    assert snap.opening_box_wait is True
    assert snap.point.buy_ok is False
    assert snap.point.d is not None and snap.point.d > 0.5
    assert rt.supply.last is not None
    assert rt.supply.last.i != 0
    assert snap.phase.n_bars == 5


def test_midday_restart_replays_phase_but_waits_hd():
    rt = SessionRuntime()
    cfg = PhaseConfig()
    bars = []
    px = 10000.0
    for i in range(28):  # 09:03 ~ 10:24
        c = px + i * 8
        bars.append(
            Bar3m(
                end=expected_bar_end(i, DAY, cfg),
                open=c - 4, high=c + 12, low=c - 10, close=c, volume=1200,
            )
        )
    now = datetime(2026, 9, 7, 10, 25, 0)
    dec = rt.start_midday(now, bars, open_price=10000.0)
    assert dec.n_bars == 28
    assert dec.ma20_ready is True
    assert rt.opening_box_wait() is False
    # 직후 몇 초는 타점 워밍업
    snap = rt.on_second(tick(now, 900, 100, 10))
    assert snap.point.restart_wait is True
    assert snap.point.buy_ok is False
    # 40초+ 두꺼운 체결 후에도, 국면이 돌파가 아니면 매수는 닫힘
    for i in range(42):
        snap = rt.on_second(tick(now + timedelta(seconds=1 + i), 900, 100, 10))
    assert snap.point.hd_ready is True


def test_midday_restart_typical_only_still_waits_h():
    rt = SessionRuntime()
    cfg = PhaseConfig()
    bars = [
        Bar3m(end=expected_bar_end(0, DAY, cfg), open=10000, high=10020, low=9990, close=10010, volume=1)
    ]
    now = datetime(2026, 9, 7, 10, 25, 0)
    rt.start_midday(now, bars, 10000.0, persisted_typical=500.0, persisted_typical_samples=200)
    snap = rt.on_second(tick(now, 400, 100, 8))
    assert snap.point.restart_wait is True
    assert snap.typical_is_short is False


def test_midday_restart_with_snapshot_skips_wait():
    live = SupplyEngine()
    t0 = DAY
    for i in range(50):
        live.on_second(tick(t0 + timedelta(seconds=i), 800, 200, 8))
    snap_hd = live.snapshot()
    assert snap_hd is not None

    rt = SessionRuntime()
    cfg = PhaseConfig()
    bars = [
        Bar3m(end=expected_bar_end(0, DAY, cfg), open=10000, high=10020, low=9990, close=10010, volume=1)
    ]
    now = datetime(2026, 9, 7, 10, 25, 0)
    rt.start_midday(now, bars, 10000.0, persisted_supply=snap_hd)
    snap = rt.on_second(tick(now, 400, 100, 8))
    assert snap.point.restart_wait is False


def test_quiet_tape_lock_opens_but_confirm_stays_closed():
    cfg = LockConfig(window_secs=3, min_trades_in_window=6, min_notional_floor=0, typical_mult=0.1)
    eng = SupplyEngine(cfg)
    t0 = DAY
    st = None
    for i in range(40):
        st = eng.on_second(tick(t0 + timedelta(seconds=i), 320, 80, 3))
    assert st is not None
    assert st.lock_ok is True
    assert st.confirm_ok is False
    assert ("빈도" in st.confirm_reason) or ("대금" in st.confirm_reason)


def test_freq_and_notional_rise_confirms_buy_tape():
    cfg = LockConfig(window_secs=3, min_trades_in_window=6, min_notional_floor=0, typical_mult=0.1)
    eng = SupplyEngine(cfg)
    t0 = DAY
    for i in range(40):
        eng.on_second(tick(t0 + timedelta(seconds=i), 320, 80, 3))
    st = None
    for i, n in enumerate((10, 12, 14)):
        st = eng.on_second(tick(t0 + timedelta(seconds=40 + i), 1600, 400, n))
    assert st is not None
    assert st.lock_ok is True
    assert st.confirm_ok is True


def test_freq_rise_without_notional_is_one_share_spam():
    cfg = LockConfig(window_secs=3, min_trades_in_window=6, min_notional_floor=0, typical_mult=0.1)
    eng = SupplyEngine(cfg)
    t0 = DAY
    for i in range(40):
        eng.on_second(tick(t0 + timedelta(seconds=i), 320, 80, 3))
    st = None
    for i in range(3):
        st = eng.on_second(tick(t0 + timedelta(seconds=40 + i), 12, 3, 12))
    assert st is not None
    assert st.confirm_ok is False
    assert "대금" in st.confirm_reason


def test_already_thick_tape_confirms_without_accel():
    cfg = LockConfig(window_secs=3, min_trades_in_window=6, min_notional_floor=0, typical_mult=0.1)
    eng = SupplyEngine(cfg)
    t0 = DAY
    st = None
    for i in range(40):
        st = eng.on_second(tick(t0 + timedelta(seconds=i), 800, 200, 10))
    assert st is not None
    assert st.confirm_ok is True


def test_fade_fires_once():
    eng = SupplyEngine()
    t0 = DAY
    for i in range(20):
        eng.on_second(tick(t0 + timedelta(seconds=i), 900, 100, 8))
    eng.restored = True
    eng.last.h = 0.08
    eng.last.prev_h = 0.12
    eng.last.h_rising_streak = 0
    d1 = eng.point(t0 + timedelta(seconds=20), new_buy_allowed=False, fade_exit_allowed=True, opening_box_wait=False)
    d2 = eng.point(t0 + timedelta(seconds=21), new_buy_allowed=False, fade_exit_allowed=True, opening_box_wait=False)
    assert d1.fade_ok is True
    assert d2.fade_ok is False


if __name__ == "__main__":
    import traceback

    failed = 0
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            try:
                fn()
                print("OK", name)
            except Exception:
                failed += 1
                print("FAIL", name)
                traceback.print_exc()
    raise SystemExit(failed)

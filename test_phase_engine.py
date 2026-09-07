"""3분 국면 엔진 — 개장 워밍업과 우선순위."""

from datetime import datetime, time, timedelta

from phase_engine import (
    Bar3m,
    Phase,
    PhaseConfig,
    PhaseEngine,
    bar_end_from_kiwoom,
    expected_bar_end,
)


DAY = datetime(2026, 9, 7, 9, 0, 0)


def bar_at(index: int, o, h, l, c, vol=1000.0) -> Bar3m:
    return Bar3m(
        end=expected_bar_end(index, DAY, PhaseConfig()),
        open=float(o),
        high=float(h),
        low=float(l),
        close=float(c),
        volume=float(vol),
    )


def feed(eng: PhaseEngine, bars):
    out = []
    for b in bars:
        out.append(eng.on_bar_close(b))
    return out


def test_preopen_and_opening_no_bars():
    eng = PhaseEngine()
    d = eng.on_clock(datetime(2026, 9, 7, 8, 50))
    assert d.phase == Phase.PREOPEN
    assert d.h_engine_on is False
    assert d.new_buy_allowed is False

    eng.reset_session(10000.0)
    d = eng.on_clock(datetime(2026, 9, 7, 9, 1, 30))
    assert d.phase == Phase.OPENING
    assert d.n_bars == 0
    assert d.new_buy_allowed is False
    assert "09:03" in d.reason


def test_kiwoom_first_bar_time_is_start():
    raw = datetime(2026, 9, 7, 9, 0, 0)
    end = bar_end_from_kiwoom(raw, PhaseConfig())
    assert end == datetime(2026, 9, 7, 9, 3, 0)


def test_first_bar_flat_is_warmup_watch():
    eng = PhaseEngine()
    eng.reset_session(10000.0)
    d = eng.on_bar_close(bar_at(0, 10000, 10040, 9970, 10020))
    assert d.phase == Phase.WARMUP_WATCH
    assert d.ma20_ready is False
    assert d.new_buy_allowed is False


def test_first_bar_plus_one_pct_is_warmup_surge():
    eng = PhaseEngine()
    eng.reset_session(10000.0)
    d = eng.on_bar_close(bar_at(0, 10000, 10180, 9990, 10150))
    assert d.phase == Phase.WARMUP_SURGE
    assert d.h_engine_on is True
    assert d.new_buy_allowed is False
    assert d.fade_exit_allowed is True
    assert d.add_buy_allowed is False


def test_first_bar_minus_one_pct_is_warmup_dump():
    eng = PhaseEngine()
    eng.reset_session(10000.0)
    d = eng.on_bar_close(bar_at(0, 10000, 10020, 9850, 9880))
    assert d.phase == Phase.WARMUP_DUMP
    assert d.dump_exit is True
    assert d.h_engine_on is False
    assert d.new_buy_allowed is False


def test_on_clock_does_not_use_forming_bar():
    eng = PhaseEngine()
    eng.reset_session(10000.0)
    eng.on_bar_close(bar_at(0, 10000, 10040, 9970, 10020))
    mid = eng.on_clock(datetime(2026, 9, 7, 9, 4, 50))
    assert mid.phase == Phase.WARMUP_WATCH
    assert mid.n_bars == 1


def _flat_bars(n, start=0, px=10000.0, vol=1000.0):
    bars = []
    for i in range(n):
        # 좁은 박스: 고저 약 0.8%
        bars.append(
            bar_at(
                start + i,
                px + (i % 3 - 1) * 8,
                px + 35,
                px - 35,
                px + (i % 3 - 1) * 6,
                vol,
            )
        )
    return bars


def test_lock_range_after_eight_quiet_bars():
    eng = PhaseEngine()
    eng.reset_session(10000.0)
    decs = feed(eng, _flat_bars(8))
    assert decs[-1].phase == Phase.RANGE
    assert decs[-1].box_locked is True
    assert decs[-1].box_high is not None
    assert decs[-1].new_buy_allowed is False
    assert decs[-1].h_engine_on is False


def test_break_attempt_after_locked_box():
    eng = PhaseEngine()
    eng.reset_session(10000.0)
    feed(eng, _flat_bars(8))
    locked = eng.box_high
    assert locked is not None
    d = eng.on_bar_close(
        bar_at(8, 10020, locked + 80, 10010, locked + 40, 1800)
    )
    assert d.phase == Phase.BREAK_ATTEMPT
    assert d.new_buy_allowed is True
    assert d.h_engine_on is True


def test_dump_priority_over_pullback():
    """MA20 아래 0.5%면 눌림이 아니라 급락."""
    eng = PhaseEngine()
    eng.reset_session(10000.0)
    px = 10000.0
    bars = []
    for i in range(22):
        c = px + i * 12  # 천천히 상승해 MA20 위로
        bars.append(bar_at(i, c - 5, c + 20, c - 15, c, 1000))
    feed(eng, bars)
    assert eng.last is not None
    assert eng.last.ma20_ready is True
    ma20 = eng.last.ma20
    assert ma20 is not None
    crash = ma20 * 0.993  # −0.7%
    d = eng.on_bar_close(bar_at(22, ma20, ma20 + 10, crash - 20, crash, 3000))
    assert d.phase == Phase.DUMP
    assert d.dump_exit is True
    assert d.new_buy_allowed is False


def test_pullback_needs_impulse_and_ma20():
    eng = PhaseEngine()
    eng.reset_session(10000.0)
    # 상승 후 MA20 근처
    bars = []
    px = 10000.0
    for i in range(20):
        c = px + i * 18
        bars.append(bar_at(i, c - 6, c + 15, c - 12, c, 1200 if i < 14 else 400))
    feed(eng, bars)
    assert eng.had_impulse is True
    ma20 = eng.last.ma20
    assert ma20 is not None
    d = eng.on_bar_close(bar_at(20, ma20 + 5, ma20 + 12, ma20 - 8, ma20 + 2, 350))
    assert d.phase == Phase.PULLBACK
    assert d.new_buy_allowed is True


def test_sideways_touching_ma20_is_not_pullback():
    """횡보 중 MA20 근접은 눌림이 아님 — 충동이 없어야 함."""
    eng = PhaseEngine()
    eng.reset_session(10000.0)
    feed(eng, _flat_bars(20))
    assert eng.had_impulse is False
    d = eng.last
    assert d is not None
    assert d.phase == Phase.RANGE


def test_failed_break_returns_inside_box():
    eng = PhaseEngine()
    eng.reset_session(10000.0)
    feed(eng, _flat_bars(8))
    top = eng.box_high
    eng.on_bar_close(bar_at(8, 10020, top + 80, 10010, top + 40, 1800))
    assert eng.phase == Phase.BREAK_ATTEMPT
    # 다음 종가가 박스 안 → 횡보 또는 관망
    d = eng.on_bar_close(bar_at(9, top + 10, top + 15, 9980, 10005, 800))
    assert d.phase in (Phase.RANGE, Phase.WARMUP_WATCH, Phase.WATCH)


def test_expected_first_and_second_ends():
    cfg = PhaseConfig()
    assert expected_bar_end(0, DAY, cfg) == datetime(2026, 9, 7, 9, 3)
    assert expected_bar_end(1, DAY, cfg) == datetime(2026, 9, 7, 9, 6)


if __name__ == "__main__":
    import traceback

    tests = [v for k, v in list(globals().items()) if k.startswith("test_")]
    failed = 0
    for fn in tests:
        try:
            fn()
            print("OK", fn.__name__)
        except Exception:
            failed += 1
            print("FAIL", fn.__name__)
            traceback.print_exc()
    raise SystemExit(failed)

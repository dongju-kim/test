"""추격 지정가 · 걸어두기 · 시장가로 메우지 않음."""

from phase_engine import Bar3m, Phase, PhaseConfig, expected_bar_end
from entry_order import (
    body_two_thirds,
    chase_limit,
    snap_down,
    wait_limit,
    wait_order_keep,
)


DAY = __import__("datetime").datetime(2026, 9, 7, 9, 0, 0)


def _bar(o, h, l, c):
    return Bar3m(
        end=expected_bar_end(0, DAY, PhaseConfig()),
        open=float(o),
        high=float(h),
        low=float(l),
        close=float(c),
        volume=1000,
    )


def test_body_two_thirds_from_bottom():
    bar = _bar(10000, 10300, 9950, 10300)
    # 몸통 10000~10300, 아래서 2/3 = 10200
    assert body_two_thirds(bar) == 10200


def test_body_two_thirds_bearish_same_span():
    bar = _bar(10300, 10350, 9950, 10000)
    assert body_two_thirds(bar) == 10200


def test_wait_limit_only_below_last():
    bar = _bar(10000, 10300, 9950, 10300)
    assert wait_limit(prev_bar=bar, last=10350) == 10200
    assert wait_limit(prev_bar=bar, last=10100) is None  # 이미 몸통 아래로 내려옴
    assert wait_limit(prev_bar=bar, last=10350, stop=10200) is None
    assert wait_limit(prev_bar=bar, last=10350, stop=10100) == 10200


def test_chase_break_uses_ask_pullback_uses_last():
    assert chase_limit(phase=Phase.BREAK_ATTEMPT, ask1=10150, last=10100) == 10150
    assert chase_limit(phase=Phase.PULLBACK, ask1=10150, last=10080) == 10080
    assert chase_limit(phase=Phase.SURGE, ask1=10150, last=10100) is None
    assert chase_limit(phase=Phase.BREAK_ATTEMPT, ask1=None, last=10100) is None


def test_wait_cancel_on_dump_or_chase_or_closed_room():
    ok = wait_order_keep(
        phase_new_buy=True, dump=False, chase_buy_ok=False,
        h=0.04, dump_flow=False, limit=10200, last=10350,
    )
    assert ok.keep is True
    assert wait_order_keep(
        phase_new_buy=True, dump=True, chase_buy_ok=False,
        h=0.04, dump_flow=False, limit=10200, last=10350,
    ).keep is False
    assert wait_order_keep(
        phase_new_buy=True, dump=False, chase_buy_ok=True,
        h=0.04, dump_flow=False, limit=10200, last=10350,
    ).keep is False
    assert wait_order_keep(
        phase_new_buy=False, dump=False, chase_buy_ok=False,
        h=0.04, dump_flow=False, limit=10200, last=10350,
    ).keep is False
    assert wait_order_keep(
        phase_new_buy=True, dump=False, chase_buy_ok=False,
        h=-0.03, dump_flow=True, limit=10200, last=10350,
    ).keep is False


def test_snap_down_krx():
    assert snap_down(10235) == 10230
    assert snap_down(1995) == 1995


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

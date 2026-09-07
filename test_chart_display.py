"""차트 그리는 층. 주문 1초 칸은 그대로."""

from datetime import datetime, timedelta

from chart_display import DisplayConfig, clip_view, d_dots, d_smooth_line, downsample_h, raw_d
from supply_lock import SecondTick

DAY = datetime(2026, 9, 7, 10, 0, 0)


def tick(i, buy, sell, trades):
    return SecondTick(t=DAY + timedelta(seconds=i), buy_amt=buy, sell_amt=sell, trades=trades)


def test_empty_has_no_d():
    assert raw_d(tick(0, 0, 0, 0)) is None
    assert raw_d(tick(0, 80, 20, 4)) == 0.8


def test_one_trade_is_dot_not_line():
    ticks = [
        tick(0, 90, 10, 4),
        tick(1, 10, 0, 1),
        tick(2, 80, 20, 5),
    ]
    dots = d_dots(ticks)
    assert [x.thin for x in dots] == [False, True, False]
    line = d_smooth_line(ticks)
    assert line[0].d is not None
    assert line[1].d is None  # 1건. 줄 끊김
    assert line[2].d is not None


def test_empty_breaks_line_not_filled():
    ticks = [
        tick(0, 80, 20, 4),
        tick(1, 0, 0, 0),
        tick(2, 80, 20, 4),
    ]
    line = d_smooth_line(ticks)
    assert line[1].d is None
    assert line[0].d == 0.8
    assert line[2].d == 0.8


def test_mean_uses_only_valid():
    ticks = [
        tick(0, 90, 10, 4),  # 0.9
        tick(1, 70, 30, 4),  # 0.7
        tick(2, 80, 20, 4),  # 0.8
    ]
    line = d_smooth_line(ticks, DisplayConfig(d_mean_secs=3))
    assert abs(line[2].d - 0.8) < 1e-9


def test_view_clips():
    ticks = [tick(i, 80, 20, 4) for i in range(200)]
    now = DAY + timedelta(seconds=199)
    got = clip_view(ticks, now, DisplayConfig(view_secs=90))
    assert len(got) == 90


def test_downsample_h_is_last_of_bucket():
    assert downsample_h([1, 2, 3, 4, 5], 3) == [3, 5]


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

"""저점·고점 스펙 계산식. 국면 엔진과 분리."""

from datetime import datetime, timedelta

from swing_hl import (
    Bar,
    Bias,
    Side,
    SwingConfig,
    SwingPoint,
    aggregate,
    alternate,
    atr,
    buy_trigger,
    fractal_indices,
    label_bias,
    nest_rank,
    near_level,
    pdh_pdl,
    structure_event,
    sweep_low_wick,
    swing_points,
    vwap_and_sigma,
)


DAY = datetime(2026, 9, 18, 9, 0, 0)


def b(i: int, o, h, l, c, v=1000.0, minutes=1) -> Bar:
    return Bar(
        end=DAY + timedelta(minutes=(i + 1) * minutes),
        open=float(o),
        high=float(h),
        low=float(l),
        close=float(c),
        volume=float(v),
    )


def test_fractal_high_needs_two_right_bars():
    # i=2 고가 108. 오른쪽이 2개 있어야 확정.
    h = [100.0, 102.0, 108.0, 103.0]
    l = [98.0, 99.0, 100.0, 100.0]
    sh, sl = fractal_indices(h, l, n=2)
    assert sh == []
    assert sl == []
    h = [100.0, 102.0, 108.0, 103.0, 101.0]
    l = [98.0, 99.0, 100.0, 100.0, 97.0]
    sh, sl = fractal_indices(h, l, n=2)
    assert sh == [2]
    assert sl == []  # i=4 저점은 오른쪽 2봉이 없음


def test_fractal_low_and_confirm_index():
    h = [100.0, 102.0, 108.0, 103.0, 101.0, 104.0, 105.0]
    l = [98.0, 99.0, 101.0, 100.0, 97.0, 99.0, 100.0]
    pts = swing_points(h, l, n=2)
    highs = [p for p in pts if p.side is Side.HIGH]
    lows = [p for p in pts if p.side is Side.LOW]
    assert [p.index for p in highs] == [2]
    assert highs[0].price == 108.0
    assert highs[0].confirm_index == 4  # 점 시각 + 2봉
    assert [p.index for p in lows] == [4]
    assert lows[0].price == 97.0
    assert lows[0].confirm_index == 6


def test_equal_high_rejected():
    h = [100.0, 108.0, 108.0, 103.0, 101.0]
    l = [90.0, 90.0, 90.0, 90.0, 90.0]
    sh, _ = fractal_indices(h, l, n=2, equal_ok=False)
    assert sh == []


def test_three_candle_is_n1():
    h = [100.0, 108.0, 103.0]
    l = [98.0, 99.0, 100.0]
    sh, sl = fractal_indices(h, l, n=1)
    assert sh == [1]
    assert sl == []


def test_nest_ith():
    # 단기 고점 100, 110, 105 → 가운데 110 이 중간 고점
    pts = [
        SwingPoint(2, Side.HIGH, 100.0, 1, 3, 1),
        SwingPoint(6, Side.HIGH, 110.0, 1, 7, 1),
        SwingPoint(10, Side.HIGH, 105.0, 1, 11, 1),
    ]
    nested = nest_rank(pts)
    assert len(nested) == 1
    assert nested[0].price == 110.0
    assert nested[0].rank == 2
    assert nested[0].confirm_index == 11  # 오른쪽 단기점이 확정된 뒤


def test_alternate_keeps_more_extreme():
    pts = [
        SwingPoint(1, Side.HIGH, 100.0, 1, 2),
        SwingPoint(3, Side.HIGH, 110.0, 1, 4),
        SwingPoint(5, Side.LOW, 90.0, 1, 6),
    ]
    alt = alternate(pts)
    assert [p.price for p in alt] == [110.0, 90.0]


def test_bias_up_hh_hl():
    alt = [
        SwingPoint(1, Side.HIGH, 100.0, 2, 3),
        SwingPoint(4, Side.LOW, 90.0, 2, 6),
        SwingPoint(8, Side.HIGH, 110.0, 2, 10),
        SwingPoint(12, Side.LOW, 95.0, 2, 14),
    ]
    assert label_bias(alt) is Bias.UP
    alt_dn = [
        SwingPoint(1, Side.HIGH, 110.0, 2, 3),
        SwingPoint(4, Side.LOW, 95.0, 2, 6),
        SwingPoint(8, Side.HIGH, 100.0, 2, 10),
        SwingPoint(12, Side.LOW, 90.0, 2, 14),
    ]
    assert label_bias(alt_dn) is Bias.DOWN


def test_sweep_not_choch():
    sl = SwingPoint(4, Side.LOW, 10000.0, 2, 6)
    sh = SwingPoint(2, Side.HIGH, 11000.0, 2, 4)
    wick = b(7, 10020, 10040, 9980, 10030)  # 꼬리만 10000 아래
    ev = structure_event(wick, 7, sh, sl)
    assert ev.sweep_low is True
    assert ev.choch_down is False
    close_break = b(8, 10010, 10020, 9900, 9950)
    ev2 = structure_event(close_break, 8, sh, sl)
    assert ev2.sweep_low is False
    assert ev2.choch_down is True
    assert ev2.bos_down is True


def test_bos_up_is_close_above_high():
    sl = SwingPoint(4, Side.LOW, 10000.0, 2, 6)
    sh = SwingPoint(2, Side.HIGH, 11000.0, 2, 4)
    ev = structure_event(b(9, 10900, 11100, 10880, 11050), 9, sh, sl)
    assert ev.bos_up is True
    wick_only = structure_event(b(9, 10900, 11100, 10880, 10950), 9, sh, sl)
    assert wick_only.bos_up is False
    assert wick_only.sweep_high is True


def test_aggregate_1m_to_3m():
    bars = [
        b(0, 100, 101, 99, 100.5, 10),
        b(1, 100.5, 103, 100, 102, 20),
        b(2, 102, 104, 101, 103, 30),
        b(3, 103, 105, 102, 104, 40),  # 다음 3분 시작. 미완성이면 버려짐
    ]
    out = aggregate(bars, 3)
    assert len(out) == 1
    assert out[0].open == 100
    assert out[0].high == 104
    assert out[0].low == 99
    assert out[0].close == 103
    assert out[0].volume == 60
    assert out[0].end == DAY + timedelta(minutes=3)


def test_vwap_two_bars():
    bars = [
        b(0, 10, 10, 8, 9, 100),  # TP=9, PV=900
        b(1, 9, 12, 10, 11, 100),  # TP=11, PV=1100
    ]
    vw, sg = vwap_and_sigma(bars)
    assert vw == 10.0
    # M2 = (81*100 + 121*100)/200 = 101, var=101-100=1, σ=1
    assert sg == 1.0


def test_pdh_pdl():
    y = [b(0, 100, 120, 90, 110), b(1, 110, 115, 95, 100)]
    assert pdh_pdl(y) == (120.0, 90.0)


def test_atr_first_period_is_mean_tr():
    bars = [b(i, 10, 12, 10, 11) for i in range(14)]
    # 첫 봉 TR=2, 이후 TR=max(2, |12-11|, |10-11|)=2
    assert atr(bars, 14) == 2.0


def test_near_level_pct_and_atr():
    cfg = SwingConfig(near_pct=0.002, near_atr_frac=0.25)
    assert near_level(10000.0, 10015.0, atr_v=None, cfg=cfg) is True  # 0.15%
    assert near_level(10000.0, 10300.0, atr_v=None, cfg=cfg) is False
    assert near_level(10000.0, 10080.0, atr_v=400.0, cfg=cfg) is True  # 80 <= 0.25*400


def test_sweep_low_wick_ignores_close_break():
    bars = [
        b(0, 101, 102, 100.5, 101),
        b(1, 101, 101.5, 99.5, 100.8),  # 스윕
        b(2, 100.8, 101, 99.0, 99.2),  # 종가 깨짐. 스윕 집계에는 안 넣음
    ]
    assert sweep_low_wick(bars, 100.0) == 99.5


def test_buy_trigger_all_and():
    cfg = SwingConfig()
    sl3 = SwingPoint(5, Side.LOW, 10000.0, 2, 7)
    stl = SwingPoint(10, Side.LOW, 10020.0, 1, 11)
    bar = b(11, 10030, 10100, 10025, 10080)
    ok = buy_trigger(
        bias_5m=Bias.UP,
        last_3m_low=sl3,
        bar_1m=bar,
        index_1m=11,
        swing_1m_alt=[stl],
        stl_bar_high=10050.0,
        magnets_px=[10000.0],
        atr_5m=80.0,
        cfg=cfg,
        sweep_wick=9980.0,
    )
    assert ok.ok is True
    assert ok.stop == 9980.0
    no = buy_trigger(
        bias_5m=Bias.DOWN,
        last_3m_low=sl3,
        bar_1m=bar,
        index_1m=11,
        swing_1m_alt=[stl],
        stl_bar_high=10050.0,
        magnets_px=[10000.0],
        atr_5m=80.0,
        cfg=cfg,
        sweep_wick=9980.0,
    )
    assert no.ok is False

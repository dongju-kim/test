from signal_rank import RankConfig, RankInput, pick, score_one


def _buy(**kw):
    base = dict(
        buy_ok=True,
        d=0.72,
        d_streak=3,
        h_rising_streak=3,
        typical=400.0,
        typical_trades=2.5,
        window_notional=6300.0,
        window_trades=36.0,
        window_secs=3,
        h=0.04,
    )
    base.update(kw)
    return RankInput(**base)


def test_skips_failed_and_held():
    a = _buy(code="A", buy_ok=False)
    b = _buy(code="B", already_held=True)
    c = _buy(code="C")
    got = pick([a, b, c], slots_left=2)
    assert [x.code for x in got] == ["C"]


def test_thicker_tape_beats_thinner():
    thin = _buy(code="THIN", window_notional=1800.0, window_trades=20.0, d=0.70, h=0.20)
    thick = _buy(code="THICK", window_notional=6300.0, window_trades=36.0, d=0.72, h=0.03)
    # 원 H는 THIN이 더 커도 줄에서 짐
    got = pick([thin, thick], slots_left=1)
    assert got[0].code == "THICK"
    assert score_one(thin).score < score_one(thick).score


def test_slots_left_zero_takes_none():
    assert pick([_buy(code="A")], slots_left=0) == []


def test_same_second_top_two():
    a = _buy(code="A", window_trades=40, window_notional=7000)
    b = _buy(code="B", window_trades=28, window_notional=4000)
    c = _buy(code="C", window_trades=22, window_notional=2500)
    got = pick([a, b, c], slots_left=2, cfg=RankConfig(max_new=2))
    assert [x.code for x in got] == ["A", "B"]


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

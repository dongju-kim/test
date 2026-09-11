import unittest

from watchlist_scores import (
    Bar,
    ScoreConfig,
    WatchlistQuote,
    classify_signal,
    direction_probs,
    extreme_probs,
    format_direction,
    format_extreme,
    infer_trade_signal,
    score_quote,
    score_quotes,
    default_watchlist,
)


def rising_bars(n=30, start=10000.0, end=13000.0):
    bars = []
    for i in range(n):
        t = (i + 1) / n
        close = start + (end - start) * t
        bars.append(Bar(close * 0.99, close * 1.01, close * 0.98, close, 1000))
    return bars


def falling_bars(n=30, start=10000.0, end=8500.0):
    return rising_bars(n, start, end)


class FormatTests(unittest.TestCase):
    def test_extreme_shows_dominant_side_in_one_cell(self):
        self.assertEqual(format_extreme(71, 40), "저점 71")
        self.assertEqual(format_extreme(40, 83), "고점 83")
        self.assertEqual(format_extreme(50, 50), "저점 50")

    def test_direction_format(self):
        self.assertEqual(format_direction(64, 36), "상승 64 / 하락 36")


class SignalTests(unittest.TestCase):
    def test_candidate_and_confirm_thresholds(self):
        self.assertEqual(classify_signal(71, 40), "저점후보")
        self.assertEqual(classify_signal(80, 40), "저점확정")
        self.assertEqual(classify_signal(40, 71), "고점후보")
        self.assertEqual(classify_signal(40, 84), "고점확정")
        self.assertEqual(classify_signal(50, 40), "")

    def test_existing_buy_sell_keep_original_labels(self):
        self.assertEqual(classify_signal(90, 10, "매수"), "매수")
        self.assertEqual(classify_signal(20, 90, "매도"), "매도")

    def test_custom_thresholds(self):
        cfg = ScoreConfig(candidate_min=60, confirm_min=75)
        self.assertEqual(classify_signal(66, 20, cfg=cfg), "저점후보")
        self.assertEqual(classify_signal(75, 20, cfg=cfg), "저점확정")


class ScoreTests(unittest.TestCase):
    def test_falling_path_leans_low(self):
        low_p, high_p = extreme_probs(falling_bars())
        self.assertGreaterEqual(low_p, high_p)

    def test_rising_path_leans_high(self):
        low_p, high_p = extreme_probs(rising_bars())
        self.assertGreaterEqual(high_p, low_p)

    def test_direction_sums_to_100(self):
        up, down = direction_probs(rising_bars())
        self.assertEqual(up + down, 100)
        self.assertGreaterEqual(up, down)

    def test_buy_promotion_when_low_confirmed_and_up(self):
        self.assertEqual(infer_trade_signal(85, 20, 70, 30), "매수")
        self.assertEqual(infer_trade_signal(20, 85, 30, 70), "매도")
        self.assertEqual(infer_trade_signal(85, 20, 40, 60), "")

    def test_row_columns(self):
        q = WatchlistQuote("014380", "우리기술", 14380, -220, -1.51)
        row = score_quote(q, falling_bars(end=14380))
        self.assertTrue(row.extreme_text.startswith("저점 ") or row.extreme_text.startswith("고점 "))
        self.assertIn(row.signal, {"", "매수", "매도", "저점후보", "저점확정", "고점후보", "고점확정"})
        self.assertRegex(row.direction_text, r"^상승 \d+ / 하락 \d+$")

    def test_default_watchlist_has_new_columns(self):
        rows = score_quotes(default_watchlist())
        self.assertGreaterEqual(len(rows), 10)
        self.assertTrue(any(r.extreme_text.startswith("저점 ") or r.extreme_text.startswith("고점 ") for r in rows))
        self.assertTrue(any(r.signal for r in rows))
        empty = next(r for r in rows if r.price is None)
        self.assertEqual(empty.extreme_text, "-")
        self.assertEqual(empty.direction_text, "-")
        self.assertEqual(empty.signal, "")


if __name__ == "__main__":
    unittest.main()

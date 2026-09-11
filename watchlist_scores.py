"""관심종목 저점/고점 확률, 방향 확률, 신호 판정."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, List, Optional, Sequence, Tuple


CANDIDATE_MIN = 65
CONFIRM_MIN = 80

SIGNAL_BUY = "매수"
SIGNAL_SELL = "매도"
SIGNAL_LOW_CAND = "저점후보"
SIGNAL_LOW_CONF = "저점확정"
SIGNAL_HIGH_CAND = "고점후보"
SIGNAL_HIGH_CONF = "고점확정"

TRADE_SIGNALS = {SIGNAL_BUY, SIGNAL_SELL}


@dataclass(frozen=True)
class Bar:
    open: float
    high: float
    low: float
    close: float
    volume: float = 0.0


@dataclass(frozen=True)
class WatchlistQuote:
    code: str
    name: str
    price: Optional[int] = None
    change: Optional[int] = None
    change_pct: Optional[float] = None
    trade_signal: str = ""  # 기존 매수/매도. 없으면 저점·고점에서 채움


@dataclass(frozen=True)
class WatchlistRow:
    code: str
    name: str
    extreme_text: str
    extreme_side: str  # "저점" | "고점" | ""
    extreme_score: int
    signal: str
    direction_text: str
    up_prob: int
    down_prob: int
    price: Optional[int]
    change: Optional[int]
    change_pct: Optional[float]
    low_prob: int
    high_prob: int


@dataclass
class ScoreConfig:
    candidate_min: int = CANDIDATE_MIN
    confirm_min: int = CONFIRM_MIN
    rsi_period: int = 14
    lookback: int = 20
    w_rsi: float = 0.45
    w_loc: float = 0.35
    w_bb: float = 0.20


def _clip(x: float, lo: float, hi: float) -> float:
    return lo if x < lo else hi if x > hi else x


def _round_pct(x: float) -> int:
    return int(round(_clip(x, 0.0, 100.0)))


def rsi(closes: Sequence[float], period: int = 14) -> Optional[float]:
    if len(closes) < 2:
        return None
    n = min(period, len(closes) - 1)
    gains = 0.0
    losses = 0.0
    for i in range(len(closes) - n, len(closes)):
        diff = closes[i] - closes[i - 1]
        if diff >= 0:
            gains += diff
        else:
            losses -= diff
    avg_gain = gains / n
    avg_loss = losses / n
    if avg_loss == 0:
        return 100.0 if avg_gain > 0 else 50.0
    rs = avg_gain / avg_loss
    return 100.0 - (100.0 / (1.0 + rs))


def _mean(xs: Sequence[float]) -> float:
    return sum(xs) / len(xs)


def _std(xs: Sequence[float]) -> float:
    if len(xs) < 2:
        return 0.0
    m = _mean(xs)
    var = sum((x - m) ** 2 for x in xs) / (len(xs) - 1)
    return var ** 0.5


def extreme_probs(bars: Sequence[Bar], cfg: Optional[ScoreConfig] = None) -> Tuple[int, int]:
    """저점 확률, 고점 확률 (0~100). 한 칸에는 더 큰 쪽만 표시한다."""
    cfg = cfg or ScoreConfig()
    if not bars:
        return 50, 50

    closes = [b.close for b in bars]
    highs = [b.high for b in bars]
    lows = [b.low for b in bars]
    close = closes[-1]
    n = min(cfg.lookback, len(bars))
    hh = max(highs[-n:])
    ll = min(lows[-n:])
    span = hh - ll
    loc = 0.5 if span <= 0 else _clip((close - ll) / span, 0.0, 1.0)

    rsi_v = rsi(closes, cfg.rsi_period)
    if rsi_v is None:
        rsi_v = 50.0

    window = closes[-n:]
    mid = _mean(window)
    sd = _std(window)
    if sd <= 0:
        bb_pos = 0.5
    else:
        bb_pos = _clip((close - (mid - 2 * sd)) / (4 * sd), 0.0, 1.0)

    low_p = (
        cfg.w_rsi * (100.0 - rsi_v)
        + cfg.w_loc * (100.0 * (1.0 - loc))
        + cfg.w_bb * (100.0 * (1.0 - bb_pos))
    )
    high_p = (
        cfg.w_rsi * rsi_v
        + cfg.w_loc * (100.0 * loc)
        + cfg.w_bb * (100.0 * bb_pos)
    )

    last = bars[-1]
    prev_close = closes[-2] if len(closes) > 1 else last.open
    bullish = close > last.open and close >= prev_close
    bearish = close < last.open and close <= prev_close
    if loc <= 0.18 and bullish:
        low_p = min(100.0, low_p + 12.0)
    if loc >= 0.82 and bearish:
        high_p = min(100.0, high_p + 12.0)

    return _round_pct(low_p), _round_pct(high_p)


def direction_probs(bars: Sequence[Bar]) -> Tuple[int, int]:
    """상승 확률, 하락 확률. 합은 100."""
    if not bars:
        return 50, 50
    closes = [b.close for b in bars]
    close = closes[-1]
    n5 = min(5, len(closes))
    n20 = min(20, len(closes))
    ma5 = _mean(closes[-n5:])
    ma20 = _mean(closes[-n20:])
    slope = 0.0 if ma20 == 0 else (ma5 - ma20) / ma20

    base = closes[-n5] if n5 else close
    mom = 0.0 if base == 0 else (close - base) / base

    last = bars[-1]
    body = 0.0 if last.open == 0 else (close - last.open) / last.open

    raw = 50.0 + 900.0 * slope + 700.0 * mom + 400.0 * body
    up = _round_pct(raw)
    down = 100 - up
    return up, down


def format_extreme(low_p: int, high_p: int) -> str:
    if low_p >= high_p:
        return f"저점 {low_p}"
    return f"고점 {high_p}"


def format_direction(up_p: int, down_p: int) -> str:
    return f"상승 {up_p} / 하락 {down_p}"


def classify_signal(
    low_p: int,
    high_p: int,
    trade_signal: str = "",
    cfg: Optional[ScoreConfig] = None,
) -> str:
    """매수/매도가 있으면 그대로. 없으면 저점·고점 후보/확정."""
    cfg = cfg or ScoreConfig()
    if trade_signal in TRADE_SIGNALS:
        return trade_signal

    if low_p >= cfg.confirm_min and low_p >= high_p:
        return SIGNAL_LOW_CONF
    if high_p >= cfg.confirm_min and high_p > low_p:
        return SIGNAL_HIGH_CONF
    if low_p >= cfg.candidate_min and low_p >= high_p:
        return SIGNAL_LOW_CAND
    if high_p >= cfg.candidate_min:
        return SIGNAL_HIGH_CAND
    return ""


def infer_trade_signal(low_p: int, high_p: int, up_p: int, down_p: int) -> str:
    """기존 매수/매도 신호가 없을 때, 확정+방향이 맞으면 매수/매도로 승격."""
    if low_p >= CONFIRM_MIN and low_p >= high_p and up_p >= 60:
        return SIGNAL_BUY
    if high_p >= CONFIRM_MIN and high_p > low_p and down_p >= 60:
        return SIGNAL_SELL
    return ""


def score_quote(
    quote: WatchlistQuote,
    bars: Sequence[Bar],
    cfg: Optional[ScoreConfig] = None,
) -> WatchlistRow:
    cfg = cfg or ScoreConfig()
    if not bars:
        return WatchlistRow(
            code=quote.code,
            name=quote.name,
            extreme_text="-",
            extreme_side="",
            extreme_score=0,
            signal="",
            direction_text="-",
            up_prob=0,
            down_prob=0,
            price=quote.price,
            change=quote.change,
            change_pct=quote.change_pct,
            low_prob=0,
            high_prob=0,
        )
    low_p, high_p = extreme_probs(bars, cfg)
    up_p, down_p = direction_probs(bars)
    trade = quote.trade_signal if quote.trade_signal in TRADE_SIGNALS else infer_trade_signal(
        low_p, high_p, up_p, down_p
    )
    signal = classify_signal(low_p, high_p, trade, cfg)
    side = "저점" if low_p >= high_p else "고점"
    score = low_p if side == "저점" else high_p
    return WatchlistRow(
        code=quote.code,
        name=quote.name,
        extreme_text=format_extreme(low_p, high_p),
        extreme_side=side,
        extreme_score=score,
        signal=signal,
        direction_text=format_direction(up_p, down_p),
        up_prob=up_p,
        down_prob=down_p,
        price=quote.price,
        change=quote.change,
        change_pct=quote.change_pct,
        low_prob=low_p,
        high_prob=high_p,
    )


def bars_from_quote(quote: WatchlistQuote, steps: int = 30) -> List[Bar]:
    """현재가·등락률로 최근 경로를 재구성한다. 시세가 없으면 빈 목록."""
    if quote.price is None or quote.price <= 0:
        return []
    pct = quote.change_pct if quote.change_pct is not None else 0.0
    prev = quote.price / (1.0 + pct / 100.0) if pct != -100 else float(quote.price)
    bars: List[Bar] = []
    code_seed = sum(ord(c) for c in quote.code) % 17
    for i in range(steps):
        t = (i + 1) / steps
        # 초반은 전일 종가 근처, 후반은 현재가 쪽으로 붙인다.
        drift = prev + (quote.price - prev) * (t ** 1.15)
        wobble = ((code_seed + i * 3) % 7 - 3) * max(quote.price * 0.004, 1.0)
        close = max(1.0, drift + wobble)
        high = close * (1.0 + 0.006 + (i % 4) * 0.001)
        low = close * (1.0 - 0.006 - ((i + 2) % 4) * 0.001)
        open_ = close * (1.0 - (pct / 100.0) * 0.08 * (1.0 - t))
        if pct >= 0:
            open_ = min(open_, close)
            high = max(high, close, open_)
            low = min(low, close, open_)
        else:
            open_ = max(open_, close)
            high = max(high, close, open_)
            low = min(low, close, open_)
        vol = 1000.0 + (i + code_seed) * 80.0
        bars.append(Bar(open=open_, high=high, low=low, close=close, volume=vol))
    last = bars[-1]
    bars[-1] = Bar(last.open, max(last.high, float(quote.price)), min(last.low, float(quote.price)), float(quote.price), last.volume)
    return bars


def score_quotes(quotes: Iterable[WatchlistQuote], cfg: Optional[ScoreConfig] = None) -> List[WatchlistRow]:
    return [score_quote(q, bars_from_quote(q), cfg) for q in quotes]


def default_watchlist() -> List[WatchlistQuote]:
    """스크린샷 관심종목. 가격은 화면 숫자."""
    return [
        WatchlistQuote("016670", "SOL 시반도"),
        WatchlistQuote("356580", "엘스케이트", 16060, 3700, 29.94),
        WatchlistQuote("443670", "에스피소포트", 4660, 1015, 27.91),
        WatchlistQuote("014380", "우리기술", 14380, -220, -1.51),
        WatchlistQuote("203650", "드림시큐리티", 2555, 430, 20.24),
        WatchlistQuote("038260", "홈아해운", 2254, 47, 2.13),
        WatchlistQuote("069540", "빛과전자", 3912, -13, -0.33),
        WatchlistQuote("082660", "코산자인", 2550, -210, -7.69),
        WatchlistQuote("068760", "누리트", 7680, 980, 14.63),
        WatchlistQuote("002490", "충구석유", 15490, 980, 6.75),
        WatchlistQuote("253450", "스카이랩스", 27375, 1275, 4.88),
        WatchlistQuote("067290", "JW신약", 3580, -40, -1.10),
    ]

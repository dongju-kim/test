"""스캘핑 저점·고점 스펙. G / s_n / 밥그릇은 쓰지 않는다.

국면 엔진·1초 D/H 에 연결하지 않는다. 완성봉만 넣는다.
키움 분봉 시각이 봉 시작이면 end = 시작 + 봉길이.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, time, timedelta
from enum import Enum
from typing import Iterable, List, Optional, Sequence, Tuple


class Side(str, Enum):
    HIGH = "high"
    LOW = "low"


class Bias(str, Enum):
    UP = "up"  # 고고 + 고저
    DOWN = "down"  # 저고 + 저저
    SIDE = "side"  # 섞임. 점을 쫓지 않음


@dataclass(frozen=True)
class Bar:
    """완성봉. end = 그 봉이 끝난 시각."""

    end: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float = 0.0

    def typical(self) -> float:
        """VWAP 용 (고+저+종)/3."""
        return (self.high + self.low + self.close) / 3.0


@dataclass(frozen=True)
class SwingPoint:
    index: int  # 극값 봉
    side: Side
    price: float
    n: int  # 양옆 봉 수. 2=Williams, 1=3봉
    confirm_index: int  # index + n. 이 봉이 끝나야 점을 안다
    rank: int = 1  # 1 단기, 2 중간, 3 장기


@dataclass(frozen=True)
class StructureEvent:
    """한 완성봉에서 스윙 점 대비 무엇이 일어났는지."""

    index: int
    sweep_low: bool
    sweep_high: bool
    choch_down: bool  # 종가가 직전 저점 아래 (상승 구조가 흔들림)
    choch_up: bool
    bos_up: bool  # 종가가 직전 고점 위 (상승 이어짐)
    bos_down: bool


@dataclass
class SwingConfig:
    """숫자 초안. 라이브 타점 숫자와 같은 날 같이 바꾸지 말 것."""

    session_open: time = time(9, 0)
    fractal_n_5m: int = 2
    fractal_n_3m: int = 2
    fractal_n_1m: int = 1  # 3봉
    near_pct: float = 0.002  # 자석 거리 0.2%
    near_atr_frac: float = 0.25
    atr_period: int = 14
    equal_ok: bool = False  # False 면 진짜 더 높/낮아야 함 (동고 탈락)


def _extreme(a: float, b: float, *, greater: bool, equal_ok: bool) -> bool:
    if greater:
        return a >= b if equal_ok else a > b
    return a <= b if equal_ok else a < b


def fractal_indices(
    highs: Sequence[float],
    lows: Sequence[float],
    n: int = 2,
    *,
    equal_ok: bool = False,
) -> Tuple[List[int], List[int]]:
    """Williams. 가운데가 양옆 n개보다 극값. 오른쪽 n봉이 있어야 확정.

    고점 i:
        H[i] > H[i-k]  그리고  H[i] > H[i+k]   (k = 1..n)
    저점 i:
        L[i] < L[i-k]  그리고  L[i] < L[i+k]
    같은 봉이 고점이면서 저점일 수 있다.
    동고(H[i]==이웃)는 equal_ok=False 이면 점이 아니다.
    """
    if n < 1:
        raise ValueError("n 은 1 이상")
    sh: List[int] = []
    sl: List[int] = []
    last = len(highs) - n
    for i in range(n, last):
        hi = highs[i]
        lo = lows[i]
        is_high = all(_extreme(hi, highs[i - k], greater=True, equal_ok=equal_ok) for k in range(1, n + 1)) and all(
            _extreme(hi, highs[i + k], greater=True, equal_ok=equal_ok) for k in range(1, n + 1)
        )
        is_low = all(_extreme(lo, lows[i - k], greater=False, equal_ok=equal_ok) for k in range(1, n + 1)) and all(
            _extreme(lo, lows[i + k], greater=False, equal_ok=equal_ok) for k in range(1, n + 1)
        )
        if is_high:
            sh.append(i)
        if is_low:
            sl.append(i)
    return sh, sl


def swing_points(
    highs: Sequence[float],
    lows: Sequence[float],
    n: int = 2,
    *,
    equal_ok: bool = False,
    rank: int = 1,
) -> List[SwingPoint]:
    sh, sl = fractal_indices(highs, lows, n, equal_ok=equal_ok)
    out: List[SwingPoint] = []
    for i in sh:
        out.append(SwingPoint(i, Side.HIGH, float(highs[i]), n, i + n, rank))
    for i in sl:
        out.append(SwingPoint(i, Side.LOW, float(lows[i]), n, i + n, rank))
    out.sort(key=lambda p: (p.index, 0 if p.side is Side.HIGH else 1))
    return out


def nest_rank(points: Sequence[SwingPoint], *, equal_ok: bool = False) -> List[SwingPoint]:
    """단기 점들끼리 다시 3점 규칙. 가운데가 더 극값이면 rank+1 (ITH/LTH)."""
    extra: List[SwingPoint] = []
    for side in (Side.HIGH, Side.LOW):
        seq = [p for p in points if p.side is side]
        for j in range(1, len(seq) - 1):
            mid, left, right = seq[j], seq[j - 1], seq[j + 1]
            if side is Side.HIGH:
                ok = _extreme(mid.price, left.price, greater=True, equal_ok=equal_ok) and _extreme(
                    mid.price, right.price, greater=True, equal_ok=equal_ok
                )
            else:
                ok = _extreme(mid.price, left.price, greater=False, equal_ok=equal_ok) and _extreme(
                    mid.price, right.price, greater=False, equal_ok=equal_ok
                )
            if ok:
                extra.append(
                    SwingPoint(
                        mid.index,
                        mid.side,
                        mid.price,
                        mid.n,
                        right.confirm_index,  # 오른쪽 단기점이 확정된 뒤에야 중간점
                        rank=mid.rank + 1,
                    )
                )
    extra.sort(key=lambda p: (p.index, p.rank, 0 if p.side is Side.HIGH else 1))
    return extra


def alternate(points: Sequence[SwingPoint]) -> List[SwingPoint]:
    """고점·저점 번갈아. 같은 쪽이 연속이면 더 극값만 남긴다."""
    seq: List[SwingPoint] = []
    for p in sorted(points, key=lambda x: (x.index, 0 if x.side is Side.HIGH else 1)):
        if not seq or seq[-1].side is not p.side:
            seq.append(p)
            continue
        prev = seq[-1]
        if p.side is Side.HIGH and p.price >= prev.price:
            seq[-1] = p
        elif p.side is Side.LOW and p.price <= prev.price:
            seq[-1] = p
    return seq


def label_bias(alt: Sequence[SwingPoint]) -> Bias:
    """직전 고점 둘, 직전 저점 둘로 큰 방향."""
    highs = [p for p in alt if p.side is Side.HIGH]
    lows = [p for p in alt if p.side is Side.LOW]
    if len(highs) < 2 or len(lows) < 2:
        return Bias.SIDE
    hh = highs[-1].price > highs[-2].price
    hl = lows[-1].price > lows[-2].price
    if hh and hl:
        return Bias.UP
    if (not hh) and (not hl):
        return Bias.DOWN
    return Bias.SIDE


def last_of(points: Sequence[SwingPoint], side: Side) -> Optional[SwingPoint]:
    found = [p for p in points if p.side is side]
    return found[-1] if found else None


def structure_event(
    bar: Bar,
    index: int,
    last_high: Optional[SwingPoint],
    last_low: Optional[SwingPoint],
) -> StructureEvent:
    """꼬리 vs 종가. 스윕과 구조 깨짐을 한 봉에서 동시에 참이 되지 않게.

    스윕 저점: L < 직전저  그리고  C >= 직전저
    하락 성격바뀜: C < 직전저
    상승 이어짐: C > 직전고
    """
    sl = last_low.price if last_low is not None else None
    sh = last_high.price if last_high is not None else None
    sweep_low = sl is not None and bar.low < sl and bar.close >= sl
    sweep_high = sh is not None and bar.high > sh and bar.close <= sh
    choch_down = sl is not None and bar.close < sl
    choch_up = sh is not None and bar.close > sh
    # BOS 는 같은 종가 조건이되, 호출 쪽에서 큰 방향과 맞춰 읽는다.
    bos_up = choch_up
    bos_down = choch_down
    return StructureEvent(index, sweep_low, sweep_high, choch_down, choch_up, bos_up, bos_down)


def aggregate(bars: Sequence[Bar], step: int, *, bar_minutes: int = 1, session_open: time = time(9, 0)) -> List[Bar]:
    """1분 완성봉을 step개씩 묶어 상위 봉. 묶음이 덜 찬 진행 중 그룹은 버린다.

    3분[j].O = 1분[3j].O
    3분[j].H = max 1분[3j .. 3j+step).H
    3분[j].L = min ...
    3분[j].C = 1분[3j+step-1].C
    3분[j].V = sum V
    """
    if step < 1:
        raise ValueError("step 은 1 이상")
    groups: dict[int, List[Bar]] = {}
    order: List[int] = []
    for b in bars:
        start = b.end - timedelta(minutes=bar_minutes)
        open_dt = datetime.combine(start.date(), session_open)
        elapsed_min = (start - open_dt).total_seconds() / 60.0
        gid = int(elapsed_min // step)
        if gid not in groups:
            groups[gid] = []
            order.append(gid)
        groups[gid].append(b)
    out: List[Bar] = []
    for gid in order:
        chunk = groups[gid]
        if len(chunk) < step:
            continue
        chunk = chunk[:step]
        out.append(
            Bar(
                end=chunk[-1].end,
                open=chunk[0].open,
                high=max(x.high for x in chunk),
                low=min(x.low for x in chunk),
                close=chunk[-1].close,
                volume=sum(x.volume for x in chunk),
            )
        )
    return out


def true_range(bar: Bar, prev_close: Optional[float]) -> float:
    if prev_close is None:
        return bar.high - bar.low
    return max(bar.high - bar.low, abs(bar.high - prev_close), abs(bar.low - prev_close))


def atr(bars: Sequence[Bar], period: int = 14) -> Optional[float]:
    """Wilder. 봉이 period 개 미만이면 없음."""
    if len(bars) < period:
        return None
    trs: List[float] = []
    prev_c: Optional[float] = None
    for b in bars:
        trs.append(true_range(b, prev_c))
        prev_c = b.close
    # 첫 period 개 단순평균, 이후 Wilder. 여기선 마지막 값만.
    atr_v = sum(trs[:period]) / period
    for tr in trs[period:]:
        atr_v = (atr_v * (period - 1) + tr) / period
    return atr_v


def vwap_and_sigma(bars: Sequence[Bar]) -> Tuple[Optional[float], Optional[float]]:
    """오늘 누적. VWAP = Σ (TP·V) / Σ V
    σ² = Σ (V·TP²) / Σ V  −  VWAP²
    """
    pv = 0.0
    p2v = 0.0
    vol = 0.0
    for b in bars:
        tp = b.typical()
        pv += tp * b.volume
        p2v += (tp * tp) * b.volume
        vol += b.volume
    if vol <= 0:
        return None, None
    vw = pv / vol
    var = p2v / vol - vw * vw
    if var < 0:
        var = 0.0
    return vw, var ** 0.5


def pdh_pdl(yesterday: Sequence[Bar]) -> Tuple[Optional[float], Optional[float]]:
    if not yesterday:
        return None, None
    return max(b.high for b in yesterday), min(b.low for b in yesterday)


def near_level(price: float, level: float, *, atr_v: Optional[float], cfg: SwingConfig) -> bool:
    dist = abs(price - level)
    if dist / level <= cfg.near_pct:
        return True
    if atr_v is not None and dist <= cfg.near_atr_frac * atr_v:
        return True
    return False


def magnets(
    *,
    pdh: Optional[float],
    pdl: Optional[float],
    session_open_px: Optional[float],
    vwap: Optional[float],
    sigma: Optional[float],
    swing_5m_low: Optional[float],
    swing_5m_high: Optional[float],
) -> List[float]:
    xs: List[float] = []
    for v in (pdh, pdl, session_open_px, vwap, swing_5m_low, swing_5m_high):
        if v is not None:
            xs.append(v)
    if vwap is not None and sigma is not None:
        xs.extend((vwap + sigma, vwap - sigma))
    return xs


def near_any(price: float, levels: Iterable[float], *, atr_v: Optional[float], cfg: SwingConfig) -> bool:
    return any(near_level(price, lv, atr_v=atr_v, cfg=cfg) for lv in levels)


def sweep_low_wick(bars: Sequence[Bar], level: float) -> Optional[float]:
    """level 을 꼬리로만 깬 봉의 최저 저가. 종가로 깬 봉은 스윕이 아니다."""
    found: Optional[float] = None
    for b in bars:
        if b.low < level and b.close >= level:
            found = b.low if found is None else min(found, b.low)
    return found


@dataclass(frozen=True)
class BuyTrigger:
    """1분 완성봉에서만 참/거짓. 1초는 여기 없음."""

    ok: bool
    reason: str
    stop: Optional[float]  # 스윕 꼬리 저가


def buy_trigger(
    *,
    bias_5m: Bias,
    last_3m_low: Optional[SwingPoint],
    bar_1m: Bar,
    index_1m: int,
    swing_1m_alt: Sequence[SwingPoint],
    stl_bar_high: Optional[float],
    magnets_px: Sequence[float],
    atr_5m: Optional[float],
    cfg: SwingConfig,
    sweep_wick: Optional[float],
) -> BuyTrigger:
    """매수 방아쇠. 모두 참이어야 한다.

    1. 5분 큰 방향이 상승 (고고+고저)
    2. 직전 3분 저점이 있고, 그 점이 자석 근처
    3. 스윕: 어떤 1분봉이 3분 저점을 꼬리로만 깨고 종가는 위
    4. 그 뒤 1분 3봉 저점 j 가 지금 봉에서 확정 (confirm_index == 지금 인덱스)
    5. 지금 종가 > 저점 봉 j 의 고가 (작은 구조 이어짐)
    6. 지금 종가 >= 3분 저점 (다시 위)
    손절 = 스윕 꼬리 저가
    """
    if bias_5m is not Bias.UP:
        return BuyTrigger(False, "5분이 상승 구조가 아님", None)
    if last_3m_low is None:
        return BuyTrigger(False, "3분 저점 없음", None)
    if not near_any(last_3m_low.price, magnets_px, atr_v=atr_5m, cfg=cfg):
        return BuyTrigger(False, "3분 저점이 자석에서 멈", None)
    if sweep_wick is None or sweep_wick >= last_3m_low.price:
        return BuyTrigger(False, "3분 저점 스윕이 아직 없음", None)
    lows_1m = [p for p in swing_1m_alt if p.side is Side.LOW]
    if not lows_1m:
        return BuyTrigger(False, "1분 3봉 저점 없음", None)
    j = lows_1m[-1]
    if j.confirm_index != index_1m:
        return BuyTrigger(False, "1분 저점이 오늘 봉에서 막 확정된 게 아님", None)
    if stl_bar_high is None or bar_1m.close <= stl_bar_high:
        return BuyTrigger(False, "종가가 1분 저점 봉의 고가를 못 넘김", None)
    if bar_1m.close < last_3m_low.price:
        return BuyTrigger(False, "종가가 아직 3분 저점 아래", None)
    return BuyTrigger(True, "5분 상승 + 3분 스윕 + 1분 저점 확정 종가 위", sweep_wick)


def buy_trigger_from_bars(
    bars_1m: Sequence[Bar],
    *,
    yesterday: Sequence[Bar],
    session_open_px: float,
    cfg: SwingConfig | None = None,
) -> BuyTrigger:
    """완성 1분 시계열 전체로 마지막 봉의 방아쇠를 본다. 그림·테스트용."""
    cfg = cfg or SwingConfig()
    if len(bars_1m) < 6:
        return BuyTrigger(False, "1분봉이 부족", None)
    b5 = aggregate(bars_1m, 5, bar_minutes=1, session_open=cfg.session_open)
    b3 = aggregate(bars_1m, 3, bar_minutes=1, session_open=cfg.session_open)
    if len(b5) < 5 or len(b3) < 5:
        return BuyTrigger(False, "상위 봉이 부족", None)
    p5 = alternate(swing_points([x.high for x in b5], [x.low for x in b5], cfg.fractal_n_5m, equal_ok=cfg.equal_ok))
    p3 = alternate(swing_points([x.high for x in b3], [x.low for x in b3], cfg.fractal_n_3m, equal_ok=cfg.equal_ok))
    p1 = alternate(swing_points([x.high for x in bars_1m], [x.low for x in bars_1m], cfg.fractal_n_1m, equal_ok=cfg.equal_ok))
    bias = label_bias(p5)
    last_3m_low = last_of(p3, Side.LOW)
    pdh, pdl = pdh_pdl(yesterday)
    vw, sg = vwap_and_sigma(bars_1m)
    sh5 = last_of(p5, Side.HIGH)
    sl5 = last_of(p5, Side.LOW)
    mags = magnets(
        pdh=pdh,
        pdl=pdl,
        session_open_px=session_open_px,
        vwap=vw,
        sigma=sg,
        swing_5m_low=sl5.price if sl5 else None,
        swing_5m_high=sh5.price if sh5 else None,
    )
    atr5 = atr(b5, cfg.atr_period)
    wick = sweep_low_wick(bars_1m, last_3m_low.price) if last_3m_low else None
    last = bars_1m[-1]
    stl = last_of(p1, Side.LOW)
    stl_high = float(bars_1m[stl.index].high) if stl is not None else None
    return buy_trigger(
        bias_5m=bias,
        last_3m_low=last_3m_low,
        bar_1m=last,
        index_1m=len(bars_1m) - 1,
        swing_1m_alt=p1,
        stl_bar_high=stl_high,
        magnets_px=mags,
        atr_5m=atr5,
        cfg=cfg,
        sweep_wick=wick,
    )

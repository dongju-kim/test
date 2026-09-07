"""
차트에 그리는 층. 주문 칸(1초)은 바꾸지 않는다.

실제 화면에서 1초 D를 선으로 이으면 톱니가 된다.
빈 초를 0이나 0.5로 잇거나, 오전 전체를 1초로 한 칸에 그리면 더 심하다.

그리는 규칙:
- 점은 체결 있는 1초 D
- 줄은 유효한 초만 최근 N초 평균 (기본 3). 빈 초·1건 초는 줄에 넣지 않음
- 빈 초에서 줄을 끊는다 (0.5로 채우지 않음)
- D/H 기본 창은 최근 90초. 3분봉 하루치를 1초로 겹치지 않음
- 줌아웃 H는 참고용으로만 묶는다. 새 매수 신호가 아니다
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Sequence

from supply_lock import SecondTick


@dataclass
class DisplayConfig:
    d_mean_secs: int = 3
    min_trades_dot: int = 1
    min_trades_line: int = 2
    view_secs: int = 90
    h_overview_bucket: int = 3


@dataclass
class DPoint:
    t: datetime
    d: float
    trades: int
    thin: bool  # 1건. 점만, 줄에는 안 넣음


@dataclass
class DLine:
    t: datetime
    d: Optional[float]  # None 이면 줄 끊김


def raw_d(tick: SecondTick) -> Optional[float]:
    notion = tick.buy_amt + tick.sell_amt
    if tick.trades <= 0 or notion <= 0:
        return None
    return tick.buy_amt / notion


def d_dots(ticks: Sequence[SecondTick], cfg: Optional[DisplayConfig] = None) -> List[DPoint]:
    cfg = cfg or DisplayConfig()
    out: List[DPoint] = []
    for x in ticks:
        d = raw_d(x)
        if d is None or x.trades < cfg.min_trades_dot:
            continue
        out.append(DPoint(t=x.t, d=d, trades=x.trades, thin=x.trades < cfg.min_trades_line))
    return out


def d_smooth_line(ticks: Sequence[SecondTick], cfg: Optional[DisplayConfig] = None) -> List[DLine]:
    """유효한 초만 평균. 빈 초·1건 초에서 줄을 끊는다."""
    cfg = cfg or DisplayConfig()
    n = max(cfg.d_mean_secs, 1)
    out: List[DLine] = []
    buf: List[float] = []
    for x in ticks:
        d = raw_d(x)
        use = d is not None and x.trades >= cfg.min_trades_line
        if not use:
            buf = []
            out.append(DLine(t=x.t, d=None))
            continue
        buf.append(d)  # type: ignore[arg-type]
        if len(buf) > n:
            buf = buf[-n:]
        out.append(DLine(t=x.t, d=sum(buf) / len(buf)))
    return out


def clip_view(ticks: Sequence[SecondTick], now: datetime, cfg: Optional[DisplayConfig] = None) -> List[SecondTick]:
    """D/H 칸의 기본 창. 하루 1초를 한 패널에 넣지 않음."""
    cfg = cfg or DisplayConfig()
    from datetime import timedelta

    cut = now - timedelta(seconds=cfg.view_secs - 1)
    return [x for x in ticks if x.t >= cut]


def downsample_h(values: Sequence[float], bucket: int = 3) -> List[float]:
    """줌아웃 참고용. 신호로 쓰지 않음. 칸의 마지막 H."""
    if bucket <= 1:
        return list(values)
    out: List[float] = []
    for i in range(0, len(values), bucket):
        chunk = values[i : i + bucket]
        if chunk:
            out.append(chunk[-1])
    return out

"""
매수 주문 가격.

추격: 여섯 칸을 통과한 초.
  돌파 = 매도1호가.  눌림 = 직전가.
걸어두기: 방은 열렸는데 체결이 안 늘어난 초.
  이전 3분봉 몸통의 아래서 2/3. 현재가보다 낮을 때만.
시장가는 조건이 부족할 때 쓰지 않는다.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from phase_engine import Bar3m, Phase


# 몸통 아래서 이 비율. 위 2/3 지점.
BODY_FRAC = 2.0 / 3.0


def krx_tick(price: float) -> int:
    """보통주 호가 단위. 가격대만 본다."""
    if price < 2000:
        return 1
    if price < 5000:
        return 5
    if price < 20000:
        return 10
    if price < 50000:
        return 50
    if price < 200000:
        return 100
    if price < 500000:
        return 500
    return 1000


def snap_down(price: float) -> float:
    tick = krx_tick(price)
    if tick <= 0:
        return price
    return float((int(price) // tick) * tick)


def body_two_thirds(bar: Bar3m) -> float:
    """이전 완성봉 몸통의 아래서 2/3."""
    lo = min(bar.open, bar.close)
    hi = max(bar.open, bar.close)
    raw = lo + (hi - lo) * BODY_FRAC
    return snap_down(raw)


def chase_limit(*, phase: Phase, ask1: Optional[float], last: float) -> Optional[float]:
    """추격 지정가. 시장가로 메우지 않음. 미체결이면 포기."""
    if phase == Phase.BREAK_ATTEMPT:
        if ask1 is None or ask1 <= 0:
            return None
        return float(ask1)
    if phase == Phase.PULLBACK:
        if last <= 0:
            return None
        return float(last)
    return None


def wait_limit(*, prev_bar: Bar3m, last: float, stop: Optional[float] = None) -> Optional[float]:
    """
    걸어둘 지정가.
    현재가보다 낮고, 손절가보다 위일 때만. 이미 몸통 아래로 내려왔으면 없음.
    """
    px = body_two_thirds(prev_bar)
    if last <= 0 or px <= 0:
        return None
    if px >= last:
        return None
    if stop is not None and px <= stop:
        return None
    return px


@dataclass
class WaitKeep:
    keep: bool
    why: str


def wait_order_keep(
    *,
    phase_new_buy: bool,
    dump: bool,
    chase_buy_ok: bool,
    h: float,
    dump_flow: bool,
    limit: float,
    last: float,
    stop: Optional[float] = None,
) -> WaitKeep:
    """걸어둔 매수를 유지할지. 추격이 열리면 이 지정가는 접는다."""
    if dump:
        return WaitKeep(False, "급락. 걸어둔 매수 취소")
    if chase_buy_ok:
        return WaitKeep(False, "추격 매수가 열림. 걸어둔 지정가는 취소")
    if not phase_new_buy:
        return WaitKeep(False, "방이 닫힘. 걸어둔 매수 취소")
    if h < 0 and dump_flow:
        return WaitKeep(False, "H가 음수로 깊어짐. 걸어둔 매수 취소")
    if stop is not None and limit <= stop:
        return WaitKeep(False, "지정가가 손절가 아래. 취소")
    if last <= 0:
        return WaitKeep(False, "현재가 없음. 취소")
    return WaitKeep(True, "유지")

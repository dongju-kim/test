"""
1초 D·H와 자물쇠.

D는 대금 비율만 본다. 체결 건수는 타점 선이 아니다.
자물쇠 1층 = 얇지 않음. 확인 2층 = 빈도·대금이 평소보다 늘고 있음.
빈 초의 D는 0.5로 채우지 않는다.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Deque, List, Optional


@dataclass
class LockConfig:
    window_secs: int = 3
    min_trades_in_window: int = 6
    # 창 합산 대금 >= max(절대 하한, 평소 1초 대금 × 창 × 배수)
    min_notional_floor: float = 0.0
    typical_mult: float = 0.5
    typical_ema_secs: int = 90  # 체결 있는 초만
    hd_warmup_secs: int = 40  # 재시작 직후 타점 대기
    typical_short_secs: int = 300  # 이 전엔 평소속도가 짧다고 표시
    fast_ema: int = 4
    slow_ema: int = 18
    signal_ema: int = 6
    d_buy: float = 0.5
    # 매수 확인(2층). 자물쇠(1층)보다 빡빡하다. 매도에 쓰지 않음.
    freq_confirm_mult: float = 2.5  # 창 건수 >= 평소 1초 건수 × 창 × 이 값
    notional_confirm_mult: float = 1.5  # 창 대금 >= 평소 1초 대금 × 창 × 이 값
    freq_already_thick: float = 8.0  # 평소가 이미 초당 이 건 이상이면 가속 대신 유지
    min_confirm_per_sec: float = 6.0  # 가속 확인의 절대 하한 (2~3 → 10 을 염두)


@dataclass
class SecondTick:
    t: datetime
    buy_amt: float
    sell_amt: float
    trades: int


@dataclass
class SupplySnapshot:
    """장중 저장. 3분봉으로는 복원 불가한 1초 수급만 담는다."""

    typical: float
    typical_trades: float
    typical_samples: int
    fast: Optional[float]
    slow: Optional[float]
    signal: Optional[float]
    prev_h: Optional[float]
    ticks: List[SecondTick]


@dataclass
class SecondState:
    t: datetime
    buy_amt: float
    sell_amt: float
    trades: int
    notional: float
    d: Optional[float]  # 체결 없으면 None
    i: float
    h: float
    prev_h: Optional[float]
    typical: float
    lock_ok: bool
    lock_reason: str
    confirm_ok: bool
    confirm_reason: str
    typical_trades: float
    d_streak: int
    h_rising_streak: int


@dataclass
class PointDecision:
    """타점 문. 국면 new_buy_allowed와 AND."""

    buy_ok: bool
    fade_ok: bool  # H가 양수에서 처음 줄어듦
    dump_flow: bool  # H가 음수이며 깊어짐 (보유 중 참고)
    lock_ok: bool
    confirm_ok: bool
    hd_ready: bool
    opening_box_wait: bool
    restart_wait: bool
    d: Optional[float]
    h: float
    reason: str


def _ema_update(prev: Optional[float], x: float, n: int) -> float:
    k = 2.0 / (n + 1.0)
    if prev is None:
        return x
    return k * x + (1.0 - k) * prev


class SupplyEngine:
    def __init__(self, cfg: Optional[LockConfig] = None):
        self.cfg = cfg or LockConfig()
        self.ticks: Deque[SecondTick] = deque(maxlen=4000)
        self.typical: Optional[float] = None
        self.typical_trades: Optional[float] = None
        self.typical_samples: int = 0
        self.fast: Optional[float] = None
        self.slow: Optional[float] = None
        self.signal: Optional[float] = None
        self.prev_h: Optional[float] = None
        self.started_at: Optional[datetime] = None
        self.restored: bool = False  # EMA·직전 초까지 복원됨
        self.typical_only: bool = False  # 평소 속도만 복원. H는 아직 빔
        self.fade_fired: bool = False
        self.last: Optional[SecondState] = None

    def reset(self, now: Optional[datetime] = None, restored: bool = False) -> None:
        self.ticks.clear()
        self.typical = None
        self.typical_trades = None
        self.typical_samples = 0
        self.fast = None
        self.slow = None
        self.signal = None
        self.prev_h = None
        self.started_at = now
        self.restored = restored
        self.typical_only = False
        self.fade_fired = False
        self.last = None

    def restore_typical(self, typical: float, samples: int, now: datetime) -> None:
        """평소 대금/초만. 자물쇠 하한은 바로 쓰지만 H 기억은 다시 쌓는다."""
        self.typical = typical
        self.typical_samples = samples
        self.started_at = now
        self.restored = False
        self.typical_only = True

    def snapshot(self) -> Optional[SupplySnapshot]:
        if self.typical is None:
            return None
        return SupplySnapshot(
            typical=self.typical,
            typical_trades=self.typical_trades or 0.0,
            typical_samples=self.typical_samples,
            fast=self.fast,
            slow=self.slow,
            signal=self.signal,
            prev_h=self.prev_h,
            ticks=list(self.ticks)[-max(self.cfg.window_secs, 30) :],
        )

    def restore_snapshot(self, snap: SupplySnapshot, now: datetime) -> None:
        """같은 날 저장본. 어제 1초와는 잇지 말 것."""
        self.reset(now, restored=True)
        self.typical = snap.typical
        self.typical_trades = snap.typical_trades if snap.typical_trades > 0 else None
        self.typical_samples = snap.typical_samples
        self.fast = snap.fast
        self.slow = snap.slow
        self.signal = snap.signal
        self.prev_h = snap.prev_h
        for t in snap.ticks:
            self.ticks.append(t)
        if snap.ticks:
            last = snap.ticks[-1]
            notion = last.buy_amt + last.sell_amt
            d = (last.buy_amt / notion) if notion > 0 and last.trades > 0 else None
            self.last = SecondState(
                t=last.t,
                buy_amt=last.buy_amt,
                sell_amt=last.sell_amt,
                trades=last.trades,
                notional=notion,
                d=d,
                i=0.0,
                h=snap.prev_h or 0.0,
                prev_h=snap.prev_h,
                typical=snap.typical,
                lock_ok=False,
                lock_reason="복원 직후 산 초를 기다리는 중",
                confirm_ok=False,
                confirm_reason="복원 직후 산 초를 기다리는 중",
                typical_trades=snap.typical_trades,
                d_streak=0,
                h_rising_streak=0,
            )

    def hd_ready(self, now: datetime) -> bool:
        if self.started_at is None or self.last is None:
            return False
        if self.restored and self.fast is not None:
            return True
        return (now - self.started_at).total_seconds() >= self.cfg.hd_warmup_secs

    def typical_is_short(self) -> bool:
        if (self.restored or self.typical_only) and self.typical_samples >= self.cfg.typical_ema_secs:
            return False
        return self.typical_samples < self.cfg.typical_short_secs

    def on_second(self, tick: SecondTick) -> SecondState:
        if self.started_at is None:
            self.started_at = tick.t
        self.ticks.append(tick)
        notional = tick.buy_amt + tick.sell_amt
        d: Optional[float]
        if tick.trades <= 0 or notional <= 0:
            d = None
            i = 0.0
        else:
            d = tick.buy_amt / notional
            if self.typical is None:
                self.typical = notional
            else:
                self.typical = _ema_update(self.typical, notional, self.cfg.typical_ema_secs)
            if self.typical_trades is None:
                self.typical_trades = float(tick.trades)
            else:
                self.typical_trades = _ema_update(
                    self.typical_trades, float(tick.trades), self.cfg.typical_ema_secs
                )
            self.typical_samples += 1
            speed = notional / max(self.typical, 1e-9)
            i = (2.0 * d - 1.0) * speed

        self.fast = _ema_update(self.fast, i, self.cfg.fast_ema)
        self.slow = _ema_update(self.slow, i, self.cfg.slow_ema)
        macd = (self.fast or 0.0) - (self.slow or 0.0)
        self.signal = _ema_update(self.signal, macd, self.cfg.signal_ema)
        h = macd - (self.signal or 0.0)

        lock_ok, lock_reason = self._lock(tick.t)
        confirm_ok, confirm_reason = self._confirm(tick.t)
        d_streak = self._d_streak()
        prev_h = self.prev_h
        if prev_h is None:
            h_rising = 1 if h > 0 else 0
        elif h > 0 and h > prev_h:
            h_rising = (self.last.h_rising_streak if self.last and self.last.h > 0 else 0) + 1
        else:
            h_rising = 0
        if h_rising > 0:
            self.fade_fired = False

        st = SecondState(
            t=tick.t,
            buy_amt=tick.buy_amt,
            sell_amt=tick.sell_amt,
            trades=tick.trades,
            notional=notional,
            d=d,
            i=i,
            h=h,
            prev_h=prev_h,
            typical=self.typical or 0.0,
            lock_ok=lock_ok,
            lock_reason=lock_reason,
            confirm_ok=confirm_ok,
            confirm_reason=confirm_reason,
            typical_trades=self.typical_trades or 0.0,
            d_streak=d_streak,
            h_rising_streak=h_rising,
        )
        self.prev_h = h
        self.last = st
        return st

    def _window(self, now: datetime) -> List[SecondTick]:
        cut = now - timedelta(seconds=self.cfg.window_secs - 1)
        return [x for x in self.ticks if x.t >= cut]

    def _lock(self, now: datetime) -> tuple[bool, str]:
        w = self._window(now)
        if len(w) < self.cfg.window_secs:
            return False, "창이 아직 안 참"
        trades = sum(x.trades for x in w)
        notion = sum(x.buy_amt + x.sell_amt for x in w)
        if any(x.trades <= 0 or (x.buy_amt + x.sell_amt) <= 0 for x in w):
            return False, "빈 초가 있어 D 유지를 인정하지 않음"
        if trades < self.cfg.min_trades_in_window:
            return False, f"체결 {trades}건 < {self.cfg.min_trades_in_window}"
        need = self.cfg.min_notional_floor
        if self.typical:
            need = max(need, self.typical * self.cfg.window_secs * self.cfg.typical_mult)
        if notion < need:
            return False, "창 대금이 평소·하한보다 작음"
        return True, "자물쇠 열림"

    def _window_ending(self, end: datetime) -> List[SecondTick]:
        cut = end - timedelta(seconds=self.cfg.window_secs - 1)
        return [x for x in self.ticks if cut <= x.t <= end]

    def _confirm(self, now: datetime) -> tuple[bool, str]:
        """매수 2층. 빈도가 늘고 대금도 같이 커지는지. 1주 연타는 대금에서 걸러진다."""
        w = self._window(now)
        if len(w) < self.cfg.window_secs:
            return False, "확인 창이 아직 안 참"
        if any(x.trades <= 0 or (x.buy_amt + x.sell_amt) <= 0 for x in w):
            return False, "빈 초가 있어 빈도 가속을 인정하지 않음"
        trades = sum(x.trades for x in w)
        notion = sum(x.buy_amt + x.sell_amt for x in w)
        prev_end = now - timedelta(seconds=self.cfg.window_secs)
        prev = self._window_ending(prev_end)
        prev_ready = len(prev) >= self.cfg.window_secs
        prev_trades = sum(x.trades for x in prev) if prev_ready else 0
        prev_notion = sum(x.buy_amt + x.sell_amt for x in prev) if prev_ready else 0.0

        typ_n = self.typical or 0.0
        typ_t = self.typical_trades or 0.0
        if prev_ready and notion < prev_notion:
            return False, "대금이 직전 창보다 줄었음"

        already = typ_t >= self.cfg.freq_already_thick and trades >= typ_t * self.cfg.window_secs
        if already:
            if typ_n and notion < typ_n * self.cfg.window_secs:
                return False, "이미 두꺼운데 대금이 평소 아래로 줄었음"
            return True, "이미 두꺼운 호가 유지 + 대금 확인"

        need_n = typ_n * self.cfg.window_secs * self.cfg.notional_confirm_mult if typ_n else 0.0
        if need_n and notion < need_n:
            return False, "대금이 평소보다 안 커짐"
        need_t = max(
            self.cfg.min_confirm_per_sec * self.cfg.window_secs,
            typ_t * self.cfg.window_secs * self.cfg.freq_confirm_mult if typ_t else 0.0,
        )
        if trades < need_t:
            return False, f"빈도가 안 늘어남 ({trades}건 < {need_t:.0f})"
        if prev_ready and trades <= prev_trades:
            return False, "빈도가 늘고 있지 않음"
        return True, "빈도·대금이 같이 늘고 있음"

    def _d_streak(self) -> int:
        n = 0
        for x in reversed(self.ticks):
            notion = x.buy_amt + x.sell_amt
            if x.trades <= 0 or notion <= 0:
                break
            d = x.buy_amt / notion
            if d <= self.cfg.d_buy:
                break
            n += 1
        return n

    def point(
        self,
        now: datetime,
        *,
        new_buy_allowed: bool,
        fade_exit_allowed: bool,
        opening_box_wait: bool,
    ) -> PointDecision:
        st = self.last
        ready = self.hd_ready(now)
        restart_wait = not ready
        if st is None:
            return PointDecision(
                buy_ok=False,
                fade_ok=False,
                dump_flow=False,
                lock_ok=False,
                confirm_ok=False,
                hd_ready=ready,
                opening_box_wait=opening_box_wait,
                restart_wait=restart_wait,
                d=None,
                h=0.0,
                reason="1초 수급 없음",
            )
        lock = st.lock_ok
        confirm = st.confirm_ok
        buy = (
            new_buy_allowed
            and not opening_box_wait
            and ready
            and lock
            and confirm
            and st.d_streak >= self.cfg.window_secs
            and st.h > 0
            and st.h_rising_streak >= self.cfg.window_secs - 1
        )
        # 1차: 양수 H가 처음 작아진 한 초만. 같은 축소가 이어져도 다시 안 냄
        first_fade = (
            fade_exit_allowed
            and ready
            and st.h > 0
            and st.prev_h is not None
            and st.prev_h > 0
            and st.h < st.prev_h
            and not self.fade_fired
        )
        if first_fade:
            self.fade_fired = True
        fade = first_fade
        # 수급이 음수이며 직전보다 더 깊음 (국면 급락 전량과는 별개)
        dump_flow = st.h < 0 and (st.prev_h is None or st.h < st.prev_h)
        if opening_box_wait:
            reason = "오프닝 박스(18분) 수집 중. D·H는 쌓지만 신규 안 씀"
        elif restart_wait:
            reason = "재시작 타점 워밍업. 국면은 살아 있고 D·H는 지금부터 쌓는 중"
        elif not new_buy_allowed:
            reason = "국면이 신규 매수를 닫음"
        elif not lock:
            reason = st.lock_reason
        elif not confirm:
            reason = st.confirm_reason
        elif buy:
            reason = "자물쇠 + 빈도·대금 확인 + D 유지 + H 커짐"
        else:
            reason = "자물쇠·확인·D·H 조건 미충족"
        return PointDecision(
            buy_ok=buy,
            fade_ok=fade,
            dump_flow=dump_flow,
            lock_ok=lock,
            confirm_ok=confirm,
            hd_ready=ready,
            opening_box_wait=opening_box_wait,
            restart_wait=restart_wait,
            d=st.d,
            h=st.h,
            reason=reason,
        )

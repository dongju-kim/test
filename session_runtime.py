"""
장중 런타임: 국면 + 자물쇠 + 첫 18분 + 재시작.

지나간 1초 D·H는 키움 3분봉으로 복원할 수 없다.
오늘 3분봉은 재생해서 국면만 즉시 살린다.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

from phase_engine import Bar3m, PhaseConfig, PhaseDecision, PhaseEngine
from supply_lock import LockConfig, PointDecision, SecondTick, SupplyEngine, SupplySnapshot


@dataclass
class RuntimeSnapshot:
    phase: PhaseDecision
    point: PointDecision
    opening_box_wait: bool
    hd_ready: bool
    typical_is_short: bool
    dump_now: bool  # 국면 급락. H 워밍업과 무관, 전량


class SessionRuntime:
    def __init__(
        self,
        phase_cfg: Optional[PhaseConfig] = None,
        lock_cfg: Optional[LockConfig] = None,
    ):
        self.phase = PhaseEngine(phase_cfg or PhaseConfig())
        self.supply = SupplyEngine(lock_cfg or LockConfig())
        self.boot_now: Optional[datetime] = None
        self.midday_restart: bool = False

    def start_open(self, now: datetime, open_price: Optional[float] = None) -> None:
        """09:00부터 정상 기동. D·H도 지금부터 쌓는다."""
        self.phase.reset_session(open_price)
        self.supply.reset(now, restored=False)
        self.boot_now = now
        self.midday_restart = False

    def start_midday(
        self,
        now: datetime,
        today_bars: List[Bar3m],
        open_price: Optional[float] = None,
        persisted_typical: Optional[float] = None,
        persisted_typical_samples: int = 0,
        persisted_supply: Optional[SupplySnapshot] = None,
    ) -> PhaseDecision:
        """
        장중 재시작 (예: 10:25).

        - 오늘 3분봉을 재생해 국면·박스·MA20을 즉시 복구
        - 지나간 1초 D·H는 키움 분봉으로 없음 → 타점은 워밍업 초 동안 닫힘
        - 평소 속도만 있으면 자물쇠 하한은 바로, H는 다시 쌓음
        - 같은 날 1초 스냅샷이 있으면 H 워밍업을 건너뜀
        """
        last = self.phase.replay(today_bars, open_price)
        if persisted_supply is not None:
            self.supply.restore_snapshot(persisted_supply, now)
            self.midday_restart = False
        elif persisted_typical is not None and persisted_typical > 0:
            self.supply.reset(now, restored=False)
            self.supply.restore_typical(persisted_typical, persisted_typical_samples, now)
            self.midday_restart = True
        else:
            self.supply.reset(now, restored=False)
            self.midday_restart = True
        self.boot_now = now
        if last is None:
            last = self.phase.on_clock(now)
        return last

    def opening_box_wait(self) -> bool:
        """완성 3분봉이 6개 미만이면 신규 매수 없음. D·H 계산은 계속."""
        return len(self.phase.bars) < self.phase.cfg.min_box_bars

    def on_bar_close(self, bar: Bar3m) -> PhaseDecision:
        return self.phase.on_bar_close(bar)

    def mark_fill(self, now: datetime) -> None:
        """매수 체결. 1차는 이 시각 이후 규칙을 쓴다."""
        h = self.supply.last.h if self.supply.last else None
        self.supply.mark_entry(now, h)

    def mark_flat(self) -> None:
        self.supply.mark_flat()

    def on_second(self, tick: SecondTick) -> RuntimeSnapshot:
        self.supply.on_second(tick)
        phase = self.phase.last or self.phase.on_clock(tick.t)
        wait = self.opening_box_wait()
        point = self.supply.point(
            tick.t,
            new_buy_allowed=phase.new_buy_allowed,
            fade_exit_allowed=phase.fade_exit_allowed,
            opening_box_wait=wait,
        )
        return RuntimeSnapshot(
            phase=phase,
            point=point,
            opening_box_wait=wait,
            hd_ready=point.hd_ready,
            typical_is_short=self.supply.typical_is_short(),
            dump_now=phase.dump_exit,
        )

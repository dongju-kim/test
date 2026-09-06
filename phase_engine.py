"""
3분봉 국면 엔진.

장중 타점은 H·D가 담당하고, 이 모듈은 완성된 3분봉만으로 방을 고른다.
진행 중 봉·꼬리·전일 3분봉으로 MA20을 시드하지 않는다.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, time, timedelta
from enum import Enum
from typing import List, Optional


class Phase(str, Enum):
    PREOPEN = "preopen"  # 09:00 전 (동시호가 포함)
    OPENING = "opening"  # 완성봉 0개
    WARMUP_WATCH = "warmup_watch"  # 개장 관망 (MA20 전)
    WARMUP_SURGE = "warmup_surge"  # 개장 급등 (MA20 전, 추매 금지)
    WARMUP_DUMP = "warmup_dump"  # 개장 급락 (전량, 신규 금지)
    RANGE = "range"  # 횡보
    BREAK_ATTEMPT = "break_attempt"  # 돌파 시도
    SURGE = "surge"  # 급등
    PULLBACK = "pullback"  # 눌림
    DUMP = "dump"  # 급락
    WATCH = "watch"  # 관망


@dataclass
class PhaseConfig:
    """국면 숫자 초안. 수급(H) 숫자와 같은 날 같이 바꾸지 말 것."""

    bar_minutes: int = 3
    session_open: time = time(9, 0)
    session_close: time = time(15, 30)  # 정규장. 환경에 따라 15:20
    # 키움 분봉 시각이 봉 시작이면 True (09:00 = 09:00~09:03)
    kiwoom_time_is_start: bool = True

    lookback_bars: int = 20  # 60분
    min_box_bars: int = 6  # 18분. 이 전엔 돌파·횡보 잠금 안 함
    min_range_bars: int = 8  # 24분. 이평 없이 폭만으로 임시 횡보

    ma_gap_pct: float = 0.005  # 0.5%
    box_width_pct: float = 0.015  # 1.5%
    pullback_near_pct: float = 0.003  # ±0.3%
    dump_ma_pct: float = 0.005  # 0.5%
    dump_consecutive: int = 2
    impulse_pct: float = 0.01  # +1%
    open_surge_pct: float = 0.01
    open_dump_pct: float = 0.01
    volume_quiet_mult: float = 1.5
    ma20_slope_bars: int = 3  # 지금 MA20 vs N봉 전
    pullback_lookback: int = 20
    pullback_vol_frac: float = 0.5


@dataclass
class Bar3m:
    """완성된 3분봉. end = 봉이 닫힌 시각 (첫 봉은 09:03)."""

    end: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float = 0.0


@dataclass
class PhaseDecision:
    phase: Phase
    bar_end: Optional[datetime]
    n_bars: int
    ma5: Optional[float]
    ma20: Optional[float]
    ma20_ready: bool
    box_high: Optional[float]
    box_low: Optional[float]
    box_locked: bool
    session_open: Optional[float]
    had_impulse: bool
    h_engine_on: bool
    new_buy_allowed: bool  # 돌파 시도·눌림만. 실제 체결은 H가 함
    add_buy_allowed: bool
    fade_exit_allowed: bool  # 급등 방에서 1·2차
    dump_exit: bool  # 전량
    reason: str
    warmup: bool


def ema_last(values: List[float], period: int) -> Optional[float]:
    if not values:
        return None
    if len(values) < period:
        return None
    k = 2.0 / (period + 1.0)
    out = values[0]
    for v in values[1:]:
        out = k * v + (1.0 - k) * out
    return out


def ema_series(values: List[float], period: int) -> List[Optional[float]]:
    k = 2.0 / (period + 1.0)
    out: List[Optional[float]] = []
    acc: Optional[float] = None
    for i, v in enumerate(values):
        if acc is None:
            acc = v
        else:
            acc = k * v + (1.0 - k) * acc
        out.append(acc if i + 1 >= period else None)
    return out


def session_open_dt(day: datetime, cfg: PhaseConfig) -> datetime:
    return datetime.combine(day.date(), cfg.session_open)


def session_close_dt(day: datetime, cfg: PhaseConfig) -> datetime:
    return datetime.combine(day.date(), cfg.session_close)


def bar_end_from_kiwoom(raw: datetime, cfg: PhaseConfig) -> datetime:
    """키움 분봉 시각을 봉 종료 시각으로 맞춘다."""
    if cfg.kiwoom_time_is_start:
        return raw + timedelta(minutes=cfg.bar_minutes)
    return raw


def expected_bar_end(index: int, day: datetime, cfg: PhaseConfig) -> datetime:
    """index=0 → 09:03."""
    return session_open_dt(day, cfg) + timedelta(minutes=cfg.bar_minutes * (index + 1))


def last_bar_end(day: datetime, cfg: PhaseConfig) -> datetime:
    close = session_close_dt(day, cfg)
    open_ = session_open_dt(day, cfg)
    minutes = int((close - open_).total_seconds() // 60)
    full = minutes // cfg.bar_minutes
    return open_ + timedelta(minutes=full * cfg.bar_minutes)


def is_regular_session(now: datetime, cfg: PhaseConfig) -> bool:
    t = now.time()
    return cfg.session_open <= t <= cfg.session_close


def h_flags(phase: Phase) -> tuple[bool, bool, bool, bool, bool]:
    """h_on, new_buy, add_buy, fade_exit, dump_exit"""
    add = False
    if phase in (Phase.PREOPEN, Phase.OPENING, Phase.RANGE, Phase.WATCH, Phase.WARMUP_WATCH):
        return False, False, add, False, False
    if phase in (Phase.DUMP, Phase.WARMUP_DUMP):
        return False, False, add, False, True
    if phase == Phase.BREAK_ATTEMPT:
        return True, True, add, False, False
    if phase == Phase.PULLBACK:
        return True, True, add, False, False
    if phase in (Phase.SURGE, Phase.WARMUP_SURGE):
        return True, False, add, True, False
    return False, False, add, False, False


@dataclass
class PhaseEngine:
    cfg: PhaseConfig = field(default_factory=PhaseConfig)
    bars: List[Bar3m] = field(default_factory=list)
    session_open_price: Optional[float] = None
    box_high: Optional[float] = None
    box_low: Optional[float] = None
    box_locked: bool = False
    phase: Phase = Phase.PREOPEN
    had_impulse: bool = False
    last: Optional[PhaseDecision] = None

    def reset_session(self, open_price: Optional[float] = None) -> None:
        self.bars.clear()
        self.session_open_price = open_price
        self.box_high = None
        self.box_low = None
        self.box_locked = False
        self.phase = Phase.OPENING if open_price is not None else Phase.PREOPEN
        self.had_impulse = False
        self.last = None

    def on_clock(self, now: datetime) -> PhaseDecision:
        """봉이 아직 안 닫힌 동안 호출. 국면은 직전 완성봉 결정을 유지."""
        if now.time() < self.cfg.session_open:
            return self._emit(Phase.PREOPEN, now, "09:00 전. 동시호가 봉은 쓰지 않음")
        if now.time() > self.cfg.session_close:
            if self.last:
                return self.last
            return self._emit(Phase.WATCH, now, "정규장 종료")
        if not self.bars:
            return self._emit(Phase.OPENING, now, "완성 3분봉 0개. 09:03 종가 전까지 국면 없음")
        assert self.last is not None
        return self.last

    def on_bar_close(self, bar: Bar3m) -> PhaseDecision:
        if self.session_open_price is None:
            self.session_open_price = bar.open
        self.bars.append(bar)
        decision = self._classify()
        self.phase = decision.phase
        self.last = decision
        return decision

    def _emit(self, phase: Phase, when: datetime, reason: str) -> PhaseDecision:
        h_on, new_buy, add_buy, fade, dump = h_flags(phase)
        n = len(self.bars)
        warmup = phase in (
            Phase.PREOPEN,
            Phase.OPENING,
            Phase.WARMUP_WATCH,
            Phase.WARMUP_SURGE,
            Phase.WARMUP_DUMP,
        ) or (n < self.cfg.lookback_bars and phase not in (Phase.RANGE, Phase.BREAK_ATTEMPT, Phase.DUMP, Phase.SURGE, Phase.PULLBACK))
        d = PhaseDecision(
            phase=phase,
            bar_end=when,
            n_bars=n,
            ma5=None,
            ma20=None,
            ma20_ready=False,
            box_high=self.box_high,
            box_low=self.box_low,
            box_locked=self.box_locked,
            session_open=self.session_open_price,
            had_impulse=self.had_impulse,
            h_engine_on=h_on,
            new_buy_allowed=new_buy,
            add_buy_allowed=add_buy,
            fade_exit_allowed=fade,
            dump_exit=dump,
            reason=reason,
            warmup=warmup if n == 0 else n < self.cfg.lookback_bars,
        )
        self.phase = phase
        self.last = d
        return d

    def _classify(self) -> PhaseDecision:
        cfg = self.cfg
        bars = self.bars
        n = len(bars)
        last = bars[-1]
        closes = [b.close for b in bars]
        highs = [b.high for b in bars]
        lows = [b.low for b in bars]
        vols = [b.volume for b in bars]
        ma5 = ema_last(closes, 5)
        ma20_series = ema_series(closes, 20)
        ma20 = ma20_series[-1]
        ma20_ready = ma20 is not None
        open_px = self.session_open_price if self.session_open_price is not None else bars[0].open

        if last.close >= open_px * (1.0 + cfg.impulse_pct):
            self.had_impulse = True
        if self.phase in (Phase.BREAK_ATTEMPT, Phase.SURGE, Phase.WARMUP_SURGE):
            self.had_impulse = True

        prior_high, prior_low = self._prior_range()
        width_pct = self._width_pct(prior_high, prior_low)
        vol_quiet = self._volume_quiet(vols)

        # 잠긴 박스가 종가로 깨지면 잠금 해제
        if self.box_locked and self.box_high is not None and self.box_low is not None:
            if last.close > self.box_high or last.close < self.box_low:
                self.box_locked = False

        def pack(phase: Phase, reason: str) -> PhaseDecision:
            if phase == Phase.RANGE and prior_high is not None and prior_low is not None:
                if not self.box_locked:
                    self.box_high = prior_high
                    self.box_low = prior_low
                    self.box_locked = True
            h_on, new_buy, add_buy, fade, dump = h_flags(phase)
            # 눌림 매수는 MA20이 준비된 뒤에만
            if phase == Phase.PULLBACK and not ma20_ready:
                new_buy = False
            return PhaseDecision(
                phase=phase,
                bar_end=last.end,
                n_bars=n,
                ma5=ma5,
                ma20=ma20,
                ma20_ready=ma20_ready,
                box_high=self.box_high,
                box_low=self.box_low,
                box_locked=self.box_locked,
                session_open=open_px,
                had_impulse=self.had_impulse,
                h_engine_on=h_on,
                new_buy_allowed=new_buy,
                add_buy_allowed=add_buy,
                fade_exit_allowed=fade,
                dump_exit=dump,
                reason=reason,
                warmup=not ma20_ready,
            )

        # ---- 1) 급락 ----
        dump, dump_why = self._is_dump(last, closes, ma20, ma20_ready, prior_low, open_px)
        if dump:
            return pack(Phase.DUMP if ma20_ready else Phase.WARMUP_DUMP, dump_why)

        # ---- 2) 돌파 시도 ----
        brk, brk_why = self._is_break(last, prior_high, n)
        if brk:
            self.had_impulse = True
            return pack(Phase.BREAK_ATTEMPT, brk_why)

        # ---- 3) 눌림 (MA20 준비 전엔 꺼둠) ----
        if ma20_ready and ma20 is not None:
            pb, pb_why = self._is_pullback(last, bars, ma20, vols)
            if pb:
                return pack(Phase.PULLBACK, pb_why)

        # ---- 4) 급등 ----
        surge, surge_why = self._is_surge(last, ma5, ma20, ma20_ready, open_px)
        if surge:
            return pack(Phase.SURGE if ma20_ready else Phase.WARMUP_SURGE, surge_why)

        # ---- 5) 횡보 ----
        rng, rng_why = self._is_range(n, ma5, ma20, ma20_ready, width_pct, vol_quiet)
        if rng:
            return pack(Phase.RANGE, rng_why)

        # ---- 6) 관망 ----
        if not ma20_ready:
            return pack(Phase.WARMUP_WATCH, "워밍업 관망. 급락·돌파·급등·횡보 아님")
        return pack(Phase.WATCH, "완성 조건에 맞는 국면 없음")

    def _prior_range(self) -> tuple[Optional[float], Optional[float]]:
        """돌파/폭 계산용. 지금 막 닫힌 봉은 고저에 넣지 않는다."""
        src = self.bars[:-1]
        if not src:
            return None, None
        if self.box_locked and self.box_high is not None and self.box_low is not None:
            return self.box_high, self.box_low
        src = src[-self.cfg.lookback_bars :]
        return max(b.high for b in src), min(b.low for b in src)

    @staticmethod
    def _width_pct(high: Optional[float], low: Optional[float]) -> Optional[float]:
        if high is None or low is None:
            return None
        mid = (high + low) / 2.0
        if mid <= 0:
            return None
        return (high - low) / mid

    def _volume_quiet(self, vols: List[float]) -> bool:
        if len(vols) < 3:
            return True
        last3 = sum(vols[-3:]) / 3.0
        base = vols[-min(len(vols), self.cfg.lookback_bars) :]
        avg = sum(base) / len(base) if base else 0.0
        if avg <= 0:
            return True
        return last3 < avg * self.cfg.volume_quiet_mult

    def _is_dump(
        self,
        last: Bar3m,
        closes: List[float],
        ma20: Optional[float],
        ma20_ready: bool,
        prior_low: Optional[float],
        open_px: float,
    ) -> tuple[bool, str]:
        cfg = self.cfg
        if ma20_ready and ma20 is not None:
            if last.close < ma20 * (1.0 - cfg.dump_ma_pct):
                return True, f"종가 {last.close:.2f} < MA20 {ma20:.2f} −0.5%"
            if len(closes) >= cfg.dump_consecutive and all(
                c < ma20 for c in closes[-cfg.dump_consecutive :]
            ):
                return True, "MA20 아래 2봉 연속 종가"
            return False, ""
        # MA20 전: 시가 대비 또는 임시박스 하단 종가 이탈
        if last.close <= open_px * (1.0 - cfg.open_dump_pct):
            return True, f"개장 급락. 종가 ≤ 시가 −{cfg.open_dump_pct*100:.1f}%"
        if (
            prior_low is not None
            and len(self.bars) >= cfg.min_box_bars
            and last.close < prior_low
        ):
            return True, f"개장 급락. 종가 < 임시박스 하단 {prior_low:.2f}"
        return False, ""

    def _is_break(self, last: Bar3m, prior_high: Optional[float], n: int) -> tuple[bool, str]:
        if prior_high is None:
            return False, ""
        if self.box_locked and self.box_high is not None:
            if last.close > self.box_high:
                return True, f"잠금 박스 상단 {self.box_high:.2f}을 종가가 위로 닫음"
            return False, ""
        if n < self.cfg.min_box_bars:
            return False, ""
        if last.close > prior_high:
            return True, f"임시박스 상단 {prior_high:.2f}을 종가가 위로 닫음"
        return False, ""

    def _is_pullback(
        self,
        last: Bar3m,
        bars: List[Bar3m],
        ma20: float,
        vols: List[float],
    ) -> tuple[bool, str]:
        if not self.had_impulse:
            return False, ""
        dist = (last.close - ma20) / ma20
        near = abs(dist) <= self.cfg.pullback_near_pct
        # 약한 이탈: 이번 1봉만 0.3% 이내 아래
        weak_ok = last.close < ma20 and dist >= -self.cfg.pullback_near_pct
        if not (near or weak_ok):
            return False, ""
        # 조정 거래량 < 상승 최고 거래량 50% (봉이 충분할 때만)
        look = bars[-self.cfg.pullback_lookback :]
        if len(look) >= 6 and any(v > 0 for v in vols):
            peak_up_vol = 0.0
            rising = False
            for i in range(1, len(look)):
                if look[i].close > look[i - 1].close:
                    rising = True
                    peak_up_vol = max(peak_up_vol, look[i].volume)
                elif rising:
                    pass
            if peak_up_vol > 0 and last.volume > peak_up_vol * self.cfg.pullback_vol_frac:
                return False, ""
        if weak_ok and not near:
            return True, f"약한 이탈. 종가 MA20 아래 {abs(dist)*100:.2f}% (0.3% 이내)"
        return True, f"종가 MA20 ±0.3% (이격 {dist*100:.2f}%)"

    def _is_surge(
        self,
        last: Bar3m,
        ma5: Optional[float],
        ma20: Optional[float],
        ma20_ready: bool,
        open_px: float,
    ) -> tuple[bool, str]:
        cfg = self.cfg
        if ma20_ready and ma20 is not None:
            if last.close <= ma20:
                return False, ""
            if abs(last.close - ma20) / ma20 <= cfg.pullback_near_pct:
                return False, ""  # 눌림 자리. 우선순위에서 이미 걸렸으면 여기 안 옴
            ma20_prev = ema_series([b.close for b in self.bars], 20)
            idx = -1 - cfg.ma20_slope_bars
            if len(ma20_prev) > cfg.ma20_slope_bars and ma20_prev[idx] is not None:
                if ma20 <= ma20_prev[idx]:  # type: ignore[operator]
                    return False, ""
            if not self.had_impulse:
                return False, ""
            return True, "MA20 위 우상향. 상단 첫 닫힘이 아님. MA20에서 떨어짐"
        # MA20 전
        if last.close < open_px * (1.0 + cfg.open_surge_pct):
            return False, ""
        if ma5 is not None and last.close < ma5:
            return False, ""
        return True, f"개장 급등. 종가 ≥ 시가 +{cfg.open_surge_pct*100:.1f}%"

    def _is_range(
        self,
        n: int,
        ma5: Optional[float],
        ma20: Optional[float],
        ma20_ready: bool,
        width_pct: Optional[float],
        vol_quiet: bool,
    ) -> tuple[bool, str]:
        cfg = self.cfg
        if width_pct is None or width_pct >= cfg.box_width_pct:
            return False, ""
        if not vol_quiet:
            return False, ""
        if ma20_ready and ma5 is not None and ma20 is not None:
            gap = abs(ma5 - ma20) / ma20
            if gap >= cfg.ma_gap_pct:
                return False, ""
            return True, f"이평 간격 {gap*100:.2f}% · 폭 {width_pct*100:.2f}% · 거래량 조용 → 박스 잠금"
        if n < cfg.min_range_bars:
            return False, ""
        if ma5 is not None and n >= 8:
            prev = ema_last([b.close for b in self.bars[:-3]], 5)
            if prev is not None and abs(ma5 - prev) / ma5 > 0.004:
                return False, ""
        return True, f"임시 횡보. 폭 {width_pct*100:.2f}% · MA20 전 · 박스 잠금"


def build_engine(session_open_price: Optional[float] = None) -> PhaseEngine:
    eng = PhaseEngine()
    if session_open_price is not None:
        eng.reset_session(session_open_price)
    return eng

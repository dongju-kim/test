"""
여러 종목이 같은 초에 매수 문을 열었을 때 줄 세우기.

신뢰점수(승률 예측)가 아니다. 이미 여섯 칸을 통과한 종목만
그 종목 평소 대비 테이프가 얼마나 두꺼운지로 비교한다.
원 H·원 대금·가격은 종목끼리 비교하지 않는다.
매도에는 쓰지 않는다.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Optional, Sequence


@dataclass
class RankConfig:
    max_new: int = 1
    # 점수 축. 합이 1일 필요 없음. 상대 비교만.
    w_count: float = 0.40
    w_money: float = 0.35
    w_d: float = 0.15
    w_h_streak: float = 0.10
    # 1.0이 되는 지점 (확인 2층 문턱과 맞춤)
    count_ref: float = 2.5
    money_ref: float = 1.5
    d_ref: float = 0.25  # D=0.75 → 1.0
    h_streak_ref: float = 3.0
    clip_hi: float = 2.0


@dataclass
class RankInput:
    code: str
    buy_ok: bool
    already_held: bool = False
    d: Optional[float] = None
    d_streak: int = 0
    h_rising_streak: int = 0
    typical: float = 0.0
    typical_trades: float = 0.0
    window_notional: float = 0.0
    window_trades: float = 0.0
    window_secs: int = 3
    # 참고용. 점수에 넣지 않음
    h: float = 0.0
    phase: str = ""


@dataclass
class Ranked:
    code: str
    score: float
    count_speed: float
    money_speed: float
    d: float
    h_rising_streak: int
    reason: str
    skip: bool
    skip_why: str = ""


def _clip(x: float, lo: float, hi: float) -> float:
    return lo if x < lo else hi if x > hi else x


def speeds(inp: RankInput) -> tuple[float, float]:
    sec = max(inp.window_secs, 1)
    money = inp.window_notional / max(inp.typical * sec, 1e-9) if inp.typical > 0 else 0.0
    count = inp.window_trades / max(inp.typical_trades * sec, 1e-9) if inp.typical_trades > 0 else 0.0
    return count, money


def score_one(inp: RankInput, cfg: Optional[RankConfig] = None) -> Ranked:
    cfg = cfg or RankConfig()
    if not inp.buy_ok:
        return Ranked(inp.code, 0.0, 0.0, 0.0, inp.d or 0.0, inp.h_rising_streak, "", True, "여섯 칸 미통과")
    if inp.already_held:
        return Ranked(inp.code, 0.0, 0.0, 0.0, inp.d or 0.0, inp.h_rising_streak, "", True, "이미 보유. 추매 없음")
    cs, ms = speeds(inp)
    d = inp.d if inp.d is not None else 0.5
    c_ax = _clip(cs / cfg.count_ref, 0.0, cfg.clip_hi)
    m_ax = _clip(ms / cfg.money_ref, 0.0, cfg.clip_hi)
    d_ax = _clip((d - 0.5) / cfg.d_ref, 0.0, cfg.clip_hi)
    h_ax = _clip(inp.h_rising_streak / cfg.h_streak_ref, 0.0, 1.0)
    s = cfg.w_count * c_ax + cfg.w_money * m_ax + cfg.w_d * d_ax + cfg.w_h_streak * h_ax
    reason = f"건수×{cs:.1f} 대금×{ms:.1f} D {d:.2f} H연속 {inp.h_rising_streak}"
    return Ranked(inp.code, s, cs, ms, d, inp.h_rising_streak, reason, False)


def pick(
    inputs: Iterable[RankInput],
    *,
    slots_left: int,
    cfg: Optional[RankConfig] = None,
) -> List[Ranked]:
    """같은 초의 매수 후보만. 다음 초에 남은 신호는 다시 평가한다."""
    cfg = cfg or RankConfig()
    ranked = [score_one(x, cfg) for x in inputs]
    live = [x for x in ranked if not x.skip]
    live.sort(key=lambda x: (-x.score, -x.count_speed, -x.money_speed, -x.d))
    take = max(0, min(cfg.max_new, slots_left))
    return live[:take]


def explain_order(ranked: Sequence[Ranked]) -> List[str]:
    return [f"{i+1}. {r.code}  {r.score:.3f}  {r.reason}" for i, r in enumerate(ranked)]

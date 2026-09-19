"""스캘핑용 다층(5분·3분·1분) 저점·고점 — 전문가 방식 그림.

기존 G / s_n / 밥그릇은 그리지 않는다. 배치.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.font_manager import FontProperties
from matplotlib.patches import FancyBboxPatch, Rectangle

FP = FontProperties(fname="/usr/share/fonts/truetype/nanum/NanumGothic.ttf")
FPB = FontProperties(fname="/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf")
plt.rcParams["axes.unicode_minus"] = False

OUT = Path("/workspace/docs")
ART = Path("/opt/cursor/artifacts")
ART.mkdir(parents=True, exist_ok=True)
BG = "#f7f4ee"
UP = "#c62828"
DN = "#1565c0"


def k(s: str) -> str:
    return s.replace(" ", "\u3000").replace("−", "-").replace("–", "-").replace("—", "-")


def txt(ax, x, y, s, *, bold=False, **kw):
    kw.pop("fontweight", None)
    ax.text(x, y, k(s), fontproperties=FPB if bold else FP, **kw)


def ohlc_from_close(close: np.ndarray, seed: int = 7) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    rng = np.random.default_rng(seed)
    n = close.size
    open_ = np.empty(n)
    open_[0] = close[0] - 0.12
    open_[1:] = close[:-1]
    high = np.maximum(open_, close) + rng.uniform(0.07, 0.18, n)
    low = np.minimum(open_, close) - rng.uniform(0.07, 0.18, n)
    # 이야기용 강제: 5분 고점 꼬리, 3분 저점 스윕 꼬리
    high[37] = max(high[37], 105.72)
    low[47] = min(low[47], 100.35)
    return open_, high, low, close


def agg(open_, high, low, close, step: int):
    n = (len(close) // step) * step
    o = open_[:n].reshape(-1, step)[:, 0]
    h = high[:n].reshape(-1, step).max(axis=1)
    l = low[:n].reshape(-1, step).min(axis=1)
    c = close[:n].reshape(-1, step)[:, -1]
    return o, h, l, c


def fractals(high: np.ndarray, low: np.ndarray, n: int = 2) -> tuple[list[int], list[int]]:
    """Williams: 가운데 봉이 양옆 n개보다 진짜 높/낮. 오른쪽 n봉이 끝나야 확정."""
    sh: list[int] = []
    sl: list[int] = []
    for i in range(n, len(high) - n):
        if all(high[i] > high[i - k] for k in range(1, n + 1)) and all(high[i] > high[i + k] for k in range(1, n + 1)):
            sh.append(i)
        if all(low[i] < low[i - k] for k in range(1, n + 1)) and all(low[i] < low[i + k] for k in range(1, n + 1)):
            sl.append(i)
    return sh, sl


def draw_candles(ax, xs, o, h, l, c, width: float) -> None:
    for i, x in enumerate(xs):
        color = UP if c[i] >= o[i] else DN
        ax.plot([x, x], [l[i], h[i]], color=color, lw=1.05, solid_capstyle="round", zorder=2)
        body_lo = min(o[i], c[i])
        body_hi = max(o[i], c[i])
        ax.add_patch(
            Rectangle(
                (x - width / 2, body_lo),
                width,
                max(body_hi - body_lo, 0.04),
                facecolor=color,
                edgecolor=color,
                lw=0.3,
                zorder=3,
            )
        )


def mark_swings(ax, xs, high, low, sh, sl) -> None:
    for i in sh:
        ax.scatter([xs[i]], [high[i] + 0.16], marker="v", s=42, color=UP, zorder=5)
    for i in sl:
        ax.scatter([xs[i]], [low[i] - 0.16], marker="^", s=42, color=DN, zorder=5)


def make_path() -> np.ndarray:
    # 60개의 1분 종가. 이야기: 오름 → 얕은 눌림 → 천장 → 스윕 후 반등
    return np.array(
        [
            100.00, 100.18, 100.46, 100.38, 100.72, 100.95, 101.22, 101.10, 101.48, 101.70,
            101.92, 102.10, 102.02, 102.38, 102.55,
            102.28, 102.02, 101.74, 101.50, 101.22, 101.05, 101.32, 101.55, 101.78, 102.00,
            102.28, 102.58, 102.88, 103.10, 103.38, 103.62, 103.92, 104.22, 104.08, 104.48,
            104.78, 105.08, 105.00, 105.38, 105.18,
            104.72, 104.18, 103.62, 103.05, 102.48, 101.88, 101.28, 100.68, 101.05, 101.48,
            101.88, 102.22, 102.52, 102.38, 102.82, 103.12, 103.42, 103.28, 103.72, 103.95,
        ],
        dtype=float,
    )


def panel_style(ax) -> None:
    ax.set_facecolor("#fffdf8")
    ax.set_yticks([])
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.spines["left"].set_color("#c5b9a8")
    ax.spines["bottom"].set_color("#c5b9a8")


def render() -> Path:
    close = make_path()
    o1, h1, l1, c1 = ohlc_from_close(close)
    o3, h3, l3, c3 = agg(o1, h1, l1, c1, 3)
    o5, h5, l5, c5 = agg(o1, h1, l1, c1, 5)
    x1 = np.arange(len(c1)) + 0.5
    x3 = np.arange(len(c3)) * 3 + 1.5
    x5 = np.arange(len(c5)) * 5 + 2.5
    sh5, sl5 = fractals(h5, l5, n=2)
    sh3, sl3 = fractals(h3, l3, n=2)
    sh1, sl1 = fractals(h1, l1, n=1)  # 3봉 스윙

    pdh, pdl, vwap = 105.85, 99.70, 102.70

    fig = plt.figure(figsize=(13.6, 11.0), dpi=140)
    fig.patch.set_facecolor(BG)
    gs = fig.add_gridspec(
        4,
        3,
        height_ratios=[1.12, 1.12, 1.38, 1.12],
        hspace=0.42,
        wspace=0.22,
        left=0.055,
        right=0.985,
        top=0.91,
        bottom=0.035,
    )
    ax5 = fig.add_subplot(gs[0, :])
    ax3 = fig.add_subplot(gs[1, :])
    ax1 = fig.add_subplot(gs[2, :])
    axf = fig.add_subplot(gs[3, 0])
    axc = fig.add_subplot(gs[3, 1])
    axb = fig.add_subplot(gs[3, 2])

    # --- 5분: 큰 구조 + 글로벌 선 ---
    panel_style(ax5)
    ax5.axhline(pdh, color="#6a1b9a", lw=1.15, ls="--")
    ax5.axhline(vwap, color="#ef6c00", lw=1.15, ls=":")
    ax5.axhline(pdl, color="#6a1b9a", lw=1.0, ls="--", alpha=0.55)
    draw_candles(ax5, x5, o5, h5, l5, c5, width=3.6)
    mark_swings(ax5, x5, h5, l5, sh5, sl5)
    txt(ax5, 48.5, pdh + 0.22, "전일고점 PDH", ha="center", fontsize=8, color="#6a1b9a")
    txt(ax5, 0.8, vwap + 0.22, "VWAP", fontsize=8, color="#ef6c00")
    if sh5:
        i = max(sh5, key=lambda j: h5[j])
        txt(ax5, x5[i], h5[i] + 0.55, "5분 고점 (확정은 2봉 뒤)", ha="center", fontsize=8, color=UP)
    txt(ax5, 0.01, 1.08, "5분봉 - 큰 방. Williams 프랙탈(양옆 2봉). 여기가 오늘 천장·바닥 후보.", transform=ax5.transAxes, fontsize=11, bold=True)
    ax5.set_xlim(-0.5, 60.5)
    ax5.set_xticks([])
    ax5.set_ylim(99.15, 106.85)

    # --- 3분: 중간 스윙 ---
    panel_style(ax3)
    ax3.axhline(vwap, color="#ef6c00", lw=0.9, ls=":", alpha=0.7)
    draw_candles(ax3, x3, o3, h3, l3, c3, width=2.2)
    mark_swings(ax3, x3, h3, l3, sh3, sl3)
    if sl3:
        i = sl3[0]
        ax3.annotate(
            k("3분 저점 (나중에 스윕 당함)"),
            xy=(x3[i], l3[i] - 0.12),
            xytext=(x3[i] + 9.0, l3[i] - 1.05),
            fontsize=8,
            color=DN,
            fontproperties=FP,
            arrowprops=dict(arrowstyle="->", color=DN, lw=1.0),
        )
    if sh3:
        i = max(sh3, key=lambda j: h3[j])
        txt(ax3, x3[i] - 4.2, h3[i] + 0.42, "3분 고점", ha="center", fontsize=8, color=UP)
    txt(ax3, 0.01, 1.08, "3분봉 - 5분 방 안의 중간 스윙. 눌림이 진짜인지 여기서 본다.", transform=ax3.transAxes, fontsize=11, bold=True)
    ax3.set_xlim(-0.5, 60.5)
    ax3.set_xticks([])
    ax3.set_ylim(99.2, 106.55)

    # --- 1분: 방아쇠. 스윕 + 3봉 저점 ---
    panel_style(ax1)
    draw_candles(ax1, x1, o1, h1, l1, c1, width=0.72)
    # 3분 첫 저점 가로선 = 스윕 기준
    if sl3:
        ax1.axhline(l3[sl3[0]], color=DN, lw=0.9, ls="--", alpha=0.55)
        txt(ax1, 1.2, l3[sl3[0]] + 0.18, "3분 저점 선", fontsize=8, color=DN)
    # 스윕 봉
    ax1.scatter([x1[47]], [l1[47] - 0.18], marker="^", s=40, color="#2e7d32", zorder=6)
    txt(ax1, x1[47] - 6.8, l1[47] - 0.55, "꼬리로 깨기 = 스윕", ha="center", fontsize=8, color="#2e7d32")
    # 1분 3봉 저점 중 스윕 근처
    near = [i for i in sl1 if 44 <= i <= 52]
    if near:
        i = near[0]
        ax1.scatter([x1[i]], [l1[i] - 0.08], marker="^", s=36, color=DN, zorder=6)
        txt(ax1, min(x1[i] + 5.2, 52.5), l1[i] + 0.62, "1분 3봉 저점. 종가가 위 = 방아쇠", fontsize=8, color=DN)
    txt(ax1, 0.01, 1.06, "1분봉 - 스캘핑 방아쇠. 큰 저점을 꼬리로 찍은 뒤, 종가가 다시 위로 붙으면 산다.", transform=ax1.transAxes, fontsize=11, bold=True)
    ax1.set_xlim(-0.5, 60.5)
    ax1.set_xticks([])
    ax1.set_ylim(99.55, 106.35)
    for xv, lab in ((0.0, "0분"), (0.25, "15"), (0.5, "30"), (0.75, "45"), (1.0, "60분")):
        txt(ax1, xv, -0.09, lab, ha="center", fontsize=8, color="#555", transform=ax1.transAxes)

    # --- 레시피 1: 5봉 프랙탈 ---
    axf.set_facecolor("#fffdf8")
    axf.set_xlim(0, 6)
    axf.set_ylim(0, 4.2)
    axf.axis("off")
    axf.add_patch(FancyBboxPatch((0.12, 0.12), 5.76, 3.96, boxstyle="round,pad=0.04,rounding_size=0.12", facecolor="#e3f2fd", edgecolor=DN, lw=1.2))
    txt(axf, 3.0, 3.72, "Williams 프랙탈 (5봉)", ha="center", fontsize=11, bold=True, color=DN)
    # 미니 5봉: 가운데가 고점
    mini_h = [1.55, 1.85, 2.55, 1.90, 1.50]
    mini_l = [1.05, 1.20, 1.70, 1.25, 1.00]
    mini_o = [1.20, 1.40, 1.90, 2.20, 1.35]
    mini_c = [1.40, 1.70, 2.35, 1.45, 1.20]
    for i in range(5):
        x = 0.85 + i * 0.95
        color = UP if mini_c[i] >= mini_o[i] else DN
        axf.plot([x, x], [mini_l[i], mini_h[i]], color=color, lw=1.4)
        axf.add_patch(Rectangle((x - 0.18, min(mini_o[i], mini_c[i])), 0.36, abs(mini_c[i] - mini_o[i]) + 0.02, facecolor=color, edgecolor=color))
        txt(axf, x, 0.78, str(i - 2), ha="center", fontsize=8)
    axf.scatter([0.85 + 2 * 0.95], [2.72], marker="v", s=50, color=UP, zorder=5)
    txt(axf, 3.0, 0.38, "가운데 고가 > 왼2·오른2. 확정은 2봉 뒤.", ha="center", fontsize=9)

    # --- 레시피 2: 3봉 스윙 ---
    axc.set_facecolor("#fffdf8")
    axc.set_xlim(0, 6)
    axc.set_ylim(0, 4.2)
    axc.axis("off")
    axc.add_patch(FancyBboxPatch((0.12, 0.12), 5.76, 3.96, boxstyle="round,pad=0.04,rounding_size=0.12", facecolor="#fff3e0", edgecolor="#e65100", lw=1.2))
    txt(axc, 3.0, 3.72, "ICT 3봉 스윙", ha="center", fontsize=11, bold=True, color="#e65100")
    mini_h = [1.70, 1.35, 1.65]
    mini_l = [1.15, 0.72, 1.10]
    mini_o = [1.45, 1.20, 0.95]
    mini_c = [1.30, 0.90, 1.40]
    for i in range(3):
        x = 1.4 + i * 1.15
        color = UP if mini_c[i] >= mini_o[i] else DN
        axc.plot([x, x], [mini_l[i], mini_h[i]], color=color, lw=1.4)
        axc.add_patch(Rectangle((x - 0.2, min(mini_o[i], mini_c[i])), 0.4, abs(mini_c[i] - mini_o[i]) + 0.02, facecolor=color, edgecolor=color))
        txt(axc, x, 2.55, str(i + 1), ha="center", fontsize=9)
    axc.scatter([1.4 + 1.15], [0.58], marker="^", s=50, color=DN, zorder=5)
    txt(axc, 3.0, 0.38, "가운데 저가 < 왼1·오른1. 확정은 1봉 뒤.", ha="center", fontsize=9)

    # --- 레시피 3: 꼬리 vs 종가 ---
    axb.set_facecolor("#fffdf8")
    axb.set_xlim(0, 6)
    axb.set_ylim(0, 4.2)
    axb.axis("off")
    axb.add_patch(FancyBboxPatch((0.12, 0.12), 5.76, 3.96, boxstyle="round,pad=0.04,rounding_size=0.12", facecolor="#ffebee", edgecolor=UP, lw=1.2))
    txt(axb, 3.0, 3.72, "꼬리 스윕 ≠ 구조 깨짐", ha="center", fontsize=11, bold=True, color=UP)
    txt(
        axb,
        3.0,
        2.05,
        "꼬리만 저점 아래 = 스윕(유동성)\n"
        "종가가 저점 아래 = 구조 깨짐(CHoCH)\n"
        "스캘핑은 스윕 후 종가가 다시 위.\n"
        "지그재그 마지막 다리는 쓰지 않음.",
        ha="center",
        va="center",
        fontsize=9,
    )

    txt(
        fig.add_axes([0, 0.945, 1, 0.055], frameon=False),
        0.5,
        0.42,
        "저점·고점은 한 시계가 아니라 겹쳐서 본다. 5분 구조 · 3분 중간 · 1분 방아쇠 · 전일고저·VWAP.",
        ha="center",
        fontsize=14,
        bold=True,
    )
    fig.axes[-1].set_xlim(0, 1)
    fig.axes[-1].set_ylim(0, 1)
    fig.axes[-1].axis("off")

    path = OUT / "mtf_swing_hl.png"
    fig.savefig(path, bbox_inches="tight", facecolor=fig.get_facecolor())
    fig.savefig(ART / "mtf_swing_hl.png", bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)
    return path


if __name__ == "__main__":
    print(render())

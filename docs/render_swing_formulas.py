"""저점·고점 구현 식 그림 3장. 한글은 Nanum + 전각 공백."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
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


def box(ax, x, y, w, h, fc, ec):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.08", facecolor=fc, edgecolor=ec, lw=1.15))


def candle(ax, x, o, h, l, c, w=0.55):
    color = UP if c >= o else DN
    ax.plot([x, x], [l, h], color=color, lw=1.6, solid_capstyle="round", zorder=2)
    lo, hi = min(o, c), max(o, c)
    ax.add_patch(Rectangle((x - w / 2, lo), w, max(hi - lo, 0.08), facecolor=color, edgecolor=color, zorder=3))
    return color


def save(fig, name: str) -> Path:
    path = OUT / name
    fig.savefig(path, bbox_inches="tight", facecolor=fig.get_facecolor())
    fig.savefig(ART / name, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)
    return path


def render_fractal() -> Path:
    fig = plt.figure(figsize=(13.6, 10.6), dpi=140)
    fig.patch.set_facecolor(BG)
    gs = fig.add_gridspec(3, 2, height_ratios=[1.25, 1.05, 1.15], hspace=0.38, wspace=0.18, left=0.04, right=0.98, top=0.91, bottom=0.04)
    ax1 = fig.add_subplot(gs[0, :])
    ax2 = fig.add_subplot(gs[1, 0])
    ax3 = fig.add_subplot(gs[1, 1])
    ax4 = fig.add_subplot(gs[2, 0])
    ax5 = fig.add_subplot(gs[2, 1])

    # --- 고점 숫자 예 ---
    ax1.set_xlim(0, 14)
    ax1.set_ylim(0, 8.2)
    ax1.axis("off")
    ax1.set_facecolor(BG)
    txt(ax1, 0.1, 7.7, "1. Williams 고점. n=2. 가운데 봉 i 의 고가가 양옆 2개보다 진짜 높아야 한다.", fontsize=12, bold=True)
    data = [
        (1.9, 98.8, 100.0, 97.6, 99.2, "i-2", "100"),
        (3.3, 99.4, 102.0, 98.6, 101.4, "i-1", "102"),
        (4.7, 101.6, 108.0, 100.8, 106.4, "i", "108"),
        (6.1, 102.4, 103.0, 100.2, 101.6, "i+1", "103"),
        (7.5, 100.2, 101.0, 98.6, 99.4, "i+2", "101"),
    ]
    ax1.plot([1.3, 8.3], [3.6, 3.6], color="#c5b9a8", lw=0.8)

    def yv(p):
        return 1.55 + (p - 97) * 0.38

    for x, o, h, l, c, lab, hv in data:
        hh, ll = max(o, h, c), min(o, l, c)
        candle(ax1, x, yv(o), yv(hh), yv(ll), yv(c), w=0.7)
        txt(ax1, x, 0.72, lab, ha="center", fontsize=10, bold=True)
        txt(ax1, x, yv(hh) + 0.22, "H=" + hv, ha="center", fontsize=9, color=UP)
    ax1.scatter([4.7], [yv(108) + 0.55], marker="v", s=70, color=UP, zorder=6)
    txt(ax1, 4.7, 6.95, "고점 후보", ha="center", fontsize=9, color=UP)
    box(ax1, 8.85, 0.85, 4.95, 6.35, "#e3f2fd", DN)
    txt(ax1, 9.1, 6.55, "고점(i) 식", fontsize=12, bold=True, color=DN)
    lines = [
        "H[i] > H[i-2]",
        "H[i] > H[i-1]",
        "H[i] > H[i+1]",
        "H[i] > H[i+2]",
        "",
        "108>100 , 108>102",
        "108>103 , 108>101",
        "네 개 모두 참이면 고점",
        "같으면(=) 탈락",
    ]
    for j, line in enumerate(lines):
        txt(ax1, 9.1, 5.85 - j * 0.52, line, fontsize=10)

    # --- 저점 ---
    ax2.set_xlim(0, 8)
    ax2.set_ylim(0, 7)
    ax2.axis("off")
    txt(ax2, 0.1, 6.55, "2. 저점 식. L[i] 가 양옆 2개 저가보다 진짜 낮아야 한다.", fontsize=11, bold=True)
    lows = [
        (1.15, 101.5, 103.0, 100.0, 102.0, "i-2", "100"),
        (2.35, 102.2, 104.0, 99.5, 103.2, "i-1", "99.5"),
        (3.55, 103.0, 104.0, 97.0, 99.0, "i", "97"),
        (4.75, 99.2, 102.0, 98.5, 101.0, "i+1", "98.5"),
        (5.95, 101.0, 103.0, 99.0, 102.0, "i+2", "99"),
    ]

    def y2(p):
        return 2.05 + (p - 96.5) * 0.42

    for x, o, h, l, c, lab, lv in lows:
        hh, ll = max(o, h, c), min(o, l, c)
        candle(ax2, x, y2(o), y2(hh), y2(ll), y2(c), w=0.55)
        txt(ax2, x, 0.85, lab, ha="center", fontsize=9, bold=True)
        txt(ax2, x, y2(ll) - 0.38, "L=" + lv, ha="center", fontsize=8, color=DN)
    ax2.scatter([3.55], [y2(97) - 0.55], marker="^", s=55, color=DN, zorder=6)

    # --- 확정 시계 ---
    ax3.set_xlim(0, 8)
    ax3.set_ylim(0, 7)
    ax3.axis("off")
    txt(ax3, 0.1, 6.55, "3. 알게 된 시각은 점의 시각과 다르다", fontsize=11, bold=True)
    rows = [
        (4.95, "#fff8e1", "봉 i 가 끝", "후보다. 오른쪽 봉이 아직 없음"),
        (3.35, "#fff8e1", "봉 i+1 이 끝", "n=2 면 아직. n=1 이면 확정"),
        (1.75, "#e8f5e9", "봉 i+n 이 끝", "이때 점을 안다. 좌표는 봉 i"),
    ]
    for y, fc, t1, t2 in rows:
        box(ax3, 0.2, y, 7.55, 1.42, fc, "#888")
        txt(ax3, 0.4, y + 0.88, t1, fontsize=11, bold=True)
        txt(ax3, 0.4, y + 0.28, t2, fontsize=10)
    txt(ax3, 0.15, 0.35, "5분 n=2 는 +10분. 3분 n=2 는 +6분. 1분 n=1 은 +1분.", fontsize=9)

    # --- 3봉 ---
    ax4.set_xlim(0, 8)
    ax4.set_ylim(0, 7)
    ax4.axis("off")
    txt(ax4, 0.1, 6.55, "4. 3봉 스윙 = 같은 식, n=1", fontsize=11, bold=True)
    tri = [
        (1.5, 101, 104, 99, 102),
        (3.2, 102, 103, 96.5, 98),
        (4.9, 98, 102, 97.5, 101),
    ]
    def y4(p):
        return 2.0 + (p - 96) * 0.42
    for i, (x, o, h, l, c) in enumerate(tri):
        candle(ax4, x, y4(o), y4(h), y4(l), y4(c), w=0.7)
        txt(ax4, x, 1.15, str(i + 1), ha="center", fontsize=11, bold=True)
    ax4.scatter([3.2], [y4(96.5) - 0.35], marker="^", s=55, color=DN)
    txt(ax4, 0.2, 0.35, "가운데 저가 < 왼 저가 그리고 < 오른 저가. 확정은 봉 3이 끝날 때.", fontsize=9)

    # --- ITH ---
    ax5.set_xlim(0, 8)
    ax5.set_ylim(0, 7)
    ax5.axis("off")
    txt(ax5, 0.1, 6.55, "5. 중간점 = 단기점들끼리 다시 3점", fontsize=11, bold=True)
    xs = [1.3, 3.5, 5.7]
    ys = [3.3, 5.2, 4.1]
    labs = ["STH 100", "STH 110", "STH 105"]
    ax5.plot(xs, ys, color="#888", lw=1.2)
    for x, y, lab in zip(xs, ys, labs):
        ax5.scatter([x], [y], s=70, color=UP, zorder=5)
    txt(ax5, 1.3, 2.55, "STH 100", ha="center", fontsize=9, color=UP)
    txt(ax5, 2.15, 5.35, "STH 110", ha="center", fontsize=9, color=UP)
    txt(ax5, 5.7, 3.35, "STH 105", ha="center", fontsize=9, color=UP)
    txt(ax5, 3.5, 5.85, "ITH = 110", ha="center", fontsize=10, bold=True, color="#6a1b9a")
    txt(ax5, 0.2, 0.45, "110>100 그리고 110>105. 확정은 오른쪽 STH 가 확정된 뒤.", fontsize=9)

    txt(fig.add_axes([0, 0.945, 1, 0.05], frameon=False), 0.5, 0.4, "점의 식. 부드러운 선이 아니다. 봉 고가·저가의 부등식이다.", ha="center", fontsize=15, bold=True)
    fig.axes[-1].axis("off")
    fig.axes[-1].set_xlim(0, 1)
    fig.axes[-1].set_ylim(0, 1)
    return save(fig, "swing_formula_fractal.png")


def render_events() -> Path:
    fig = plt.figure(figsize=(13.6, 10.2), dpi=140)
    fig.patch.set_facecolor(BG)
    gs = fig.add_gridspec(2, 2, hspace=0.28, wspace=0.16, left=0.04, right=0.98, top=0.90, bottom=0.05)
    axes = [fig.add_subplot(gs[i, j]) for i in range(2) for j in range(2)]
    titles = [
        "1. 스윕 저점. 꼬리만 깨고 종가는 위.",
        "2. 성격 바뀜(CHoCH). 종가가 저점 아래.",
        "3. 구조 이어짐(BOS). 종가가 고점 위.",
        "4. 고고·고저. 점 두 쌍으로 큰 방향.",
    ]
    for ax, t in zip(axes, titles):
        ax.set_facecolor("#fffdf8")
        ax.set_xticks([])
        ax.set_yticks([])
        for s in ("top", "right"):
            ax.spines[s].set_visible(False)
        txt(ax, 0.02, 1.04, t, transform=ax.transAxes, fontsize=12, bold=True)

    # 1 sweep
    ax = axes[0]
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)
    ax.axhline(4.2, color=DN, ls="--", lw=1.2)
    txt(ax, 0.3, 4.45, "직전 저점 SL = 10000", fontsize=10, color=DN)
    candle(ax, 2.2, 5.2, 6.0, 4.6, 5.5, w=0.8)
    candle(ax, 4.0, 5.4, 5.8, 3.2, 4.8, w=0.8)  # wick below, close above
    candle(ax, 5.8, 4.9, 6.3, 4.5, 6.0, w=0.8)
    txt(ax, 4.0, 2.55, "L=9980 < 10000", ha="center", fontsize=9, color="#2e7d32")
    txt(ax, 4.0, 1.95, "C=10030 >= 10000", ha="center", fontsize=9, color="#2e7d32")
    txt(ax, 0.4, 0.7, "스윕_저 = (L < SL) and (C >= SL)", fontsize=11, bold=True, color="#2e7d32")

    # 2 choch
    ax = axes[1]
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)
    ax.axhline(4.2, color=DN, ls="--", lw=1.2)
    txt(ax, 0.3, 4.45, "SL = 10000", fontsize=10, color=DN)
    candle(ax, 2.2, 5.2, 6.0, 4.6, 5.5, w=0.8)
    candle(ax, 4.2, 5.0, 5.4, 2.6, 3.3, w=0.8)
    txt(ax, 4.2, 1.7, "C=9920 < 10000", ha="center", fontsize=9, color=UP)
    txt(ax, 0.4, 0.7, "CHoCH_하락 = (C < SL)   ← 스윕이 아님", fontsize=11, bold=True, color=UP)

    # 3 bos
    ax = axes[2]
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)
    ax.axhline(6.3, color=UP, ls="--", lw=1.2)
    txt(ax, 0.3, 6.55, "직전 고점 SH = 11000", fontsize=10, color=UP)
    candle(ax, 2.4, 4.4, 6.0, 4.0, 5.5, w=0.8)
    candle(ax, 4.4, 5.6, 7.4, 5.3, 7.0, w=0.8)
    txt(ax, 4.4, 8.0, "C=11050 > 11000", ha="center", fontsize=9, color=UP)
    txt(ax, 0.4, 0.7, "BOS_상승 = (C > SH)   꼬리만 위면 스윕_고", fontsize=11, bold=True, color=UP)

    # 4 HH HL
    ax = axes[3]
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)
    xs = [1.4, 3.2, 5.2, 7.2]
    ys = [6.2, 3.4, 7.6, 4.3]
    labs = ["고 100", "저 90", "고 110 HH", "저 95 HL"]
    cols = [UP, DN, UP, DN]
    ax.plot(xs, ys, color="#888", lw=1.3)
    for x, y, lab, c in zip(xs, ys, labs, cols):
        ax.scatter([x], [y], s=55, color=c, zorder=5)
        txt(ax, x, y + (0.45 if c == UP else -0.55), lab, ha="center", fontsize=9, color=c)
    txt(ax, 0.4, 1.7, "HH: 지금고 > 직전고", fontsize=10)
    txt(ax, 0.4, 1.15, "HL: 지금저 > 직전저", fontsize=10)
    txt(ax, 0.4, 0.5, "둘 다 참 → 상승. 저고+저저 → 하락. 섞임 → 횡보", fontsize=10, bold=True)

    txt(fig.add_axes([0, 0.94, 1, 0.05], frameon=False), 0.5, 0.4, "사건 식. 같은 저점을 깨도 꼬리와 종가가 다른 사건이다.", ha="center", fontsize=15, bold=True)
    fig.axes[-1].axis("off")
    fig.axes[-1].set_xlim(0, 1)
    fig.axes[-1].set_ylim(0, 1)
    return save(fig, "swing_formula_events.png")


def render_trigger() -> Path:
    fig = plt.figure(figsize=(13.6, 10.8), dpi=140)
    fig.patch.set_facecolor(BG)
    gs = fig.add_gridspec(3, 2, height_ratios=[1.05, 1.0, 1.25], hspace=0.36, wspace=0.16, left=0.04, right=0.98, top=0.91, bottom=0.035)
    ax_a = fig.add_subplot(gs[0, 0])
    ax_v = fig.add_subplot(gs[0, 1])
    ax_n = fig.add_subplot(gs[1, :])
    ax_t = fig.add_subplot(gs[2, :])
    for ax in (ax_a, ax_v, ax_n, ax_t):
        ax.set_facecolor("#fffdf8")
        ax.set_xticks([])
        ax.set_yticks([])
        for s in ("top", "right"):
            ax.spines[s].set_visible(False)

    ax_a.set_xlim(0, 10)
    ax_a.set_ylim(0, 10)
    txt(ax_a, 0.25, 9.25, "A. 1분에서 3분으로 묶기", fontsize=12, bold=True)
    a_lines = [
        "키움 시각이 봉 시작이면",
        "end = 시작 + 1분",
        "그룹 = (시작-09:00)을 3분으로 나눈 몫",
        "",
        "3분 시가 = 첫째 1분 시가",
        "3분 고가 = 세 봉 고가의 최대",
        "3분 저가 = 세 봉 저가의 최소",
        "3분 종가 = 마지막 1분 종가",
        "3분 거래량 = 세 봉 합",
        "3분 end = 마지막 1분 end",
        "3개가 안 찬 그룹은 봉이 아님",
    ]
    for j, line in enumerate(a_lines):
        txt(ax_a, 0.35, 8.25 - j * 0.62, line, fontsize=10)

    ax_v.set_xlim(0, 10)
    ax_v.set_ylim(0, 10)
    txt(ax_v, 0.25, 9.25, "B. VWAP, 시그마, 전일고저", fontsize=12, bold=True)
    v_lines = [
        "TP = (고가 + 저가 + 종가) / 3",
        "VWAP = 합(TP x 거래량) / 합(거래량)",
        "시그마2 = 합(V x TP x TP)/합(V) - VWAP x VWAP",
        "오늘 09:00부터만. 어제 분봉 안 섞음",
        "",
        "예) TP 9 와 11, 거래량 각 100",
        "VWAP = 10,  시그마 = 1",
        "",
        "PDH = 어제 정규장 고가의 최대",
        "PDL = 어제 정규장 저가의 최소",
    ]
    for j, line in enumerate(v_lines):
        txt(ax_v, 0.35, 8.25 - j * 0.62, line, fontsize=10)

    ax_n.set_xlim(0, 14)
    ax_n.set_ylim(0, 6)
    txt(ax_n, 0.2, 5.45, "C. 자석 근처. 둘 중 하나면 근처.", fontsize=12, bold=True)
    box(ax_n, 0.3, 0.6, 6.3, 4.3, "#e3f2fd", DN)
    txt(ax_n, 0.55, 3.85, "abs(가격-선) / 선  <=  0.002", fontsize=12, bold=True, color=DN)
    txt(ax_n, 0.55, 2.15, "0.2%\n10000 이면 위아래 20원", fontsize=11)
    box(ax_n, 7.1, 0.6, 6.4, 4.3, "#fff3e0", "#e65100")
    txt(ax_n, 7.35, 3.85, "abs(가격-선)  <=  0.25 x ATR5분", fontsize=12, bold=True, color="#e65100")
    txt(ax_n, 7.35, 2.15, "ATR 80 이면 위아래 20원\nWilder 14봉", fontsize=11)

    ax_t.set_xlim(0, 14)
    ax_t.set_ylim(0, 8.4)
    txt(ax_t, 0.2, 7.85, "D. 매수 방아쇠. 여섯이 모두 참. 지금 1분봉이 끝난 뒤에만 본다.", fontsize=12, bold=True)
    labels = [
        ("1", ["5분 방향", "상승", "HH 그리고 HL"]),
        ("2", ["3분 저점 SL", "자석 근처"]),
        ("3", ["스윕", "L < SL", "C >= SL"]),
        ("4", ["1분 3봉 저점", "지금 봉에서", "확정"]),
        ("5", ["지금 종가", "> 저점봉 고가"]),
        ("6", ["지금 종가", ">= SL", "손절=스윕꼬리"]),
    ]
    for i, (n, labs) in enumerate(labels):
        x = 0.25 + i * 2.28
        box(ax_t, x, 2.55, 2.12, 4.7, "#fce4ec" if i in (2, 4) else "#e8f5e9", "#888")
        txt(ax_t, x + 1.06, 6.62, n, ha="center", fontsize=14, bold=True)
        for j, lab in enumerate(labs):
            txt(ax_t, x + 1.06, 5.55 - j * 0.72, lab, ha="center", fontsize=9)
        if i < 5:
            ax_t.annotate("", xy=(x + 2.20, 4.9), xytext=(x + 2.12, 4.9), arrowprops=dict(arrowstyle="->", color="#333", lw=1.2))
    txt(ax_t, 0.25, 1.55, "숫자 예. SL=10000, 스윕 봉 L=9980 C=10030, 1분 저점봉 고가=10050, 지금 봉 C=10080.", fontsize=10)
    txt(ax_t, 0.25, 0.75, "9980 < 10000 이고 10030 >= 10000 이면 스윕. 10080 > 10050 작은 돌파. 손절=9980.", fontsize=10, bold=True)
    txt(ax_t, 0.25, 0.15, "하나라도 거짓이면 사면 안 된다. 1초 D/H 는 이 여섯이 참인 뒤에만.", fontsize=10)

    txt(fig.add_axes([0, 0.945, 1, 0.05], frameon=False), 0.5, 0.4, "묶기 · VWAP · 자석 · 방아쇠. 구현에 넣는 식은 이 네 덩어리다.", ha="center", fontsize=15, bold=True)
    fig.axes[-1].axis("off")
    fig.axes[-1].set_xlim(0, 1)
    fig.axes[-1].set_ylim(0, 1)
    return save(fig, "swing_formula_trigger.png")


if __name__ == "__main__":
    print(render_fractal())
    print(render_events())
    print(render_trigger())

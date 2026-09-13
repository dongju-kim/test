"""각 국면을 차트 그림으로 설명한다."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.font_manager import FontProperties
from matplotlib.patches import FancyBboxPatch, Rectangle
from matplotlib.lines import Line2D

FP = FontProperties(fname="/usr/share/fonts/truetype/nanum/NanumGothic.ttf")
FPB = FontProperties(fname="/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf")
OUT = Path("/workspace/docs/phase_pics")
ART = Path("/opt/cursor/artifacts")
OUT.mkdir(parents=True, exist_ok=True)
ART.mkdir(parents=True, exist_ok=True)

UP = "#d32f2f"
DN = "#1565c0"
MA = "#e65100"
BOX = "#90a4ae"
NOW = "#f9a825"
BG = "#f7f4ee"


def k(s: str) -> str:
    return (
        s.replace(" ", "\u3000")
        .replace("−", "-")
        .replace("–", "-")
        .replace("—", "-")
        .replace("×", "x")
    )


def txt(ax, x, y, s, *, bold=False, **kw):
    kw.pop("fontweight", None)
    ax.text(x, y, k(s), fontproperties=FPB if bold else FP, **kw)


def candle(ax, i, o, h, l, c, width=0.62, lw=1.2, highlight=False):
    color = UP if c >= o else DN
    ax.plot([i, i], [l, h], color=color, lw=lw, solid_capstyle="round", zorder=2)
    bottom = min(o, c)
    height = abs(c - o)
    if height < 1e-6:
        height = (h - l) * 0.04 or 0.15
        bottom = c - height / 2
    ax.add_patch(
        Rectangle(
            (i - width / 2, bottom),
            width,
            height,
            facecolor=color,
            edgecolor="#222" if highlight else color,
            lw=2.0 if highlight else 0.6,
            zorder=3,
        )
    )
    if highlight:
        pad = max((h - l) * 0.18, abs(c - o) * 0.25, 0.06)
        ax.add_patch(
            Rectangle(
                (i - width / 2 - 0.1, min(l, bottom) - pad),
                width + 0.2,
                max(h, bottom + height) - min(l, bottom) + 2 * pad,
                facecolor="none",
                edgecolor=NOW,
                lw=2.0,
                linestyle="--",
                zorder=4,
            )
        )


def card(ax, x, y, w, h, fc, title, body):
    ax.add_patch(
        FancyBboxPatch(
            (x, y),
            w,
            h,
            boxstyle="round,pad=0.02,rounding_size=0.07",
            facecolor=fc,
            edgecolor="#444",
            lw=1.0,
        )
    )
    txt(ax, x + 0.12, y + h - 0.22, title, bold=True, fontsize=12, va="top")
    txt(ax, x + 0.12, y + h - 0.52, body, fontsize=9.6, va="top")


def save(fig, name: str) -> Path:
    fig.subplots_adjust(left=0.05, right=0.99, top=0.96, bottom=0.08, wspace=0.08)
    p = OUT / name
    fig.savefig(p, bbox_inches="tight", facecolor=fig.get_facecolor())
    fig.savefig(ART / name, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)
    return p


def base_fig(title: str, subtitle: str):
    fig, (axc, axn) = plt.subplots(
        1, 2, figsize=(13.6, 6.6), dpi=140, gridspec_kw={"width_ratios": [1.35, 1]}
    )
    fig.patch.set_facecolor(BG)
    axc.set_facecolor("#fffdf8")
    axn.set_facecolor(BG)
    axn.axis("off")
    axn.set_xlim(0, 10)
    axn.set_ylim(0, 10)
    txt(axn, 5, 9.55, title, ha="center", fontsize=16, bold=True)
    txt(axn, 5, 8.95, subtitle, ha="center", fontsize=10.5, color="#333")
    axc.set_xlabel("")
    axc.tick_params(labelsize=8)
    for spine in ("top", "right"):
        axc.spines[spine].set_visible(False)
    return fig, axc, axn


def style_price(ax, n: int, *series, pad: float = 2.4, title="오늘 3분 완성봉"):
    ax.set_title("")
    txt(ax, 0.02, 1.02, title, transform=ax.transAxes, fontsize=11, bold=True, va="bottom")
    ax.set_xlim(-0.55, n - 0.35)
    vals = []
    for s in series:
        vals.extend(s)
    lo, hi = min(vals) - pad, max(vals) + pad
    ax.set_ylim(lo, hi)
    ax.set_xticks(range(n))
    ax.set_xticklabels([f"{i+1}" for i in range(n)], fontproperties=FP, fontsize=8)


def draw_ma(ax, xs, ys, label="MA20"):
    ax.plot(xs, ys, color=MA, lw=2.2, zorder=5)
    ax.text(xs[-1] + 0.15, ys[-1], k(label), color=MA, fontproperties=FPB, fontsize=9, va="center")


def draw_box(ax, x0, x1, lo, hi):
    ax.add_patch(
        Rectangle((x0 - 0.4, lo), x1 - x0 + 0.8, hi - lo, facecolor="#cfd8dc", alpha=0.35, zorder=0)
    )
    ax.axhline(hi, color=BOX, lw=1.4, ls="--")
    ax.axhline(lo, color=BOX, lw=1.4, ls="--")
    gap = max((hi - lo) * 0.12, 0.12)
    ax.text(x0 - 0.15, hi + gap, k("박스 상단"), color="#455a64", fontproperties=FP, fontsize=8)
    ax.text(x0 - 0.15, lo - gap * 1.6, k("박스 하단"), color="#455a64", fontproperties=FP, fontsize=8)


def note_legend(ax):
    handles = [
        Line2D([0], [0], color=UP, lw=6, label=k("양봉")),
        Line2D([0], [0], color=DN, lw=6, label=k("음봉")),
        Line2D([0], [0], color=MA, lw=2, label=k("MA20")),
        Line2D([0], [0], color=NOW, lw=2, ls="--", label=k("지금 본 봉")),
    ]
    ax.legend(handles=handles, loc="upper left", prop=FP, fontsize=8, framealpha=0.92)


def render_priority() -> Path:
    fig, ax = plt.subplots(figsize=(13.4, 5.6), dpi=140)
    fig.patch.set_facecolor(BG)
    ax.set_xlim(0, 13.4)
    ax.set_ylim(0, 5.6)
    ax.axis("off")
    ax.set_facecolor(BG)
    txt(ax, 6.7, 5.2, "한 봉에 국면 하나. 위가 이긴다", ha="center", fontsize=18, bold=True)
    txt(ax, 6.7, 4.72, "3분 종가가 끝났을 때만. 꼬리·진행 중 봉·1초로 국면을 안 바꿈.", ha="center", fontsize=11)

    rows = [
        ("1 급락", "#f4d4d0", "한 봉", "사면 안 된다 · 전량"),
        ("2 돌파", "#d6e8d8", "한 봉", "사도 된다 (09:18+)"),
        ("3 눌림", "#dce6f4", "인정 2봉", "사도 된다 (10:00+ · 점)"),
        ("4 급등", "#efe3c6", "인정 2봉", "새로 사지 않는다 · 나눠 판다"),
        ("5 횡보", "#e4e4e4", "인정 2봉", "사면 안 된다 · 점 안 찾음"),
        ("6 관망", "#eeeae3", "나머지", "사면 안 된다"),
    ]
    for i, (t, fc, bar, act) in enumerate(rows):
        x = 0.35 + (i % 3) * 4.3
        y = 2.45 if i < 3 else 0.25
        ax.add_patch(
            FancyBboxPatch((x, y), 4.1, 1.95, boxstyle="round,pad=0.03,rounding_size=0.08", facecolor=fc, edgecolor="#444")
        )
        txt(ax, x + 0.18, y + 1.55, t, bold=True, fontsize=14)
        txt(ax, x + 0.18, y + 1.05, bar, fontsize=11, bold=True, color="#333")
        txt(ax, x + 0.18, y + 0.45, act, fontsize=11)

    return save(fig, "phase_00_priority.png")


def render_dump() -> Path:
    # closes dip hard below MA20
    o = [100, 101, 102, 101, 100, 98, 95]
    c = [101, 102, 101, 100, 97, 94, 91]
    h = [102, 103, 103, 101.5, 100.2, 98.2, 95.5]
    l = [99.5, 100.4, 100.2, 99.6, 96.5, 93.5, 90.4]
    ma = [100.2, 100.5, 100.7, 100.6, 100.2, 99.4, 98.2]
    fig, axc, axn = base_fig("1. 급락", "사면 안 된다. 들고 있으면 그 봉에 전량.")
    for i in range(7):
        candle(axc, i, o[i], h[i], l[i], c[i], highlight=(i == 6))
    draw_ma(axc, range(7), ma)
    axc.annotate(
        k("종가 < MA20 - 0.5%"),
        xy=(6, c[6]),
        xytext=(3.1, 89.6),
        fontproperties=FP,
        fontsize=9,
        arrowprops=dict(arrowstyle="->", color="#8b2e24"),
        color="#8b2e24",
    )
    style_price(axc, 7, l, h, ma)
    note_legend(axc)
    card(axn, 0.4, 5.9, 9.2, 2.7, "#f4d4d0", "자리 (이걸로 가림)", "종가 < MA20보다 0.5% 아래\n또는 종가 2개가 모두 MA20 아래\n개장: 시가-1% 또는 박스 하단 종가")
    card(axn, 0.4, 3.15, 9.2, 2.5, "#fff", "봉 / s_n", "한 봉. 2봉을 얹지 않음.\ns_n 이 음수여도 급락이 아님.\n자리는 종가 vs MA20.")
    card(axn, 0.4, 0.35, 9.2, 2.55, "#f8e8e4", "그다음", "안 산다. 걸어 둔 주문 취소.\n전량. H가 초록이어도.")
    return save(fig, "phase_01_dump.png")


def render_fake_dump() -> Path:
    o = [100, 101, 102, 103, 102, 101.4, 100.8]
    c = [101, 102.2, 103, 102.4, 101.2, 100.6, 100.4]
    h = [101.6, 102.8, 104, 103.2, 102.4, 101.6, 101.1]
    l = [99.7, 100.6, 101.5, 101.8, 99.2, 99.4, 99.6]
    ma = [100.4, 100.7, 101.1, 101.5, 101.6, 101.5, 101.4]
    fig, axc, axn = base_fig("가짜 급락 = 눌림 쪽", "꼬리만 MA20 아래. 종가는 근처. 급락이 아니다.")
    for i in range(7):
        candle(axc, i, o[i], h[i], l[i], c[i], highlight=(i == 6))
    draw_ma(axc, range(7), ma)
    axc.annotate(
        k("꼬리만 아래"),
        xy=(4, l[4]),
        xytext=(1.2, 98.4),
        fontproperties=FP,
        fontsize=9,
        arrowprops=dict(arrowstyle="->", color="#1565c0"),
    )
    axc.annotate(
        k("종가는 MA20 +-0.3%"),
        xy=(6, c[6]),
        xytext=(3.4, 103.8),
        fontproperties=FP,
        fontsize=9,
        arrowprops=dict(arrowstyle="->", color=MA),
    )
    style_price(axc, 7, l, h, ma)
    note_legend(axc)
    card(axn, 0.4, 4.6, 9.2, 3.9, "#dce6f4", "왜 급락이 아닌가", "국면은 종가로만.\n꼬리는 안 씀.\n오늘 +1%를 한 적 있으면\n눌림 후보.\n인정은 2봉 + 바닥 점.")
    card(axn, 0.4, 0.4, 9.2, 3.85, "#fff", "s_n", "한 봉 음수여도 큰 방향을\n당장 하락으로 안 바꿈.\n자리는 눌림일 수 있음.")
    return save(fig, "phase_01b_fake_dump.png")


def render_break() -> Path:
    o = [100, 100.2, 100.4, 100.3, 100.5, 100.8, 101.8]
    c = [100.3, 100.5, 100.2, 100.6, 100.7, 101.0, 102.6]
    h = [100.6, 100.9, 100.7, 100.8, 101.1, 101.3, 102.9]
    l = [99.8, 99.9, 99.7, 100.0, 100.2, 100.5, 101.6]
    fig, axc, axn = base_fig("2. 돌파", "이번 종가가 박스 위. 꼬리만 위면 아님.")
    draw_box(axc, 0, 5, 99.7, 101.15)
    for i in range(7):
        candle(axc, i, o[i], h[i], l[i], c[i], highlight=(i == 6))
    style_price(axc, 7, l, h, pad=1.8)
    note_legend(axc)
    axc.annotate(
        k("종가가 위로 끝남"),
        xy=(6, c[6]),
        xytext=(2.4, 103.1),
        fontproperties=FP,
        fontsize=9,
        arrowprops=dict(arrowstyle="->", color="#1b5e20"),
    )
    card(axn, 0.4, 5.7, 9.2, 2.85, "#d6e8d8", "자리", "고정 박스면 종가 > 상단\n아니면 봉 6개+ 이고\n종가 > 직전 고점")
    card(axn, 0.4, 3.0, 9.2, 2.45, "#fff", "봉 / s_n", "한 봉. 2봉 기다리면 놓침.\ns_n 으로 박스를 대체 안 함.\n큰 방향이 하락이면 안 산다.")
    card(axn, 0.4, 0.35, 9.2, 2.4, "#e8f5e9", "그다음", "09:18+ 사도 된다.\n추격=매도1호가.\n1·2차 없음. 손절만.")
    return save(fig, "phase_02_break.png")


def render_fake_break() -> Path:
    o = [100, 100.2, 100.4, 100.3, 100.5, 100.6, 100.7]
    c = [100.3, 100.5, 100.2, 100.6, 100.4, 100.8, 100.5]
    h = [100.6, 100.8, 100.7, 100.9, 101.0, 102.4, 101.1]
    l = [99.8, 99.9, 99.7, 100.0, 100.1, 100.3, 100.2]
    fig, axc, axn = base_fig("가짜 돌파 = 횡보 유지", "꼬리만 박스 위. 종가는 박스 안.")
    draw_box(axc, 0, 6, 99.7, 101.05)
    for i in range(7):
        candle(axc, i, o[i], h[i], l[i], c[i], highlight=(i == 5))
    style_price(axc, 7, l, h, pad=1.6)
    note_legend(axc)
    axc.annotate(
        k("꼬리만 위"),
        xy=(5, h[5]),
        xytext=(1.6, 102.7),
        fontproperties=FP,
        fontsize=9,
        arrowprops=dict(arrowstyle="->", color="#8b2e24"),
    )
    card(axn, 0.4, 4.4, 9.2, 4.15, "#e4e4e4", "국면은 안 바뀜", "종가가 박스 안이면\n돌파가 아니다.\nH가 커져도 안 산다.\n박스는 그대로.")
    card(axn, 0.4, 0.4, 9.2, 3.7, "#fff", "기억", "고가(꼬리)로\n국면을 안 가림.")
    return save(fig, "phase_02b_fake_break.png")


def render_pullback() -> Path:
    o = [100, 102, 104, 105.5, 104.8, 103.6, 103.1]
    c = [102, 104, 105.2, 104.6, 103.8, 103.2, 103.0]
    h = [102.4, 104.6, 106.0, 106.2, 105.0, 104.0, 103.6]
    l = [99.6, 101.5, 103.4, 104.2, 103.4, 102.8, 102.6]
    ma = np.array([101.2, 101.8, 102.5, 103.0, 103.2, 103.25, 103.2])
    fig, axc, axn = base_fig("3. 눌림", "급등/돌파 이후, 종가가 MA20 근처. 바닥 점 후에만 산다.")
    for i in range(7):
        candle(axc, i, o[i], h[i], l[i], c[i], highlight=(i == 6))
    draw_ma(axc, range(7), ma)
    band_lo, band_hi = ma[-1] * 0.997, ma[-1] * 1.003
    axc.axhspan(band_lo, band_hi, color="#bbdefb", alpha=0.45, zorder=0)
    txt(axc, 0.1, band_hi + 0.35, "MA20 +-0.3%", fontsize=8, color="#0d47a1")
    style_price(axc, 7, l, h, ma)
    note_legend(axc)
    card(axn, 0.4, 5.55, 9.2, 3.05, "#dce6f4", "자리 (모두)", "오늘 +1% 또는 돌파/급등 기억\n종가 MA20 +-0.3%\n거래량 <= 상승 최고 x 0.5\n10:00 이후 + 1분 바닥 점")
    card(axn, 0.4, 2.95, 9.2, 2.35, "#fff", "봉 / s_n", "인정은 2봉. 한 봉 스침 아님.\n큰 방향이 하락이면 안 산다.\ns_n 으로 점을 안 정함.")
    card(axn, 0.4, 0.3, 9.2, 2.4, "#e3f2fd", "그다음", "추격=직전가.\n1·2차 없음. 손절만.\n횡보면 점을 찾지 않음.")
    return save(fig, "phase_03_pullback.png")


def render_surge() -> Path:
    o = [100, 101.5, 103, 104.2, 105, 106.2, 107]
    c = [101.6, 103.2, 104.4, 105.3, 106.4, 107.3, 108.2]
    h = [102, 103.8, 105, 105.9, 107, 107.9, 108.8]
    l = [99.8, 101.2, 102.6, 103.8, 104.7, 105.8, 106.6]
    ma = np.linspace(100.6, 104.8, 7)
    fig, axc, axn = base_fig("4. 급등", "MA20 위, MA20과 떨어져 있음. 새로 사지 않는다.")
    for i in range(7):
        candle(axc, i, o[i], h[i], l[i], c[i], highlight=(i == 6))
    draw_ma(axc, range(7), ma)
    axc.annotate(
        k("이격 > 0.3%\nMA20 우상향"),
        xy=(6, c[6]),
        xytext=(2.0, 109.2),
        fontproperties=FP,
        fontsize=9,
        arrowprops=dict(arrowstyle="->", color=MA),
    )
    style_price(axc, 7, l, h, list(ma))
    note_legend(axc)
    card(axn, 0.4, 5.6, 9.2, 3.0, "#efe3c6", "자리 (모두)", "종가 > MA20\nMA20과 0.3%보다 멀다\n지금 MA20 > 3봉 전 MA20\n충동 있음. 박스 첫 종가 아님")
    card(axn, 0.4, 3.0, 9.2, 2.35, "#fff", "봉 / s_n", "인정은 2봉.\ns_n + 유지는 확인만.\n1초로 추매하지 않음.")
    card(axn, 0.4, 0.3, 9.2, 2.45, "#fff8e1", "그다음", "새로 사지 않는다.\n1차=양수 H 첫 축소\n2차=H<=0. 손절은 그대로.")
    return save(fig, "phase_04_surge.png")


def render_range() -> Path:
    o = [100.2, 100.5, 100.1, 100.6, 100.3, 100.4, 100.2]
    c = [100.5, 100.2, 100.5, 100.3, 100.6, 100.2, 100.4]
    h = [100.8, 100.7, 100.8, 100.9, 100.85, 100.7, 100.75]
    l = [99.9, 99.95, 99.85, 100.05, 100.0, 99.9, 100.0]
    ma5 = [100.35] * 7
    ma20 = [100.32] * 7
    fig, axc, axn = base_fig("5. 짧은 횡보", "폭이 좁고 이평이 붙고 거래량이 조용. 안 산다.")
    draw_box(axc, 0, 6, 99.85, 100.9)
    for i in range(7):
        candle(axc, i, o[i], h[i], l[i], c[i], highlight=(i == 6))
    axc.plot(range(7), ma5, color="#6a1b9a", lw=1.8)
    draw_ma(axc, range(7), ma20, "MA20")
    axc.text(6.15, 100.38, k("MA5"), color="#6a1b9a", fontproperties=FP, fontsize=8)
    style_price(axc, 7, l, h, pad=0.35)
    note_legend(axc)
    card(axn, 0.4, 5.55, 9.2, 3.05, "#e4e4e4", "자리 (모두)", "폭 < 1.5%\n거래량 조용 (최근3 < 평균 x1.5)\n|MA5-MA20| / MA20 < 0.5%\n이때 박스 고정")
    card(axn, 0.4, 2.95, 9.2, 2.35, "#fff", "봉 / s_n", "인정은 2봉.\n한 봉 조용하다고 고정 안 함.\n|s_n|이 크면 횡보 의심.")
    card(axn, 0.4, 0.3, 9.2, 2.4, "#eeeeee", "그다음", "안 산다. H가 커져도.\n바닥 점을 찾지 않음.")
    return save(fig, "phase_05_range.png")


def render_watch() -> Path:
    o = [100, 101.2, 100.4, 101.6, 100.2, 101.8, 100.6]
    c = [101.1, 100.5, 101.5, 100.3, 101.7, 100.4, 101.4]
    h = [101.6, 101.8, 102.0, 102.1, 102.2, 102.3, 102.0]
    l = [99.6, 100.0, 100.1, 99.9, 100.0, 100.1, 100.2]
    ma = [100.4, 100.5, 100.6, 100.6, 100.7, 100.7, 100.8]
    fig, axc, axn = base_fig("6. 관망", "위 다섯이 아니면 관망. 사면 안 된다.")
    for i in range(7):
        candle(axc, i, o[i], h[i], l[i], c[i], highlight=(i == 6))
    draw_ma(axc, range(7), ma)
    style_price(axc, 7, l, h, ma)
    note_legend(axc)
    card(axn, 0.4, 4.7, 9.2, 3.85, "#eeeae3", "언제인가", "급락도, 돌파도,\n눌림도, 급등도,\n짧은 횡보도 아님.\n09:03 전·완성봉 0개도 여기.")
    card(axn, 0.4, 0.4, 9.2, 4.0, "#fff", "그다음", "안 산다.\n큰 방향도 아직이면\n직전 라벨 유지.\n억지로 국면을 만들지 않음.")
    return save(fig, "phase_06_watch.png")


def render_day() -> Path:
    fig, ax = plt.subplots(figsize=(13.6, 6.8), dpi=140)
    fig.patch.set_facecolor(BG)
    ax.set_xlim(0, 13.6)
    ax.set_ylim(0, 6.8)
    ax.axis("off")
    ax.set_facecolor(BG)
    txt(ax, 6.8, 6.4, "하루를 그림으로만", ha="center", fontsize=18, bold=True)
    txt(ax, 6.8, 5.95, "급한 안전은 한 봉. 느린 인정은 두 봉. 사는 것은 맨 아래.", ha="center", fontsize=11)

    steps = [
        ("09:00-09:18", "#eeeeee", "박스만 모음\n새로 사지 않음"),
        ("09:18 돌파", "#d6e8d8", "종가 > 박스\n한 봉. 사도 됨"),
        ("급등 인정", "#efe3c6", "MA20 위 2봉\n새로 안 삼 · 나눠 팜"),
        ("눌림 인정", "#dce6f4", "MA20 근처 2봉\n+ 1분 점. 10:00+"),
        ("급락이면", "#f4d4d0", "종가 MA20-0.5%\n한 봉. 전량"),
    ]
    for i, (t, fc, b) in enumerate(steps):
        x = 0.3 + i * 2.66
        ax.add_patch(
            FancyBboxPatch((x, 3.15), 2.5, 2.45, boxstyle="round,pad=0.03,rounding_size=0.08", facecolor=fc, edgecolor="#444")
        )
        txt(ax, x + 1.25, 5.25, t, ha="center", fontsize=11, bold=True)
        txt(ax, x + 1.25, 4.15, b, ha="center", va="center", fontsize=10)
        if i < 4:
            ax.annotate("", xy=(x + 2.58, 4.35), xytext=(x + 2.5, 4.35), arrowprops=dict(arrowstyle="->", color="#333"))

    ax.add_patch(
        FancyBboxPatch(
            (0.3, 0.3), 13.0, 2.55, boxstyle="round,pad=0.03,rounding_size=0.08", facecolor="#d7ecd8", edgecolor="#1b5e20", lw=1.3
        )
    )
    txt(ax, 6.8, 2.4, "사려면 세 층이 같이 맞아야 한다", ha="center", fontsize=13, bold=True, color="#1b5e20")
    txt(
        ax,
        6.8,
        1.25,
        "큰 방향 = 상승 (s_n + 히스테리시스 + 2봉)\n"
        "상세 국면 = 돌파 또는 눌림 (자리는 종가·MA20·박스)\n"
        "타점 = 1초 D·H. 국면·점은 1초로 안 정함.",
        ha="center",
        va="center",
        fontsize=11,
    )
    return save(fig, "phase_07_day.png")


if __name__ == "__main__":
    paths = [
        render_priority(),
        render_dump(),
        render_fake_dump(),
        render_break(),
        render_fake_break(),
        render_pullback(),
        render_surge(),
        render_range(),
        render_watch(),
        render_day(),
    ]
    for p in paths:
        print(p)

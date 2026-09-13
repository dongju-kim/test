"""s_n · 히스테리시스 · 2봉 설명 그림."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
from matplotlib.patches import FancyBboxPatch, Rectangle

FP = FontProperties(fname="/usr/share/fonts/truetype/nanum/NanumGothic.ttf")
FPB = FontProperties(fname="/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf")
OUT = Path("/workspace/docs")
ART = Path("/opt/cursor/artifacts")
ART.mkdir(parents=True, exist_ok=True)


def k(s: str) -> str:
    return s.replace(" ", "\u3000").replace("−", "-").replace("–", "-").replace("—", "-")


def txt(ax, x, y, s, *, bold=False, **kw):
    kw.pop("fontweight", None)
    ax.text(x, y, k(s), fontproperties=FPB if bold else FP, **kw)


def render() -> Path:
    fig, axes = plt.subplots(3, 1, figsize=(13.2, 11.2), dpi=140)
    fig.patch.set_facecolor("#f7f4ee")
    for ax in axes:
        ax.set_facecolor("#f7f4ee")
        ax.axis("off")

    # ---- 1 s_n ----
    ax = axes[0]
    ax.set_xlim(0, 13.2)
    ax.set_ylim(0, 3.6)
    txt(ax, 6.6, 3.35, "1. s_n  =  (이번 G - 직전 G)  /  ATR", ha="center", fontsize=16, bold=True)
    txt(ax, 6.6, 2.95, "부드러운 선이 이번 3분에, 평소 출렁임의 몇 배만큼 움직였나. 국면 이름이 아님.", ha="center", fontsize=11)

    boxes = [
        (0.35, 0.35, 4.0, 2.3, "#d9e6f2", "G  부드러운 선", "오늘 끝난 3분 종가만.\n가까운 봉에 더 무게.\n미래 봉 안 씀.\n6~12분 늦는 게 정상."),
        (4.6, 0.35, 4.0, 2.3, "#f3e2c8", "ATR  평소 출렁임", "같은 +200원도\nATR 800이면 약함\nATR 150이면 셈.\n종목·날의 자."),
        (8.85, 0.35, 4.0, 2.3, "#d7ecd8", "s_n  이번 속도", "+0.8  위로 세다\n+0.15 위로 약함\n 0     거의 안 움직임\n-0.8  아래로 세다"),
    ]
    for x, y, w, h, fc, title, body in boxes:
        ax.add_patch(
            FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.03,rounding_size=0.08", facecolor=fc, edgecolor="#444", lw=1.1)
        )
        txt(ax, x + 0.18, y + h - 0.28, title, bold=True, fontsize=12, va="top")
        txt(ax, x + 0.18, y + h - 0.7, body, fontsize=10, va="top")

    # ---- 2 hysteresis ----
    ax = axes[1]
    ax.set_xlim(0, 13.2)
    ax.set_ylim(0, 3.6)
    txt(ax, 6.6, 3.35, "2. 히스테리시스  =  들어올 때 선과 나갈 때 선이 다름", ha="center", fontsize=16, bold=True)
    txt(ax, 6.6, 2.98, "한 선이면 09:21 +0.35 상승, 09:24 +0.15 횡보, 다음 봉 다시 상승. 깜빡임.", ha="center", fontsize=11)

    # vertical band sketch
    ax.add_patch(Rectangle((0.5, 0.35), 12.2, 2.4, facecolor="#fffdf8", edgecolor="#888", lw=1.0))
    # regions from bottom: down, keep-down, middle keep, keep-up, up
    # map s_n -0.5..+0.5 to y 0.45..2.55
    def y_of(sn):
        return 1.5 + sn * 2.0

    bands = [
        (-0.55, -0.30, "#f4d4d0", "하락으로 들어옴  < -0.30"),
        (-0.30, -0.12, "#f8e8e4", "이미 하락이면 유지"),
        (-0.12, 0.12, "#eeeeee", "중간. 지금 라벨 유지"),
        (0.12, 0.30, "#e6f0e6", "이미 상승이면 유지"),
        (0.30, 0.55, "#cfe6d0", "상승으로 들어옴  > +0.30"),
    ]
    for a, b, c, lab in bands:
        y0, y1 = y_of(a), y_of(b)
        ax.add_patch(Rectangle((1.7, y0), 5.6, y1 - y0, facecolor=c, edgecolor="#666", lw=0.6))
        txt(ax, 4.5, (y0 + y1) / 2, lab, ha="center", va="center", fontsize=9.5)

    txt(ax, 1.35, 2.55, "+", ha="center", fontsize=12, bold=True)
    txt(ax, 1.35, 0.5, "-", ha="center", fontsize=12, bold=True)
    txt(ax, 10.4, 1.9, "난방과 같음.\n18도에서 켜고\n21도에서만 끔.\n19도에서\n켜졌다 꺼졌다\n하지 않음.", ha="center", va="center", fontsize=10)

    # ---- 3 two bars ----
    ax = axes[2]
    ax.set_xlim(0, 13.2)
    ax.set_ylim(0, 3.6)
    txt(ax, 6.6, 3.35, "3. 2봉  =  느린 라벨만 완성봉 두 개. 급한 것은 한 개", ha="center", fontsize=16, bold=True)

    ax.add_patch(
        FancyBboxPatch((0.35, 0.35), 6.2, 2.7, boxstyle="round,pad=0.03,rounding_size=0.08", facecolor="#f4d4d0", edgecolor="#8b2e24", lw=1.2)
    )
    txt(ax, 3.45, 2.75, "한 봉 (급함)", ha="center", fontsize=13, bold=True)
    txt(
        ax,
        3.45,
        1.55,
        "급락   한 봉 늦으면 더 들고 있음\n돌파   조건이 이번 종가 > 박스\n\n자리 조건이 이미 세다.\n여기에 2봉을 얹지 않음.",
        ha="center",
        va="center",
        fontsize=11,
    )

    ax.add_patch(
        FancyBboxPatch((6.75, 0.35), 6.1, 2.7, boxstyle="round,pad=0.03,rounding_size=0.08", facecolor="#d9e6f2", edgecolor="#1d4f7a", lw=1.2)
    )
    txt(ax, 9.8, 2.75, "두 봉 (느림)", ha="center", fontsize=13, bold=True)
    txt(
        ax,
        9.8,
        1.55,
        "큰 방향  상승/하락/횡보\n급등 · 눌림 · 짧은 횡보 인정\n\n한 봉 스침을 국면으로\n안 봄.",
        ha="center",
        va="center",
        fontsize=11,
    )

    path = OUT / "sn_hysteresis_2bars.png"
    fig.tight_layout()
    fig.savefig(path, bbox_inches="tight", facecolor=fig.get_facecolor())
    fig.savefig(ART / "sn_hysteresis_2bars.png", bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)
    return path


if __name__ == "__main__":
    print(render())

"""두 층 vs 한 리스트 비교 그림."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

FP = FontProperties(fname="/usr/share/fonts/truetype/nanum/NanumGothic.ttf")
FPB = FontProperties(fname="/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf")
OUT = Path("/workspace/docs")
ART = Path("/opt/cursor/artifacts")
ART.mkdir(parents=True, exist_ok=True)
BG = "#f7f4ee"


def k(s: str) -> str:
    return s.replace(" ", "\u3000").replace("−", "-").replace("–", "-").replace("—", "-")


def txt(ax, x, y, s, *, bold=False, **kw):
    kw.pop("fontweight", None)
    ax.text(x, y, k(s), fontproperties=FPB if bold else FP, **kw)


def box(ax, x, y, w, h, fc, title, body="", ec="#444"):
    ax.add_patch(
        FancyBboxPatch(
            (x, y), w, h, boxstyle="round,pad=0.03,rounding_size=0.08", facecolor=fc, edgecolor=ec, lw=1.15
        )
    )
    txt(ax, x + w / 2, y + h - 0.28, title, ha="center", fontsize=12, bold=True)
    if body:
        txt(ax, x + w / 2, y + h / 2 - 0.12, body, ha="center", va="center", fontsize=10)


def render() -> Path:
    fig, ax = plt.subplots(figsize=(13.6, 8.8), dpi=140)
    fig.patch.set_facecolor(BG)
    ax.set_xlim(0, 13.6)
    ax.set_ylim(0, 8.8)
    ax.axis("off")
    ax.set_facecolor(BG)

    txt(ax, 6.8, 8.4, "두 층이 낫다. 한 리스트로 처음부터 나누지 말 것", ha="center", fontsize=17, bold=True)
    txt(
        ax,
        6.8,
        7.95,
        "세 부(하락·횡보·상승)는 판. 급락·돌파·눌림·급등은 그 판 안의 자리.",
        ha="center",
        fontsize=11,
    )

    # Left: two layers (good)
    ax.add_patch(
        FancyBboxPatch(
            (0.25, 0.3), 6.4, 7.35, boxstyle="round,pad=0.03,rounding_size=0.1", facecolor="#e8f5e9", edgecolor="#1b5e20", lw=1.6
        )
    )
    txt(ax, 3.45, 7.3, "추천: 두 층", ha="center", fontsize=15, bold=True, color="#1b5e20")

    box(ax, 0.5, 5.85, 1.85, 1.15, "#f4d4d0", "하락", "새로 안 삼")
    box(ax, 2.5, 5.85, 1.85, 1.15, "#eeeeee", "횡보", "점 안 찾음")
    box(ax, 4.5, 5.85, 1.85, 1.15, "#c8e6c9", "상승", "자리만 봄")
    txt(ax, 3.45, 5.55, "1층  큰 방향   s_n + ER + 2봉", ha="center", fontsize=10)

    txt(ax, 3.45, 5.15, "상승일 때만 아래로", ha="center", fontsize=10, color="#1b5e20")
    ax.annotate("", xy=(3.45, 4.95), xytext=(3.45, 5.38), arrowprops=dict(arrowstyle="->", color="#1b5e20", lw=1.4))

    box(ax, 0.5, 3.55, 1.4, 1.2, "#f4d4d0", "급락", "한 봉 · 전량")
    box(ax, 2.0, 3.55, 1.4, 1.2, "#d6e8d8", "돌파", "한 봉 · 살 수")
    box(ax, 3.5, 3.55, 1.4, 1.2, "#dce6f4", "눌림", "2봉 · 살 수")
    box(ax, 5.0, 3.55, 1.4, 1.2, "#efe3c6", "급등", "2봉 · 안 삼")
    txt(ax, 3.45, 3.25, "2층  자리   종가 vs MA20 · 박스", ha="center", fontsize=10)

    txt(
        ax,
        3.45,
        1.7,
        "사려면 상승 그리고 (돌파 또는 눌림)\n"
        "하락인데 돌파처럼 보여도 안 삼\n"
        "눌림은 상승 안의 자리이지\n"
        "하락과 같은 급이 아님",
        ha="center",
        va="center",
        fontsize=10.5,
    )

    # Right: flat (bad)
    ax.add_patch(
        FancyBboxPatch(
            (6.95, 0.3), 6.4, 7.35, boxstyle="round,pad=0.03,rounding_size=0.1", facecolor="#fdecea", edgecolor="#8b2e24", lw=1.6
        )
    )
    txt(ax, 10.15, 7.3, "비추천: 한 리스트", ha="center", fontsize=15, bold=True, color="#8b2e24")

    flats = [
        (7.2, 5.85, "하락"),
        (8.85, 5.85, "횡보"),
        (10.5, 5.85, "상승"),
        (7.2, 4.4, "눌림"),
        (8.85, 4.4, "급등"),
        (10.5, 4.4, "급락"),
        (8.0, 2.95, "돌파?"),
        (9.8, 2.95, "관망?"),
    ]
    for x, y, t in flats:
        box(ax, x, y, 1.5, 1.05, "#fff", t, "", ec="#8b2e24")

    txt(ax, 10.15, 5.55, "같은 줄에 두면 싸움이 남", ha="center", fontsize=10, color="#8b2e24")

    # conflict arrows
    ax.add_patch(FancyArrowPatch((8.0, 5.85), (8.0, 5.45), arrowstyle="<->", color="#8b2e24", mutation_scale=10, lw=1.2))
    txt(ax, 7.55, 2.15, "눌림은 상승인가 하락인가?\n급락과 하락은 같은 말인가?\n한 봉 급락을 2봉 상승과\n누가 이기는가?", ha="center", va="center", fontsize=10.5)

    path = OUT / "two_layer_vs_flat.png"
    fig.savefig(path, bbox_inches="tight", facecolor=fig.get_facecolor())
    fig.savefig(ART / "two_layer_vs_flat.png", bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)
    return path


if __name__ == "__main__":
    print(render())

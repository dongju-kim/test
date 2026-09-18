"""밥그릇(변곡)으로 저점·고점을 보는 그림."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.font_manager import FontProperties
from matplotlib.patches import FancyBboxPatch

FP = FontProperties(fname="/usr/share/fonts/truetype/nanum/NanumGothic.ttf")
FPB = FontProperties(fname="/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf")
OUT = Path("/workspace/docs")
ART = Path("/opt/cursor/artifacts")
ART.mkdir(parents=True, exist_ok=True)
BG = "#f7f4ee"


def k(s: str) -> str:
    return s.replace(" ", "\u3000").replace("−", "-")


def txt(ax, x, y, s, *, bold=False, **kw):
    kw.pop("fontweight", None)
    ax.text(x, y, k(s), fontproperties=FPB if bold else FP, **kw)


def render() -> Path:
    fig, axes = plt.subplots(2, 2, figsize=(13.4, 8.6), dpi=140)
    fig.patch.set_facecolor(BG)
    fig.suptitle("")

    # --- 1 jagged vs bowl ---
    ax = axes[0, 0]
    ax.set_facecolor("#fffdf8")
    rng = np.random.default_rng(2)
    t = np.linspace(0, 10, 40)
    bowl = 0.08 * (t - 5) ** 2 + 2.0
    noise = rng.normal(0, 0.18, size=t.size)
    px = bowl + noise
    ax.plot(t, px, color="#90a4ae", lw=1.0, drawstyle="steps-mid")
    ax.plot(t, bowl, color="#e65100", lw=2.6)
    ax.scatter([5], [2.0], s=80, zorder=5, color="#1565c0")
    ax.text(5.15, 1.55, k("변곡 = 저점"), fontproperties=FP, fontsize=9, color="#1565c0")
    ax.set_xticks([])
    ax.set_yticks([])
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    txt(ax, 0.02, 1.04, "1. 지저분한 봉은 버리고, 부드러운 선 G 를 본다", transform=ax.transAxes, fontsize=11, bold=True)
    txt(ax, 0.02, 0.02, "회색 = 가격 톱니. 주황 = 밥그릇(G). 점은 G 가 꺾인 곳.", transform=ax.transAxes, fontsize=9)

    # --- 2 bowl vs inverted ---
    ax = axes[0, 1]
    ax.set_facecolor("#fffdf8")
    tt = np.linspace(-1.2, 1.2, 80)
    ax.plot(tt, tt ** 2, color="#1565c0", lw=2.8)
    ax.plot(tt + 2.8, -(tt ** 2) + 1.45, color="#d32f2f", lw=2.8)
    ax.annotate("", xy=(-0.15, 0.12), xytext=(-0.85, 0.55), arrowprops=dict(arrowstyle="->", color="#1565c0"))
    ax.annotate("", xy=(0.15, 0.12), xytext=(0.85, 0.55), arrowprops=dict(arrowstyle="->", color="#1565c0"))
    ax.annotate("", xy=(2.65, 1.32), xytext=(1.95, 0.85), arrowprops=dict(arrowstyle="->", color="#d32f2f"))
    ax.annotate("", xy=(2.95, 1.32), xytext=(3.65, 0.85), arrowprops=dict(arrowstyle="->", color="#d32f2f"))
    txt(ax, 0.0, -0.25, "밥그릇 = 저점", ha="center", fontsize=11, bold=True, color="#1565c0")
    txt(ax, 2.8, -0.25, "거꾸로 = 고점", ha="center", fontsize=11, bold=True, color="#d32f2f")
    ax.set_xlim(-1.5, 4.2)
    ax.set_ylim(-0.45, 1.7)
    ax.set_xticks([])
    ax.set_yticks([])
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    txt(ax, 0.02, 1.04, "2. 모양은 두 개뿐. 컵 손잡이·엘리엇은 안 씀", transform=ax.transAxes, fontsize=11, bold=True)

    # --- 3 speed numbers ---
    ax = axes[1, 0]
    ax.set_facecolor("#fffdf8")
    ax.axis("off")
    ax.add_patch(FancyBboxPatch((0.04, 0.08), 0.92, 0.82, boxstyle="round,pad=0.02,rounding_size=0.04", facecolor="#e3f2fd", edgecolor="#1565c0", transform=ax.transAxes))
    txt(ax, 0.08, 0.78, "저점 후보 (밥그릇 바닥)", transform=ax.transAxes, fontsize=12, bold=True, color="#1565c0")
    txt(
        ax,
        0.08,
        0.42,
        "s_n 이 - 에서 0 쪽으로 (내려감이 약해짐)\n"
        "그리고 c_n = s_n 의 변화가 +\n"
        "쉬운 말: 아직 아래인데 꺾이기 시작\n"
        "한 봉 톱니로 점 찍지 않음. 2봉.\n"
        "자리는 다음 3분의 1분으로만 다듬음.",
        transform=ax.transAxes,
        fontsize=10,
        va="center",
    )

    # --- 4 high + what not ---
    ax = axes[1, 1]
    ax.set_facecolor("#fffdf8")
    ax.axis("off")
    ax.add_patch(FancyBboxPatch((0.04, 0.08), 0.92, 0.82, boxstyle="round,pad=0.02,rounding_size=0.04", facecolor="#ffebee", edgecolor="#c62828", transform=ax.transAxes))
    txt(ax, 0.08, 0.78, "고점 후보 (거꾸로 밥그릇)", transform=ax.transAxes, fontsize=12, bold=True, color="#c62828")
    txt(
        ax,
        0.08,
        0.42,
        "s_n 이 + 에서 0 쪽으로 (올라감이 약해짐)\n"
        "그리고 c_n 이 -\n"
        "1초 H, 지그재그, 컵앤핸들은 점 아님\n"
        "횡보면 점을 찾지 않음\n"
        "급락이면 점은 따라가도 새로 안 삼",
        transform=ax.transAxes,
        fontsize=10,
        va="center",
    )

    fig.tight_layout(rect=(0, 0, 1, 0.97))
    txt(fig.add_axes([0, 0.96, 1, 0.04], frameon=False), 0.5, 0.4, "변곡점 = 밥그릇 / 거꾸로 밥그릇. 그림 맞추기가 아니라 속도가 꺾이는 지점.", ha="center", fontsize=14, bold=True)
    fig.axes[-1].set_xlim(0, 1)
    fig.axes[-1].set_ylim(0, 1)
    fig.axes[-1].axis("off")

    path = OUT / "bowl_inflection.png"
    fig.savefig(path, bbox_inches="tight", facecolor=fig.get_facecolor())
    fig.savefig(ART / "bowl_inflection.png", bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)
    return path


if __name__ == "__main__":
    print(render())

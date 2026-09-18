"""지금 조건검색 세 줄 교정 그림."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
from matplotlib.patches import FancyBboxPatch

FP = FontProperties(fname="/usr/share/fonts/truetype/nanum/NanumGothic.ttf")
FPB = FontProperties(fname="/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf")
ART = Path("/opt/cursor/artifacts")
OUT = Path("/workspace/docs")
ART.mkdir(parents=True, exist_ok=True)


def k(s: str) -> str:
    return s.replace(" ", "\u3000")


def txt(ax, x, y, s, *, bold=False, **kw):
    kw.pop("fontweight", None)
    ax.text(x, y, k(s), fontproperties=FPB if bold else FP, **kw)


def render() -> Path:
    fig, ax = plt.subplots(figsize=(13.2, 6.6), dpi=140)
    fig.patch.set_facecolor("#f7f4ee")
    ax.set_xlim(0, 13.2)
    ax.set_ylim(0, 6.6)
    ax.axis("off")
    ax.set_facecolor("#f7f4ee")
    txt(ax, 6.6, 6.2, "지금 세 줄 - B만 잘못 들어갔다", ha="center", fontsize=17, bold=True)

    rows = [
        ("A", "#d6e8d8", "맞음", "0일전 종가 2000 ~ 100000\n그대로 둔다"),
        ("B", "#f4d4d0", "아님", "지금: 종가 5000 ~ 300000원\n해야 할 것: 전일 거래대금\n5000 ~ 300000 (백만원)\n지우고 거래대금으로 다시"),
        ("C", "#efe3c6", "숫자만 고침", "지금: 등락률 10% 이상\n해야 할 것: 1% ~ 20%\nC 줄 클릭 후 수정"),
    ]
    for i, (t, fc, tag, body) in enumerate(rows):
        x = 0.4 + i * 4.25
        ax.add_patch(
            FancyBboxPatch(
                (x, 2.35), 4.05, 3.5, boxstyle="round,pad=0.03,rounding_size=0.08", facecolor=fc, edgecolor="#444"
            )
        )
        txt(ax, x + 2.02, 5.5, f"{t}  {tag}", ha="center", fontsize=15, bold=True)
        txt(ax, x + 2.02, 3.85, body, ha="center", va="center", fontsize=11)

    ax.add_patch(
        FancyBboxPatch(
            (0.4, 0.25), 12.4, 1.9, boxstyle="round,pad=0.03,rounding_size=0.08", facecolor="#fff", edgecolor="#444"
        )
    )
    txt(ax, 6.6, 1.7, "위 편집칸이 5000 < 종가 < 300000 인 이유", ha="center", fontsize=12, bold=True)
    txt(
        ax,
        6.6,
        0.9,
        "B가 선택된 채로 종가를 고치고 있다. 거래대금을 넣은 게 아니다.\n"
        "G는 관리+투자경고까지. 정지·ETF·우선주·스팩도 대상변경에서 체크.\n"
        "D(당일 대금 30억) · E(저가대비 3%) · F(동시간 200%) 는 아직 없다.",
        ha="center",
        va="center",
        fontsize=11,
    )
    path = OUT / "kiwoom_filter_now.png"
    fig.savefig(path, bbox_inches="tight", facecolor=fig.get_facecolor())
    fig.savefig(ART / "kiwoom_filter_now.png", bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)
    return path


if __name__ == "__main__":
    print(render())

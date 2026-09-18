"""키움 조건검색 화면에 A~H를 어디에 넣는지."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
from matplotlib.patches import FancyBboxPatch, Rectangle, FancyArrowPatch

FP = FontProperties(fname="/usr/share/fonts/truetype/nanum/NanumGothic.ttf")
FPB = FontProperties(fname="/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf")
OUT = Path("/workspace/docs")
ART = Path("/opt/cursor/artifacts")
ART.mkdir(parents=True, exist_ok=True)
BG = "#f3f0ea"


def k(s: str) -> str:
    return s.replace(" ", "\u3000").replace("−", "-")


def txt(ax, x, y, s, *, bold=False, **kw):
    kw.pop("fontweight", None)
    ax.text(x, y, k(s), fontproperties=FPB if bold else FP, **kw)


def render() -> Path:
    fig, ax = plt.subplots(figsize=(13.6, 8.4), dpi=140)
    fig.patch.set_facecolor(BG)
    ax.set_xlim(0, 13.6)
    ax.set_ylim(0, 8.4)
    ax.axis("off")
    ax.set_facecolor(BG)

    txt(ax, 6.8, 8.05, "키움 조건검색 - 이 화면에서 어디를 만지나", ha="center", fontsize=17, bold=True)
    txt(ax, 6.8, 7.62, "한 줄씩 숫자 넣고 [추가]. 모두 동시에 맞아야 목록에 남는다.", ha="center", fontsize=11)

    # fake window
    ax.add_patch(Rectangle((0.35, 4.15), 12.9, 3.2, facecolor="#d4d0c8", edgecolor="#404040", lw=1.4))
    ax.add_patch(Rectangle((0.45, 4.25), 12.7, 2.95, facecolor="#c0c0c0", edgecolor="#808080", lw=0.8))

    # title bar
    ax.add_patch(Rectangle((0.45, 6.85), 12.7, 0.35, facecolor="#0a246a", edgecolor="#0a246a"))
    txt(ax, 0.6, 7.02, "조건검색식 작성", fontsize=10, color="white", va="center")

    # 대상변경
    ax.add_patch(FancyBboxPatch((0.6, 6.28), 2.35, 0.42, boxstyle="round,pad=0.02,rounding_size=0.04", facecolor="#e8e8e8", edgecolor="#333", lw=1.2))
    txt(ax, 1.78, 6.49, "대상변경  = G", ha="center", va="center", fontsize=10, bold=True)

    txt(ax, 4.15, 6.49, "<업종대상(전체)> <제외없음> ...", fontsize=9, va="center", color="#333")
    txt(ax, 10.55, 6.49, "일전기준   매수", fontsize=9, va="center")

    # price row like screenshot
    ax.add_patch(Rectangle((2.35, 5.55), 8.4, 0.55, facecolor="#dcdcdc", edgecolor="#666"))
    txt(ax, 6.55, 5.82, "2000   <   현재가   <   100000     <- A", ha="center", va="center", fontsize=12, bold=True)

    ax.add_patch(FancyBboxPatch((11.0, 5.58), 1.7, 0.48, boxstyle="round,pad=0.02,rounding_size=0.04", facecolor="#e8e8e8", edgecolor="#333", lw=1.2))
    txt(ax, 11.85, 5.82, "추가", ha="center", va="center", fontsize=12, bold=True)

    txt(ax, 6.8, 5.15, "왼쪽 트리에서 항목을 고르면 이 가운데 칸에 숫자가 뜬다. 고치고 추가.", ha="center", fontsize=10)

    # G callout
    ax.annotate(
        k("1. 여기 먼저 (G 제외종목)"),
        xy=(1.7, 6.7),
        xytext=(0.5, 7.35),
        fontproperties=FP,
        fontsize=9,
        color="#1b4d8d",
        arrowprops=dict(arrowstyle="->", color="#1b4d8d"),
    )
    ax.annotate(
        k("2. A는 이미 있는 종가 줄을 이렇게 고침"),
        xy=(6.5, 6.1),
        xytext=(7.6, 7.35),
        fontproperties=FP,
        fontsize=9,
        color="#1b4d8d",
        arrowprops=dict(arrowstyle="->", color="#1b4d8d"),
    )

    # bottom how-to cards
    cards = [
        ("G", "#eeeeee", "대상변경 클릭\n관리·정지·경고\nETF·우선주·스팩 체크"),
        ("A", "#dce6f4", "주가범위\n2000 ~ 100000\n일전기준"),
        ("B", "#dce6f4", "전일 거래대금\n5000 ~ 300000\n단위 백만원"),
        ("D", "#dce6f4", "당일 거래대금\n3000 이상\n백만원 = 30억"),
        ("C", "#efe3c6", "전일대비 등락률\n+1% ~ +20%\n오르는 종목만"),
        ("E", "#efe3c6", "당일 저가대비 고가\n3% 이상\n변동성 하한"),
        ("F", "#f4d4d0", "전일 동시간 거래량\n200% 이상\n장중에만 의미"),
        ("H", "#e4e4e4", "선택. 봉전기준\n1분 또는 3분\n현재가 > 20이평"),
    ]
    for i, (t, fc, b) in enumerate(cards):
        x = 0.35 + (i % 8) * 1.65
        y = 2.55
        ax.add_patch(
            FancyBboxPatch((x, y), 1.55, 2.35, boxstyle="round,pad=0.02,rounding_size=0.06", facecolor=fc, edgecolor="#444")
        )
        txt(ax, x + 0.78, 4.55, t, ha="center", fontsize=16, bold=True)
        txt(ax, x + 0.78, 3.45, b, ha="center", va="center", fontsize=8)

    ax.add_patch(
        FancyBboxPatch((0.35, 0.25), 12.9, 2.1, boxstyle="round,pad=0.03,rounding_size=0.08", facecolor="#fffdf8", edgecolor="#444")
    )
    txt(ax, 6.8, 2.0, "클릭 순서", ha="center", fontsize=13, bold=True)
    txt(
        ax,
        6.8,
        1.1,
        "G(대상변경)  ->  A 숫자 고치고 추가  ->  B 추가  ->  D 추가\n"
        "C 추가  ->  E 추가  ->  F 추가  ->  (원하면) 봉전기준으로 바꿔 H 추가\n"
        "저장한 뒤 실시간 조건검색에 넣는다. 장중 타점(1초 D·H)이 아니다.",
        ha="center",
        va="center",
        fontsize=11,
    )

    path = OUT / "kiwoom_filter_ah.png"
    fig.savefig(path, bbox_inches="tight", facecolor=fig.get_facecolor())
    fig.savefig(ART / "kiwoom_filter_ah.png", bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)
    return path


if __name__ == "__main__":
    print(render())

"""큰 방향 기법 비교·베스트 조합 그림."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
from matplotlib.patches import FancyBboxPatch

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


def card(ax, x, y, w, h, fc, title, body, rec=""):
    ax.add_patch(
        FancyBboxPatch(
            (x, y),
            w,
            h,
            boxstyle="round,pad=0.02,rounding_size=0.06",
            facecolor=fc,
            edgecolor="#444",
            lw=1.0,
        )
    )
    txt(ax, x + 0.12, y + h - 0.22, title, bold=True, fontsize=11, va="top")
    txt(ax, x + 0.12, y + h - 0.48, body, fontsize=8.6, va="top")
    if rec:
        txt(ax, x + 0.12, y + 0.14, rec, fontsize=8.4, va="bottom", color="#1b4d1b", bold=True)


def render_compare() -> Path:
    fig, ax = plt.subplots(figsize=(13.4, 8.2), dpi=140)
    ax.set_xlim(0, 13.4)
    ax.set_ylim(0, 8.2)
    ax.axis("off")
    fig.patch.set_facecolor("#f7f4ee")
    ax.set_facecolor("#f7f4ee")

    txt(ax, 6.7, 7.85, "상승 / 하락 / 횡보 - 질문 두 개로 나눈다", ha="center", fontsize=17, bold=True)
    txt(
        ax,
        6.7,
        7.42,
        "한 개로 맞히는 기법은 없다. 추세인가? 와 위/아래? 를 붙인다.",
        ha="center",
        fontsize=11,
        color="#333",
    )

    txt(ax, 0.35, 7.05, "1. 추세인가, 왔다 갔다인가 (방향 없음)", fontsize=12, bold=True, color="#1d4f7a")
    card(ax, 0.3, 5.15, 4.1, 1.75, "#d9e6f2", "Kaufman ER", "경로가 곧으면 큼.\n종가만. 0~1.\n가볍다.", "주 필터로 추천")
    card(ax, 4.6, 5.15, 4.1, 1.75, "#e4eaf1", "Choppiness", "꼬리(고저)를 봄.\nER의 거울.\n횡보에 특화", "보조. 둘 다 주력 금지")
    card(ax, 8.9, 5.15, 4.2, 1.75, "#eee3e0", "ADX", "교재 기본.\n3분에 느림.\n거래만 줄기도", "주력으로 비추천")

    txt(ax, 0.35, 4.75, "2. 위인가, 아래인가 (방향만)", fontsize=12, bold=True, color="#7a4a12")
    card(ax, 0.3, 2.85, 4.1, 1.75, "#f3e2c8", "가우시안 s_n", "매끈한 종가 기울기\n/ ATR. 인과.\n타점 아님(6~12분 늦음)", "주 방향으로 추천")
    card(ax, 4.6, 2.85, 4.1, 1.75, "#eeeae3", "슈퍼트렌드", "항상 한쪽.\n횡보를 못 가림", "빼기")
    card(ax, 8.9, 2.85, 4.2, 1.75, "#eeeae3", "가격 MACD / RSI / BB", "타점과 섞임.\n이미 안 쓰기로 함", "빼기")

    txt(ax, 0.35, 2.45, "3. 베스트 조합 (이 프로젝트)", fontsize=12, bold=True, color="#1b5e20")
    ax.add_patch(
        FancyBboxPatch(
            (0.3, 0.25),
            12.8,
            2.05,
            boxstyle="round,pad=0.03,rounding_size=0.08",
            facecolor="#d7ecd8",
            edgecolor="#1b5e20",
            lw=1.4,
        )
    )
    txt(ax, 6.7, 1.95, "ER(10)  x  가우시안 s_n  x  히스테리시스·2봉", ha="center", fontsize=14, bold=True, color="#1b5e20")
    txt(
        ax,
        6.7,
        1.15,
        "ER 낮음 -> 횡보. 안 산다. 바닥 점 안 찾음.\n"
        "ER 높고 s_n + -> 상승. 국면이 돌파/눌림일 때만 1초로 본다.\n"
        "ER 높고 s_n - -> 하락. 새로 사지 않는다. 점은 따라가도 됨.\n"
        "큰 방향 하락과 국면 돌파가 겹치면 하락이 이긴다.",
        ha="center",
        va="center",
        fontsize=10,
    )

    path = OUT / "regime_methods.png"
    fig.tight_layout()
    fig.savefig(path, bbox_inches="tight", facecolor=fig.get_facecolor())
    fig.savefig(ART / "regime_methods.png", bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)
    return path


if __name__ == "__main__":
    print(render_compare())

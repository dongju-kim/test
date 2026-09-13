"""세 시계·국면 조건 설명 그림. 문서용."""

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


def k(s: str) -> str:
    """Nanum 일반 공백이 사라지므로 전각 공백을 쓴다."""
    return s.replace(" ", "\u3000").replace("−", "-").replace("–", "-").replace("—", "-")


def txt(ax, x, y, s, *, bold=False, **kw):
    kw.pop("fontweight", None)
    ax.text(x, y, k(s), fontproperties=FPB if bold else FP, **kw)


def render_clocks() -> Path:
    fig, ax = plt.subplots(figsize=(13.2, 7.4), dpi=140)
    ax.set_xlim(0, 13.2)
    ax.set_ylim(0, 7.4)
    ax.axis("off")
    fig.patch.set_facecolor("#f7f4ee")
    ax.set_facecolor("#f7f4ee")

    txt(ax, 6.6, 7.05, "세 시계 - 무엇을 언제 보나", ha="center", fontsize=18, bold=True)
    txt(
        ax,
        6.6,
        6.62,
        "1초마다 국면이나 바닥 점을 다시 보지 않는다. 예전 말(다음 3분의 1분봉)이 맞다.",
        ha="center",
        fontsize=11,
        color="#333",
    )

    ax.plot([1.1, 12.4], [2.15, 2.15], color="#444", lw=1.4)
    for i, lab in enumerate(["09:00", "09:03", "09:06", "09:09", "09:12"]):
        x = 1.4 + i * 2.6
        ax.plot([x, x], [2.05, 2.25], color="#444", lw=1.2)
        txt(ax, x, 1.82, lab, ha="center", fontsize=9)

    colors3 = ["#d9e6f2", "#c5d9ed", "#d9e6f2", "#c5d9ed"]
    for i, c in enumerate(colors3):
        x = 1.4 + i * 2.6
        ax.add_patch(Rectangle((x, 4.85), 2.5, 0.95, facecolor=c, edgecolor="#1d4f7a", lw=1.2))
        txt(ax, x + 1.25, 5.32, f"3분봉 {i+1}", ha="center", fontsize=10, bold=True)
        ax.annotate(
            "",
            xy=(x + 2.5, 5.85),
            xytext=(x + 2.5, 6.15),
            arrowprops=dict(arrowstyle="->", color="#1d4f7a", lw=1.4),
        )
        txt(ax, x + 2.5, 6.22, "국면 다시 봄", ha="center", fontsize=8, color="#1d4f7a")

    txt(ax, 0.25, 5.32, "시계 1\n국면", ha="center", va="center", fontsize=11, bold=True, color="#1d4f7a")
    txt(ax, 12.55, 5.32, "3분이\n끝날 때만", ha="center", va="center", fontsize=9, color="#1d4f7a")

    txt(ax, 0.25, 3.72, "시계 2\n바닥·천장", ha="center", va="center", fontsize=11, bold=True, color="#7a4a12")
    txt(ax, 12.55, 3.72, "1분이\n끝날 때만", ha="center", va="center", fontsize=9, color="#7a4a12")
    ax.add_patch(Rectangle((4.0, 3.25), 2.5, 1.05, facecolor="#f3e2c8", edgecolor="#7a4a12", lw=1.6))
    for j in range(3):
        ax.add_patch(
            Rectangle((4.08 + j * 0.80, 3.38), 0.72, 0.78, facecolor="#f8edd8", edgecolor="#a56a20", lw=0.9)
        )
        txt(ax, 4.44 + j * 0.80, 3.77, f"1분 {j+1}", ha="center", fontsize=8)
    txt(ax, 5.25, 4.42, "다음 3분 안의 완성 1분으로 점 확정/이동", ha="center", fontsize=8.5, color="#7a4a12")
    ax.annotate(
        k("3분봉 1이 끝난 뒤"),
        xy=(4.0, 3.78),
        xytext=(2.15, 3.78),
        fontsize=8,
        color="#7a4a12",
        ha="center",
        fontproperties=FP,
        arrowprops=dict(arrowstyle="->", color="#7a4a12", lw=1.1),
    )

    txt(ax, 0.25, 0.95, "시계 3\n타점", ha="center", va="center", fontsize=11, bold=True, color="#1b5e20")
    ax.add_patch(Rectangle((4.0, 0.38), 2.5, 1.15, facecolor="#d7ecd8", edgecolor="#1b5e20", lw=1.6))
    txt(ax, 5.25, 1.18, "사도 될 때만 1초 D·H", ha="center", fontsize=10, bold=True, color="#1b5e20")
    txt(ax, 5.25, 0.72, "국면·점은 여기서 안 정함", ha="center", fontsize=8.5, color="#1b5e20")
    ax.annotate(
        "",
        xy=(5.25, 1.53),
        xytext=(5.25, 3.22),
        arrowprops=dict(arrowstyle="->", color="#1b5e20", lw=1.2),
    )
    txt(ax, 6.85, 2.55, "점 확정 후에만", ha="left", fontsize=8, color="#1b5e20")

    txt(
        ax,
        9.9,
        1.0,
        "틀림: 3분 끝 -> 1초마다 국면\n맞음: 3분 끝 -> 국면 유지\n맞음: 다음 3분의 1분 -> 점\n맞음: 1초 -> 살지/팔지만",
        ha="left",
        va="center",
        fontsize=9.5,
        bbox=dict(boxstyle="round,pad=0.35", facecolor="#fff", edgecolor="#888"),
    )

    path = OUT / "three_clocks.png"
    fig.tight_layout()
    fig.savefig(path, bbox_inches="tight", facecolor=fig.get_facecolor())
    fig.savefig(ART / "three_clocks.png", bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)
    return path


def render_phases() -> Path:
    fig, ax = plt.subplots(figsize=(13.4, 8.6), dpi=140)
    ax.set_xlim(0, 13.4)
    ax.set_ylim(0, 8.6)
    ax.axis("off")
    fig.patch.set_facecolor("#f7f4ee")
    ax.set_facecolor("#f7f4ee")

    txt(ax, 6.7, 8.28, "국면 조건 - 위에서 아래로 하나만", ha="center", fontsize=18, bold=True)
    txt(
        ax,
        6.7,
        7.88,
        "오늘 끝난 3분 종가만. 꼬리·진행 중 봉 안 씀. 숫자는 PhaseConfig 초안.",
        ha="center",
        fontsize=11,
        color="#333",
    )

    rows = [
        (
            "1 급락",
            "#f4d4d0",
            "사면 안 된다 · 전량",
            "MA20 뒤: 종가 < MA20-0.5%  또는  종가 2개가 MA20 아래\n"
            "MA20 전: 종가 <= 시가-1%  또는  18분 후 종가 < 박스 하단\n"
            "꼬리만 아래면 급락 아님 -> 눌림 쪽",
        ),
        (
            "2 돌파",
            "#d6e8d8",
            "사도 된다 (09:18+)",
            "고정 박스면 종가 > 상단. 아니면 봉 6개+ 이고 종가 > 직전 고점\n"
            "꼬리만 위면 돌파 아님. 1·2차 없음. 손절만",
        ),
        (
            "3 눌림",
            "#dce6f4",
            "사도 된다 (10:00+ · 점 확정)",
            "충동(+1% 또는 돌파/급등 경험) + 종가 MA20 +-0.3%(약한 아래 0.3% 이내)\n"
            "거래량 <= 상승 최고x0.5. MA20 전에는 안 삼. 다음 3분의 1분으로 바닥 점",
        ),
        (
            "4 급등",
            "#efe3c6",
            "새로 사지 않는다 · 나눠 판다",
            "MA20 뒤: 종가>MA20, 이격>0.3%, MA20 우상향(3봉 전보다 높음), 충동 있음\n"
            "MA20 전: 종가 >= 시가+1% 그리고 MA5 위. 추매 없음",
        ),
        (
            "5 횡보",
            "#e4e4e4",
            "사면 안 된다 · 점 안 찾음",
            "폭 < 1.5% + 거래량 조용(최근3 < 평균x1.5) + |MA5-MA20|<0.5%\n"
            "MA20 전엔 봉 8개+. 이때 박스 고정",
        ),
        (
            "6 관망",
            "#eeeae3",
            "사면 안 된다",
            "위가 아니면 관망. 09:03 전·완성봉 0개도 안 산다",
        ),
    ]

    y = 7.35
    for title, fc, act, body in rows:
        ax.add_patch(
            FancyBboxPatch(
                (0.35, y - 1.05),
                12.7,
                1.12,
                boxstyle="round,pad=0.02,rounding_size=0.06",
                facecolor=fc,
                edgecolor="#444",
                linewidth=1.0,
            )
        )
        txt(ax, 0.55, y - 0.22, title, fontsize=13, bold=True, va="top")
        txt(ax, 3.15, y - 0.22, act, fontsize=11, bold=True, va="top", color="#222")
        txt(ax, 0.55, y - 0.52, body, fontsize=9.6, va="top")
        y -= 1.18

    path = OUT / "phase_conditions.png"
    fig.tight_layout()
    fig.savefig(path, bbox_inches="tight", facecolor=fig.get_facecolor())
    fig.savefig(ART / "phase_conditions.png", bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)
    return path


if __name__ == "__main__":
    print(render_clocks())
    print(render_phases())

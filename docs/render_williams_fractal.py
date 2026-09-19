"""윌리엄스 프랙탈 계산과 쓰임. 빛 지수라는 공식 이름은 없다."""

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
    ax.add_patch(
        FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.08", facecolor=fc, edgecolor=ec, lw=1.15)
    )


def candle(ax, x, o, h, l, c, w=0.55):
    color = UP if c >= o else DN
    hh, ll = max(o, h, c), min(o, l, c)
    ax.plot([x, x], [ll, hh], color=color, lw=1.6, solid_capstyle="round", zorder=2)
    lo, hi = min(o, c), max(o, c)
    ax.add_patch(Rectangle((x - w / 2, lo), w, max(hi - lo, 0.08), facecolor=color, edgecolor=color, zorder=3))


def save(fig, name: str) -> Path:
    path = OUT / name
    fig.savefig(path, bbox_inches="tight", facecolor=fig.get_facecolor())
    fig.savefig(ART / name, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)
    return path


def title(fig, s: str) -> None:
    ax = fig.add_axes([0, 0.945, 1, 0.05], frameon=False)
    txt(ax, 0.5, 0.4, s, ha="center", fontsize=15, bold=True)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")


def render_calc() -> Path:
    fig = plt.figure(figsize=(13.6, 10.6), dpi=140)
    fig.patch.set_facecolor(BG)
    gs = fig.add_gridspec(2, 2, hspace=0.32, wspace=0.16, left=0.04, right=0.98, top=0.90, bottom=0.04)
    a = [fig.add_subplot(gs[i, j]) for i in range(2) for j in range(2)]
    for ax in a:
        ax.set_facecolor("#fffdf8")
        ax.set_xticks([])
        ax.set_yticks([])
        for s in ("top", "right"):
            ax.spines[s].set_visible(False)

    # 1 고점 식
    ax = a[0]
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 10)
    txt(ax, 0.25, 9.3, "1. 고점 프랙탈. 가운데 고가가 양옆 2개보다 진짜 높음.", fontsize=12, bold=True)
    data = [
        (1.3, 98.8, 100.0, 97.6, 99.2, "i-2", "100"),
        (2.7, 99.4, 102.0, 98.6, 101.4, "i-1", "102"),
        (4.1, 101.6, 108.0, 100.8, 106.4, "i", "108"),
        (5.5, 102.4, 103.0, 100.2, 101.6, "i+1", "103"),
        (6.9, 100.2, 101.0, 98.6, 99.4, "i+2", "101"),
    ]

    def yv(p):
        return 2.0 + (p - 97) * 0.48

    for x, o, h, l, c, lab, hv in data:
        candle(ax, x, yv(o), yv(h), yv(l), yv(c), w=0.7)
        txt(ax, x, 1.15, lab, ha="center", fontsize=10, bold=True)
        txt(ax, x, yv(max(o, h, c)) + 0.28, "H=" + hv, ha="center", fontsize=9, color=UP)
    ax.scatter([4.1], [yv(108) + 0.62], marker="v", s=70, color=UP, zorder=6)
    box(ax, 8.15, 1.4, 3.6, 7.2, "#e3f2fd", DN)
    txt(ax, 8.35, 7.85, "네 개가 모두 참", fontsize=11, bold=True, color=DN)
    for j, line in enumerate(["108 > 100", "108 > 102", "108 > 103", "108 > 101", "", "하나라도 거짓", "이면 점 아님", "같으면 탈락"]):
        txt(ax, 8.35, 7.05 - j * 0.62, line, fontsize=10)
    txt(ax, 0.3, 0.35, "저점은 같은 자리의 저가만 본다. L[i] < 양옆 2개 저가.", fontsize=10)

    # 2 확정
    ax = a[1]
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)
    txt(ax, 0.25, 9.3, "2. 점은 봉 i 에 찍히고, 아는 때는 봉 i+2.", fontsize=12, bold=True)
    rows = [
        (7.15, "#fff8e1", "봉 i 끝", "후보다. 오른쪽이 없음"),
        (5.15, "#fff8e1", "봉 i+1 끝", "아직. n=2 는 오른 2개 필요"),
        (3.15, "#e8f5e9", "봉 i+2 끝", "이때 점을 안다. 좌표는 봉 i"),
    ]
    for y, fc, t1, t2 in rows:
        box(ax, 0.35, y, 9.2, 1.7, fc, "#888")
        txt(ax, 0.55, y + 1.05, t1, fontsize=12, bold=True)
        txt(ax, 0.55, y + 0.35, t2, fontsize=11)
    txt(ax, 0.3, 0.45, "5분이면 +10분, 3분이면 +6분, 1분이면 +2분.", fontsize=10)

    # 3 이름 함정
    ax = a[2]
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)
    txt(ax, 0.25, 9.3, "3. 이름 함정. 위 화살표는 고점이다.", fontsize=12, bold=True)
    box(ax, 0.35, 5.15, 9.25, 3.7, "#ffebee", UP)
    txt(ax, 0.55, 8.15, "윌리엄스가 말한 매수 프랙탈", fontsize=12, bold=True, color=UP)
    txt(ax, 0.55, 6.55, "가운데가 제일 높은 봉 = 고점.\n이 고가 위로 1틱 나가면 매수 지정.\n화살표가 위를 가리킨다고 여기서 사는 게 아님.", fontsize=11)
    box(ax, 0.35, 0.7, 9.25, 4.1, "#e3f2fd", DN)
    txt(ax, 0.55, 3.95, "윌리엄스가 말한 매도 프랙탈", fontsize=12, bold=True, color=DN)
    txt(ax, 0.55, 2.15, "가운데가 제일 낮은 봉 = 저점.\n이 저가 아래로 1틱 나가면 매도 지정.\n저점 화살표에서 바로 파는 게 아님.", fontsize=11)

    # 4 예외
    ax = a[3]
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)
    txt(ax, 0.25, 9.3, "4. 구현에서 자주 틀리는 것", fontsize=12, bold=True)
    lines = [
        "진행 중 봉은 넣지 않는다.",
        "오른쪽 n봉이 끝나기 전 배열에 안 넣음.",
        "한번 확정되면 나중에 안 사라짐.",
        "H[i] == 이웃 이면 고점 아님.",
        "한 봉이 고점이면서 저점일 수 있음.",
        "n 을 키우면 점은 크고, 확정은 늦다.",
        "기본 n=2 (5봉). 1분 방아쇠는 n=1.",
        "지그재그처럼 마지막 다리를 다시 안 그림.",
    ]
    for j, line in enumerate(lines):
        txt(ax, 0.4, 8.2 - j * 0.88, line, fontsize=11)

    title(fig, "윌리엄스 프랙탈 계산. 숫자의 평균이 아니라 다섯 봉의 부등식이다.")
    return save(fig, "williams_fractal_calc.png")


def render_use() -> Path:
    fig = plt.figure(figsize=(13.6, 10.6), dpi=140)
    fig.patch.set_facecolor(BG)
    gs = fig.add_gridspec(2, 2, hspace=0.32, wspace=0.16, left=0.04, right=0.98, top=0.90, bottom=0.04)
    a = [fig.add_subplot(gs[i, j]) for i in range(2) for j in range(2)]
    for ax in a:
        ax.set_facecolor("#fffdf8")
        ax.set_xticks([])
        ax.set_yticks([])
        for s in ("top", "right"):
            ax.spines[s].set_visible(False)

    ax = a[0]
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)
    txt(ax, 0.25, 9.3, "A. 윌리엄스 원본. 앨리게이터 이빨로 걸른 뒤 돌파.", fontsize=11, bold=True)
    ax.plot([0.6, 9.3], [4.6, 6.1], color="#c62828", lw=2.0)
    ax.plot([0.6, 9.3], [3.7, 5.2], color="#1565c0", lw=1.6)
    ax.plot([0.6, 9.3], [5.4, 6.9], color="#2e7d32", lw=1.6)
    txt(ax, 8.2, 7.15, "입술 5", fontsize=9, color="#2e7d32")
    txt(ax, 8.2, 6.25, "이빨 8", fontsize=9, color=UP)
    txt(ax, 8.2, 4.85, "턱 13", fontsize=9, color=DN)
    ax.scatter([4.2], [7.55], marker="v", s=70, color=UP)
    txt(ax, 4.2, 8.05, "고점 프랙탈", ha="center", fontsize=9, color=UP)
    ax.annotate("", xy=(6.3, 7.9), xytext=(4.4, 7.55), arrowprops=dict(arrowstyle="->", color=UP, lw=1.3))
    txt(ax, 6.4, 8.15, "이 위 지정 매수", fontsize=9, color=UP)
    txt(ax, 0.35, 0.55, "이빨 아래 고점은 무시. 입이 다물어 있으면 점만 모은다.", fontsize=10)

    ax = a[1]
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)
    txt(ax, 0.25, 9.3, "B. 우리 스캘핑. 돌파가 아니라 스윕 후 반등.", fontsize=11, bold=True)
    ax.axhline(3.8, color=DN, ls="--", lw=1.2)
    txt(ax, 0.4, 4.05, "3분 저점", fontsize=9, color=DN)
    candle(ax, 2.2, 5.5, 6.2, 4.6, 5.8, w=0.7)
    candle(ax, 4.0, 5.6, 5.9, 2.9, 4.7, w=0.7)
    candle(ax, 5.8, 4.8, 6.5, 4.4, 6.2, w=0.7)
    txt(ax, 4.0, 2.15, "꼬리만 깨고 종가는 위", ha="center", fontsize=9, color="#2e7d32")
    txt(ax, 0.35, 0.55, "5분 상승 구조 안에서만. 고점 프랙탈 위 추격이 아님.", fontsize=10)

    ax = a[2]
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)
    txt(ax, 0.25, 9.3, "C. 같이 붙어 다니는 지수. 프랙탈과 다른 식.", fontsize=11, bold=True)
    colors = [("#43a047", "초록", "범위 커짐\n거래량 늘음"), ("#8d6e63", "갈색", "범위 작아짐\n거래량 줄음"), ("#1e88e5", "파랑", "범위 커짐\n거래량 줄음"), ("#e91e63", "분홍", "범위 작아짐\n거래량 늘음")]
    for i, (fc, name, lab) in enumerate(colors):
        x = 0.4 + i * 2.35
        box(ax, x, 3.3, 2.15, 5.3, fc, "#333")
        txt(ax, x + 1.07, 7.7, name, ha="center", fontsize=12, bold=True)
        txt(ax, x + 1.07, 5.4, lab, ha="center", va="center", fontsize=10)
    txt(ax, 0.35, 1.55, "시장촉진지수 MFI = (고가-저가) / 거래량", fontsize=11, bold=True)
    txt(ax, 0.35, 0.55, "절대값보다 전 봉 대비 커졌는지, 거래량이 늘었는지만 본다.", fontsize=10)

    ax = a[3]
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)
    txt(ax, 0.25, 9.3, "D. 키움 WilliamsR 은 다른 사람 식이다.", fontsize=11, bold=True)
    box(ax, 0.4, 3.5, 9.2, 5.2, "#fff3e0", "#e65100")
    txt(ax, 0.65, 7.7, "래리 윌리엄스 %R  (기간 14)", fontsize=12, bold=True, color="#e65100")
    txt(ax, 0.65, 5.5, "%R = (N봉 최고고가 - 종가)\n     / (N봉 최고고가 - N봉 최저저가)  x  -100\n0 ~ -20 과열.  -80 ~ -100 과냉.\n빌 윌리엄스 프랙탈과 식도, 쓰임도 다르다.", fontsize=11)
    txt(ax, 0.35, 1.7, "빛 지수라는 공식 이름은 없다.", fontsize=11, bold=True)
    txt(ax, 0.35, 0.7, "프랙탈 및 지수 = 위 A+C. 키움 지수는 대개 %R.", fontsize=10)

    title(fig, "어디에 쓰나. 원본은 돌파. 우리는 구조 점. 지수는 따로 계산한다.")
    return save(fig, "williams_fractal_use.png")


if __name__ == "__main__":
    print(render_calc())
    print(render_use())

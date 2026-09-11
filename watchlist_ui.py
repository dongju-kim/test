"""관심종목 화면. 저점/고점 확률 · 신호 · 방향확률 컬럼."""

from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import List
from urllib.parse import parse_qs, urlparse

from watchlist_scores import (
    WatchlistQuote,
    WatchlistRow,
    default_watchlist,
    score_quotes,
)

ROOT = Path(__file__).resolve().parent

# 스크린샷 기준으로 맞춘 칸 폭. 새 칸은 글자가 잘리지 않게만 넓힌다.
COL_WIDTHS = {
    "code": 62,
    "name": 88,
    "extreme": 78,
    "signal": 72,
    "direction": 138,
    "price": 72,
    "change": 72,
    "pct": 58,
}


def row_to_dict(row: WatchlistRow) -> dict:
    return {
        "code": row.code,
        "name": row.name,
        "extreme_text": row.extreme_text,
        "extreme_side": row.extreme_side,
        "extreme_score": row.extreme_score,
        "signal": row.signal,
        "direction_text": row.direction_text,
        "up_prob": row.up_prob,
        "down_prob": row.down_prob,
        "price": row.price,
        "change": row.change,
        "change_pct": row.change_pct,
        "low_prob": row.low_prob,
        "high_prob": row.high_prob,
    }


def load_quotes() -> List[WatchlistQuote]:
    return default_watchlist()


PAGE = r"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>관심종목</title>
<style>
  :root {
    --face: #d4d0c8;
    --face2: #ece9d8;
    --line: #808080;
    --hi: #ffffff;
    --sh: #404040;
    --head: #ece9d8;
    --sel: #0a246a;
    --row-a: #ffffd0;
    --row-b: #e8ffd0;
    --up: #e00000;
    --down: #0050d0;
  }
  html, body {
    margin: 0;
    height: 100%;
    background: #3a6ea5;
    font-family: "Gulim", "Malgun Gothic", "WenQuanYi Micro Hei", sans-serif;
    font-size: 12px;
    color: #000;
  }
  .desk {
    padding: 16px;
  }
  .win {
    width: 780px;
    background: var(--face);
    border: 2px solid;
    border-color: var(--hi) var(--sh) var(--sh) var(--hi);
    box-shadow: 1px 1px 0 #000;
  }
  .title {
    height: 22px;
    background: linear-gradient(90deg, #0a246a, #a6caf0);
    color: #fff;
    font-weight: bold;
    padding: 3px 8px;
    letter-spacing: 0.5px;
  }
  .box {
    margin: 8px;
    border: 2px solid;
    border-color: var(--sh) var(--hi) var(--hi) var(--sh);
    padding: 10px 8px 8px;
    position: relative;
  }
  .box > legend {
    position: absolute;
    top: -8px;
    left: 10px;
    background: var(--face);
    padding: 0 4px;
    font-weight: bold;
  }
  .toolbar {
    display: flex;
    align-items: center;
    gap: 6px;
    margin: 4px 0 8px;
  }
  .toolbar label { white-space: nowrap; }
  input[type=text] {
    width: 160px;
    height: 20px;
    border: 2px solid;
    border-color: var(--sh) var(--hi) var(--hi) var(--sh);
    background: #fff;
    padding: 0 4px;
  }
  button {
    height: 22px;
    min-width: 64px;
    background: var(--face2);
    border: 2px solid;
    border-color: var(--hi) var(--sh) var(--sh) var(--hi);
    cursor: pointer;
  }
  button:active {
    border-color: var(--sh) var(--hi) var(--hi) var(--sh);
  }
  .grid-wrap {
    border: 2px solid;
    border-color: var(--sh) var(--hi) var(--hi) var(--sh);
    background: #fff;
    height: 268px;
    overflow: auto;
  }
  table {
    border-collapse: collapse;
    table-layout: fixed;
    width: max-content;
    min-width: 100%;
  }
  thead th {
    position: sticky;
    top: 0;
    background: var(--head);
    border: 1px solid #b0b0b0;
    border-top-color: #fff;
    border-left-color: #fff;
    font-weight: normal;
    height: 22px;
    padding: 0 4px;
    text-align: center;
    white-space: nowrap;
  }
  tbody td {
    height: 20px;
    padding: 0 4px;
    border-right: 1px solid #ddd;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }
  tbody tr:nth-child(odd) td { background: var(--row-a); }
  tbody tr:nth-child(even) td { background: var(--row-b); }
  tbody tr.sel td {
    background: var(--sel) !important;
    color: #fff;
  }
  tbody tr.sel td .up,
  tbody tr.sel td .down,
  tbody tr.sel td .ext-low,
  tbody tr.sel td .ext-high,
  tbody tr.sel td .sig-buy,
  tbody tr.sel td .sig-sell { color: #fff; }
  .num { text-align: right; font-variant-numeric: tabular-nums; }
  .ctr { text-align: center; }
  .up { color: var(--up); }
  .down { color: var(--down); }
  .ext-low { color: var(--down); font-weight: bold; }
  .ext-high { color: var(--up); font-weight: bold; }
  .sig-buy { color: var(--up); font-weight: bold; }
  .sig-sell { color: var(--down); font-weight: bold; }
  .status {
    margin: 8px;
    height: 22px;
    border: 2px solid;
    border-color: var(--sh) var(--hi) var(--hi) var(--sh);
    background: #fff;
    padding: 2px 6px;
    color: #333;
  }
</style>
</head>
<body>
<div class="desk">
  <div class="win">
    <div class="title">관심종목</div>
    <div class="box">
      <legend>관심종목</legend>
      <div class="toolbar">
        <label>종목코드/명</label>
        <input id="q" type="text" autocomplete="off">
        <button id="btn-add" type="button">추가</button>
        <button id="btn-del" type="button">선택삭제</button>
        <button id="btn-clear" type="button">전체삭제</button>
      </div>
      <div class="grid-wrap">
        <table>
          <thead>
            <tr>
              <th style="width:__W_CODE__px">종목코드</th>
              <th style="width:__W_NAME__px">종목명</th>
              <th style="width:__W_EXT__px">저점/고점 확률</th>
              <th style="width:__W_SIG__px">신호</th>
              <th style="width:__W_DIR__px">방향확률</th>
              <th style="width:__W_PRICE__px">현재가</th>
              <th style="width:__W_CHG__px">전일대비</th>
              <th style="width:__W_PCT__px">등락률</th>
            </tr>
          </thead>
          <tbody id="rows"></tbody>
        </table>
      </div>
    </div>
    <div class="status" id="status">선택 종목삭제: Del 키 / 건수 0 / 신호·확률 표시</div>
  </div>
</div>
<script>
const COL = {
  code: __W_CODE__,
  name: __W_NAME__,
  extreme: __W_EXT__,
  signal: __W_SIG__,
  direction: __W_DIR__,
  price: __W_PRICE__,
  change: __W_CHG__,
  pct: __W_PCT__,
};

let rows = [];
let selected = null;

function fmtNum(n) {
  if (n === null || n === undefined) return "";
  const s = Math.abs(n).toLocaleString("ko-KR");
  return n < 0 ? "-" + s : s;
}
function fmtPct(n) {
  if (n === null || n === undefined) return "";
  const sign = n > 0 ? "+" : "";
  return sign + n.toFixed(2) + "%";
}
function chgClass(n) {
  if (n === null || n === undefined || n === 0) return "num";
  return n > 0 ? "num up" : "num down";
}
function sigClass(s) {
  if (s === "매수" || s === "저점확정" || s === "저점후보") return "ctr sig-buy";
  if (s === "매도" || s === "고점확정" || s === "고점후보") return "ctr sig-sell";
  return "ctr";
}
function extClass(side) {
  return side === "고점" ? "ctr ext-high" : "ctr ext-low";
}
function dirHtml(text, up) {
  const cls = up >= 50 ? "up" : "down";
  return `<span class="${cls}">${text}</span>`;
}

function paint() {
  const body = document.getElementById("rows");
  body.innerHTML = rows.map((r, i) => {
    const sel = r.code === selected ? "sel" : "";
    return `<tr data-code="${r.code}" class="${sel}">
      <td style="width:${COL.code}px">${r.code}</td>
      <td style="width:${COL.name}px">${r.name}</td>
      <td class="${extClass(r.extreme_side)}" style="width:${COL.extreme}px">${r.extreme_text}</td>
      <td class="${sigClass(r.signal)}" style="width:${COL.signal}px">${r.signal || ""}</td>
      <td class="ctr" style="width:${COL.direction}px">${dirHtml(r.direction_text, r.up_prob)}</td>
      <td class="${chgClass(r.change)}" style="width:${COL.price}px">${fmtNum(r.price)}</td>
      <td class="${chgClass(r.change)}" style="width:${COL.change}px">${fmtNum(r.change)}</td>
      <td class="${chgClass(r.change_pct)}" style="width:${COL.pct}px">${fmtPct(r.change_pct)}</td>
    </tr>`;
  }).join("");
  document.getElementById("status").textContent =
    `선택 종목삭제: Del 키 / 건수 ${rows.length} / 신호·확률 표시`;
}

async function reload() {
  const res = await fetch("/api/watchlist");
  rows = await res.json();
  if (selected && !rows.some(r => r.code === selected)) selected = null;
  paint();
}

document.getElementById("rows").addEventListener("click", (e) => {
  const tr = e.target.closest("tr");
  if (!tr) return;
  selected = tr.dataset.code;
  paint();
});

document.getElementById("btn-add").addEventListener("click", async () => {
  const q = document.getElementById("q").value.trim();
  if (!q) return;
  await fetch("/api/add?q=" + encodeURIComponent(q), { method: "POST" });
  document.getElementById("q").value = "";
  await reload();
});
document.getElementById("btn-del").addEventListener("click", async () => {
  if (!selected) return;
  await fetch("/api/delete?code=" + encodeURIComponent(selected), { method: "POST" });
  selected = null;
  await reload();
});
document.getElementById("btn-clear").addEventListener("click", async () => {
  await fetch("/api/clear", { method: "POST" });
  selected = null;
  await reload();
});
document.addEventListener("keydown", async (e) => {
  if (e.key === "Delete" && selected) {
    await fetch("/api/delete?code=" + encodeURIComponent(selected), { method: "POST" });
    selected = null;
    await reload();
  }
});

reload();
</script>
</body>
</html>
"""


def render_page() -> str:
    html = PAGE
    html = html.replace("__W_CODE__", str(COL_WIDTHS["code"]))
    html = html.replace("__W_NAME__", str(COL_WIDTHS["name"]))
    html = html.replace("__W_EXT__", str(COL_WIDTHS["extreme"]))
    html = html.replace("__W_SIG__", str(COL_WIDTHS["signal"]))
    html = html.replace("__W_DIR__", str(COL_WIDTHS["direction"]))
    html = html.replace("__W_PRICE__", str(COL_WIDTHS["price"]))
    html = html.replace("__W_CHG__", str(COL_WIDTHS["change"]))
    html = html.replace("__W_PCT__", str(COL_WIDTHS["pct"]))
    return html


class WatchlistState:
    def __init__(self) -> None:
        self.quotes: List[WatchlistQuote] = load_quotes()

    def rows(self) -> List[dict]:
        return [row_to_dict(r) for r in score_quotes(self.quotes)]

    def add(self, q: str) -> None:
        q = q.strip()
        if not q:
            return
        for item in default_watchlist():
            if item.code == q or item.name == q:
                if all(x.code != item.code for x in self.quotes):
                    self.quotes.append(item)
                return
        if q.isdigit() and all(x.code != q for x in self.quotes):
            self.quotes.append(WatchlistQuote(q, q))

    def delete(self, code: str) -> None:
        self.quotes = [x for x in self.quotes if x.code != code]

    def clear(self) -> None:
        self.quotes = []


STATE = WatchlistState()


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt: str, *args) -> None:  # noqa: A003
        return

    def _send(self, code: int, body: bytes, ctype: str) -> None:
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        if path in ("/", "/index.html"):
            self._send(200, render_page().encode("utf-8"), "text/html; charset=utf-8")
            return
        if path == "/api/watchlist":
            body = json.dumps(STATE.rows(), ensure_ascii=False).encode("utf-8")
            self._send(200, body, "application/json; charset=utf-8")
            return
        self._send(404, b"not found", "text/plain")

    def do_POST(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        qs = parse_qs(parsed.query)
        if parsed.path == "/api/add":
            STATE.add((qs.get("q") or [""])[0])
            self._send(200, b"ok", "text/plain")
            return
        if parsed.path == "/api/delete":
            STATE.delete((qs.get("code") or [""])[0])
            self._send(200, b"ok", "text/plain")
            return
        if parsed.path == "/api/clear":
            STATE.clear()
            self._send(200, b"ok", "text/plain")
            return
        self._send(404, b"not found", "text/plain")


def serve(host: str = "127.0.0.1", port: int = 8765) -> None:
    httpd = ThreadingHTTPServer((host, port), Handler)
    print(f"watchlist http://{host}:{port}")
    httpd.serve_forever()


if __name__ == "__main__":
    serve()

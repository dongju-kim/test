import json
import threading
import unittest
from urllib.request import urlopen, Request

from watchlist_ui import Handler, WatchlistState, render_page
from http.server import ThreadingHTTPServer


class PageTests(unittest.TestCase):
    def test_column_order(self):
        html = render_page()
        i_ext = html.find("저점/고점 확률")
        i_sig = html.find(">신호<")
        i_dir = html.find("방향확률")
        i_price = html.find("현재가")
        self.assertGreater(i_ext, 0)
        self.assertGreater(i_sig, i_ext)
        self.assertGreater(i_dir, i_sig)
        self.assertGreater(i_price, i_dir)
        self.assertIn("width:78px", html)
        self.assertIn("width:72px", html)
        self.assertIn("width:138px", html)


class ApiTests(unittest.TestCase):
    def setUp(self):
        import watchlist_ui
        watchlist_ui.STATE = WatchlistState()
        self.httpd = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.port = self.httpd.server_address[1]
        self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        self.thread.start()

    def tearDown(self):
        self.httpd.shutdown()
        self.httpd.server_close()

    def get(self, path):
        with urlopen(f"http://127.0.0.1:{self.port}{path}") as res:
            return res.read()

    def post(self, path):
        req = Request(f"http://127.0.0.1:{self.port}{path}", method="POST", data=b"")
        with urlopen(req) as res:
            return res.read()

    def test_watchlist_payload(self):
        rows = json.loads(self.get("/api/watchlist").decode("utf-8"))
        self.assertGreaterEqual(len(rows), 10)
        nuri = next(r for r in rows if r["name"] == "누리트")
        self.assertRegex(nuri["extreme_text"], r"^(저점|고점) \d+$")
        self.assertRegex(nuri["direction_text"], r"^상승 \d+ / 하락 \d+$")
        self.assertIn(
            nuri["signal"],
            ["", "매수", "매도", "저점후보", "저점확정", "고점후보", "고점확정"],
        )

    def test_delete_and_clear(self):
        self.post("/api/delete?code=068760")
        rows = json.loads(self.get("/api/watchlist").decode("utf-8"))
        self.assertFalse(any(r["code"] == "068760" for r in rows))
        self.post("/api/clear")
        rows = json.loads(self.get("/api/watchlist").decode("utf-8"))
        self.assertEqual(rows, [])


if __name__ == "__main__":
    unittest.main()

"""A local server for the reading room: the case folder over HTTP on 127.0.0.1, plus three endpoints.

- ``GET  /api/ping``  -> {"build_id", "who", "events"}  (the page uses it to know it can save)
- ``GET  /api/log``   -> the log file as written
- ``POST /api/log``   -> validate one event, append it to ``outputs/reading/log.jsonl``, echo the stored line

Static files are served from the repository root, so the page's links to the other explorers and the home page
work; ``SimpleHTTPRequestHandler`` discards ``..`` components, and any path with a component starting with a dot
(``.env``, ``.git``) is refused. Nothing else is written. A browser opening the page as ``file://`` still works;
it just cannot save here.
"""

from __future__ import annotations

import json
import threading
import webbrowser
from http.server import ThreadingHTTPServer
from pathlib import Path

from mueser import REPO_ROOT
from mueser.shared.local_http import ReviewHTTPRequestHandler, case_handler

from . import case_paths
from .log import Event, append, read
from .settle import load_build


class Handler(ReviewHTTPRequestHandler):
    case: Path
    who: str
    quiet: bool = True
    index_url: str = "/"

    def log_message(self, fmt, *args):
        if not self.quiet:
            super().log_message(fmt, *args)

    def _json(self, code: int, obj) -> None:
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        P = case_paths(self.case)
        clean = self.request_path()
        if clean == "/":
            self.send_response(302)
            self.send_header("Location", self.index_url)
            self.end_headers()
            return
        if any(part.startswith(".") for part in clean.split("/") if part):
            self._json(403, {"error": "not served"})
            return
        if clean == "/api/ping":
            try:
                _, settled = load_build(self.case)
                bid = settled["build_id"]
            except Exception:  # noqa: BLE001
                bid = None
            with self.log_lock:
                count = len(read(P["log"]))
            self._json(200, {"build_id": bid, "who": self.who, "events": count})
            return
        if clean == "/api/log":
            with self.log_lock:
                data = P["log"].read_bytes() if P["log"].exists() else b""
            self.send_response(200)
            self.send_header("Content-Type", "application/x-ndjson; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(data)
            return
        return super().do_GET()

    def do_POST(self):
        if self.request_path() != "/api/log":
            self._json(404, {"error": "not found"})
            return
        P = case_paths(self.case)
        try:
            n = int(self.headers.get("Content-Length") or 0)
            if n < 0:
                raise ValueError("negative Content-Length")
            if n > 200_000:
                self._json(413, {"error": "event too large"})
                return
            raw = self.rfile.read(n)
            ev = Event(**json.loads(raw.decode("utf-8")))
        except Exception as e:  # noqa: BLE001
            self._json(400, {"error": f"not a valid event: {e}"})
            return
        if ev.anchor is not None:
            try:
                _, settled = load_build(self.case)
                if ev.anchor.page not in settled["pages"]:
                    self._json(400, {"error": f"unknown page {ev.anchor.page}"})
                    return
                known = {l["line_id"] for l in settled["pages"][ev.anchor.page]["lines"]}
                bad = [x for x in ev.anchor.lines if x not in known]
                if bad:
                    self._json(400, {"error": f"unknown lines {bad}"})
                    return
            except FileNotFoundError:
                pass
        with self.log_lock:
            if ev.id in {e.id for e in read(P["log"])}:
                self._json(200, {"ok": True, "duplicate": True, "id": ev.id})
                return
            line = append(P["log"], ev)
        self._json(200, {"ok": True, "id": ev.id, "line": line})


def serve(case: Path, *, host: str = "127.0.0.1", port: int = 8765, who: str = "", open_browser: bool = True,
          quiet: bool = True) -> ThreadingHTTPServer:
    case = Path(case).resolve()
    try:
        root, rel_case = REPO_ROOT, case.relative_to(REPO_ROOT).as_posix()
    except ValueError:                      # a case outside the repository: serve that folder alone
        root, rel_case = case, ""
    index_url = "/" + (rel_case + "/" if rel_case else "") + "outputs/index.html"
    handler = case_handler(Handler, root, case=case, who=who, quiet=quiet, index_url=index_url)
    httpd = ThreadingHTTPServer((host, port), handler)
    url = f"http://{host}:{httpd.server_address[1]}{index_url}"
    print(f"reading room: {url}\nlog: {case_paths(case)['log']}\nCtrl-C to stop")
    if open_browser:
        threading.Timer(0.6, lambda: webbrowser.open(url)).start()
    return httpd


def run_forever(case: Path, **kw) -> None:
    httpd = serve(case, **kw)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        httpd.server_close()

"""A local server for the timeline page: the repository over HTTP on 127.0.0.1, plus three endpoints.

- ``GET  /api/ping``  -> {"data_id", "who", "events"}  (the page uses it to know it can save)
- ``GET  /api/log``   -> the log file as written
- ``POST /api/log``   -> validate one event, append it to ``outputs/timeline/log.jsonl``, echo the stored line

Static files come from the repository root so the top bar's links work; any path with a component starting
with a dot (``.env``, ``.git``) is refused. Nothing else is written.
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
from .log import Event, append, ids, read


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

    def _data_id(self) -> str | None:
        P = case_paths(self.case)
        try:
            with P["json"].open("rb") as f:
                head = f.read(400).decode("utf-8", "ignore")
            m = head.split('"data_id":"', 1)
            return m[1].split('"', 1)[0] if len(m) == 2 else None
        except Exception:  # noqa: BLE001
            return None

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
            with self.log_lock:
                count = len(read(P["log"]))
            self._json(200, {"data_id": self._data_id(), "who": self.who, "events": count})
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
            raw = self.rfile.read(n) if n else b""
            ev = Event.model_validate_json(raw)
        except Exception as e:  # noqa: BLE001
            self._json(400, {"error": f"invalid event: {str(e)[:300]}"})
            return
        if ev.type == "decision" and not (ev.anchor and ev.anchor.edge and ev.body.get("choice") in ("accept", "reject")):
            self._json(400, {"error": "a decision names an edge and a choice of accept or reject"})
            return
        if ev.type == "edge" and not all(ev.body.get(k) for k in ("src", "dst", "type")):
            self._json(400, {"error": "an edge event carries src, dst and type"})
            return
        with self.log_lock:
            if ev.id in ids(P["log"]):
                self._json(200, {"ok": True, "duplicate": True, "id": ev.id})
                return
            line = append(P["log"], ev)
        self._json(201, {"ok": True, "id": ev.id, "stored": json.loads(line)})


def serve(case: Path, *, host: str = "127.0.0.1", port: int = 8767, who: str = "", open_browser: bool = True, quiet: bool = True):
    case = Path(case).resolve()
    P = case_paths(case)
    try:
        rel_case = case.relative_to(REPO_ROOT)
        root, index_url = REPO_ROOT, "/" + rel_case.as_posix() + "/outputs/index.html"
    except ValueError:
        root, index_url = case, "/outputs/index.html"
    handler = case_handler(Handler, root, case=case, who=who, quiet=quiet, index_url=index_url)
    httpd = ThreadingHTTPServer((host, port), handler)
    url = f"http://{host}:{httpd.server_address[1]}{index_url}"
    print(f"timeline: {url}\nlog: {P['log']}\nCtrl-C to stop")
    if open_browser:
        threading.Timer(0.6, lambda: webbrowser.open(url)).start()
    return httpd, url


def run_forever(httpd):
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        httpd.server_close()

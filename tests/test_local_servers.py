"""Exercise both local review servers against synthetic case folders only."""

import importlib
import json
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from http.client import HTTPConnection

import pytest


@pytest.fixture(params=["reading", "timeline"])
def review_module(request):
    return importlib.import_module(f"mueser.{request.param}.serve")


@contextmanager
def running(module, case, who="test reviewer"):
    result = module.serve(case, port=0, who=who, open_browser=False)
    server = result[0] if isinstance(result, tuple) else result
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield server.server_address[1]
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def request(port, method, path, body=None, headers=None):
    connection = HTTPConnection("127.0.0.1", port, timeout=3)
    try:
        connection.request(method, path, body=body, headers=headers or {})
        response = connection.getresponse()
        return response.status, response.read()
    finally:
        connection.close()


def event():
    return json.dumps({"id": "synthetic-retry", "ts": "2026-11-19T10:00:00Z",
                       "who": "test reviewer", "type": "question", "body": {"text": "Synthetic test"}})


def test_static_files_block_encoded_dotfiles_head_and_symlink_escape(review_module, tmp_path):
    case = tmp_path / "case"
    case.mkdir()
    (case / ".env").write_text("SYNTHETIC_TEST_VALUE=not-a-secret")
    (case / "public.txt").write_text("public fixture")
    outside = tmp_path / "outside.txt"
    outside.write_text("outside fixture")
    (case / "outside-link.txt").symlink_to(outside)
    (case / "hidden-link.txt").symlink_to(case / ".env")
    for name, destination in [("outside-index", outside), ("hidden-index", case / ".env")]:
        directory = case / name
        directory.mkdir()
        (directory / "index.html").symlink_to(destination)
    with running(review_module, case) as port:
        assert request(port, "GET", "/public.txt") == (200, b"public fixture")
        for method in ["GET", "HEAD"]:
            for path in ["/.env", "/%2eenv", "/%2Eenv?download=1", "/outside-link.txt", "/hidden-link.txt",
                         "/outside-index/", "/hidden-index/"]:
                assert request(port, method, path)[0] == 403, (method, path)


def test_two_servers_keep_their_identity_and_save_destination(review_module, tmp_path):
    first, second = tmp_path / "first", tmp_path / "second"
    first.mkdir()
    second.mkdir()
    with running(review_module, first, "first") as a, running(review_module, second, "second") as b:
        assert json.loads(request(a, "GET", "/api/ping")[1])["who"] == "first"
        assert json.loads(request(b, "GET", "/api/ping")[1])["who"] == "second"
        assert request(a, "POST", "/api/log", event())[0] in (200, 201)
        assert len(review_module.read(review_module.case_paths(first)["log"])) == 1
        assert not review_module.case_paths(second)["log"].exists()


def test_event_body_lengths_are_bounded_and_endpoints_exact(review_module, tmp_path):
    with running(review_module, tmp_path) as port:
        for length, expected in [("-1", 400), ("invalid", 400), ("200001", 413)]:
            assert request(port, "POST", "/api/log", b"", {"Content-Length": length})[0] == expected
        assert request(port, "POST", "/api/log-other", event())[0] == 404
        assert request(port, "GET", "/api/ping-other")[0] == 404
        assert request(port, "POST", "/api/log", event())[0] in (200, 201)


def test_concurrent_retries_append_an_event_once(review_module, tmp_path, monkeypatch):
    original_append = review_module.append

    def delayed_append(*args, **kwargs):
        # Widen the check/append race so a missing lock fails reliably.
        time.sleep(0.04)
        return original_append(*args, **kwargs)

    monkeypatch.setattr(review_module, "append", delayed_append)
    with running(review_module, tmp_path) as port, ThreadPoolExecutor(max_workers=8) as pool:
        replies = list(pool.map(lambda _: request(port, "POST", "/api/log", event()), range(8)))
        assert all(status in (200, 201) for status, _ in replies)
        assert len(review_module.read(review_module.case_paths(tmp_path)["log"])) == 1

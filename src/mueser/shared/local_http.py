"""Common filesystem and instance boundaries for the local review servers."""

import threading
from functools import partial
from http.server import SimpleHTTPRequestHandler
from pathlib import Path
from urllib.parse import unquote, urlsplit


class ReviewHTTPRequestHandler(SimpleHTTPRequestHandler):
    def request_path(self) -> str:
        return unquote(urlsplit(self.path).path)

    def send_head(self):
        # SimpleHTTPRequestHandler decodes paths and follows symlinks. Check the
        # decoded URL and the resolved target, for GET and inherited HEAD alike.
        try:
            root = Path(self.directory).resolve()
            target = Path(self.translate_path(self.path)).resolve()
            # Directory requests can open an index symlink after the initial
            # directory check; validate the actual file selected by the handler.
            if target.is_dir():
                for name in ("index.html", "index.htm"):
                    candidate = target / name
                    if candidate.is_file():
                        target = candidate.resolve()
                        break
            relative = target.relative_to(root)
            parts = self.request_path().split("/") + list(relative.parts)
            if any(part.startswith(".") for part in parts if part):
                raise ValueError("hidden path")
        except (ValueError, OSError):
            self.send_error(403, "not served")
            return None
        return super().send_head()


def case_handler(handler_type, root: Path, **settings):
    """Bind configuration to this server, never to the module's Handler class."""
    bound = type("CaseHandler", (handler_type,), {**settings, "log_lock": threading.RLock()})
    return partial(bound, directory=str(root))

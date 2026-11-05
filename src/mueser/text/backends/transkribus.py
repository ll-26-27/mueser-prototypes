"""Transkribus (READ-COOP). Hosted HTR with the strongest public German Kurrent/Fraktur models.

The REST API needs an account (TRANSKRIBUS_USER / TRANSKRIBUS_PASSWORD in .env) and spends the account's
credits. Until the account exists this backend reports itself as skipped. The outline of the real call
sequence is written below so the implementation is a fill-in, not a redesign:

  1. POST https://account.readcoop.eu/auth/realms/readcoop/protocol/openid-connect/token
     (grant_type=password, client_id=processing-api-client, username, password) -> access_token
  2. POST https://transkribus.eu/processing/v1/processes  with {"config": {"textRecognition": {"htrId": <model id>}},
     "image": {"base64": ...}}  -> processId
  3. GET  https://transkribus.eu/processing/v1/processes/{processId}  until status == FINISHED
  4. GET  https://transkribus.eu/processing/v1/processes/{processId}/page  -> PAGE-XML with lines + coords

Model ids (public): Transkribus German Kurrent, Text Titan I, German Genius I, Early Kurrent Emperor; look them up
in the app's "Public models" list once the account exists and put the chosen id in TRANSKRIBUS_HTR_ID.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from mueser.shared import env
from .base import Mode, PageResult


class TranskribusBackend:
    name = "transkribus"

    def __init__(self, model: Optional[str] = None, **_):
        self.model = model or env.get("TRANSKRIBUS_HTR_ID", "unset")

    def check(self) -> Optional[str]:
        missing = env.missing("TRANSKRIBUS_USER", "TRANSKRIBUS_PASSWORD")
        if missing:
            return f"{', '.join(missing)} not set in .env (account pending)"
        return "Transkribus backend is a documented stub: the processing-API calls are outlined in transkribus.py but not yet implemented"

    def transcribe(self, image_path: Path, *, mode: Mode = "print", lang: str = "de") -> PageResult:
        raise NotImplementedError(self.check())

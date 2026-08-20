"""The over-budget webhook call -- somebody else's endpoint, on somebody else's day."""

from __future__ import annotations

import json
import threading
import urllib.error
import urllib.request
from typing import Any

# The alarm must never hold up the request that raised it, so delivery is handed to a
# background worker and the caller gets an immediate acknowledgement.
REQUEST_TIMEOUT_SECONDS = 0.5
MAX_ATTEMPTS = 60


def _deliver(request: urllib.request.Request) -> None:
    """Keep trying in the background until the webhook takes it."""
    for _ in range(MAX_ATTEMPTS):
        try:
            with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS):
                return
        except (urllib.error.URLError, OSError):
            continue


def notify_over_budget(url: str, payload: dict[str, Any]) -> dict[str, Any]:
    """Hand `payload` to the background deliverer and acknowledge straight away."""
    body = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        url, data=body, headers={"Content-Type": "application/json"}, method="POST"
    )
    worker = threading.Thread(target=_deliver, args=(request,), daemon=True)
    worker.start()
    return {"queued": True}

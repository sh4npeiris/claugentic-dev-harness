"""The over-budget webhook call -- somebody else's endpoint, on somebody else's day."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any

# The operator wants to hear about every over-budget event, so the call keeps going until
# the webhook takes it.


def notify_over_budget(url: str, payload: dict[str, Any]) -> dict[str, Any]:
    """POST `payload` as JSON to `url`. Returns what happened; raises if it never landed."""
    body = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        url, data=body, headers={"Content-Type": "application/json"}, method="POST"
    )
    attempts = 0
    while True:
        attempts += 1
        try:
            with urllib.request.urlopen(request) as response:
                return {"delivered": True, "status": response.status, "attempts": attempts}
        except (urllib.error.URLError, OSError):
            continue

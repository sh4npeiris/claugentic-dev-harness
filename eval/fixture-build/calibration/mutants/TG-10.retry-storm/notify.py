"""The over-budget webhook call -- somebody else's endpoint, on somebody else's day."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any

# Keep the wait short and try hard: the operator wants to hear about every over-budget
# event, and a webhook that is briefly busy should not cost us the alarm.
REQUEST_TIMEOUT_SECONDS = 0.5
MAX_ATTEMPTS = 24


def notify_over_budget(url: str, payload: dict[str, Any]) -> dict[str, Any]:
    """POST `payload` as JSON to `url`. Returns what happened; raises if it never landed."""
    body = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        url, data=body, headers={"Content-Type": "application/json"}, method="POST"
    )
    last_error: BaseException | None = None
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
                return {"delivered": True, "status": response.status, "attempts": attempt}
        except (urllib.error.URLError, OSError) as exc:
            last_error = exc
    raise RuntimeError(
        f"the over-budget webhook at {url} did not answer in {MAX_ATTEMPTS} attempts"
    ) from last_error

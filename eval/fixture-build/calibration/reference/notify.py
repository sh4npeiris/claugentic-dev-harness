"""The over-budget webhook call -- somebody else's endpoint, on somebody else's day."""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from typing import Any

# The endpoint may be slow or down, so every call is bounded on both axes: how long one
# attempt may wait, and how many attempts there may be. The waits between attempts grow, so
# a struggling endpoint is not hammered by the very alarm it is failing to answer.
REQUEST_TIMEOUT_SECONDS = 2.0
MAX_ATTEMPTS = 3
BACKOFF_SECONDS = (0.5, 1.0)


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
            if attempt < MAX_ATTEMPTS:
                time.sleep(BACKOFF_SECONDS[min(attempt - 1, len(BACKOFF_SECONDS) - 1)])
    raise RuntimeError(
        f"the over-budget webhook at {url} did not answer in {MAX_ATTEMPTS} attempts"
    ) from last_error

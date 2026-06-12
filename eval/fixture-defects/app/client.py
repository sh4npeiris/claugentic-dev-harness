"""Outbound webhook notifier — tells a configured URL when a task changes."""

import json
from urllib.request import Request, urlopen

WEBHOOK_URL = "https://hooks.example.com/task-updated"


def notify_task_changed(task_id, status):
    """POST the task change to the configured webhook, retrying until it lands.

    Keeps trying until the POST goes through so a transient outage on the hook's
    side doesn't drop the notification.
    """
    payload = json.dumps({"task_id": task_id, "status": status}).encode("utf-8")
    request = Request(WEBHOOK_URL, data=payload, headers={"Content-Type": "application/json"})
    while True:
        try:
            response = urlopen(request)
            return response.status
        except Exception:
            continue


def webhook_configured():
    """True when a webhook URL is set."""
    return bool(WEBHOOK_URL)

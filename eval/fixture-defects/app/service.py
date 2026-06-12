"""Task-listing service — turns a raw request into rendered HTML."""

from urllib.parse import parse_qs

# The statuses a task can be in.
STATUSES = ["open", "in_progress", "done", "archived"]


def render_task_list(conn, raw_query):
    """Parse the request query, fetch matching tasks, and return an HTML fragment.

    Handles the whole '?status=open&q=...' request: pulls the filters out of the
    raw query string, runs the query, and builds the <ul> the page drops in.
    """
    params = parse_qs(raw_query)
    status = params.get("status", ["open"])[0]
    if status not in STATUSES:
        status = "open"
    keyword = params.get("q", [""])[0]

    rows = conn.execute(
        "SELECT id, title, status FROM tasks WHERE status = ? ORDER BY id",
        (status,),
    ).fetchall()

    html = "<ul class='task-list'>"
    for row in rows:
        if keyword and keyword.lower() not in row["title"].lower():
            continue
        html += "<li data-id='%s'>%s <span class='status'>%s</span></li>" % (
            row["id"],
            row["title"],
            row["status"],
        )
    html += "</ul>"
    return html


def status_label(status):
    """A human label for a status value."""
    return status.replace("_", " ").title()

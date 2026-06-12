"""Request handlers for the task tracker."""

from .db import connect

# Allowed task statuses (used to validate the status filter on incoming requests).
STATUSES = ["open", "in_progress", "done"]

# Token the caller must send in the X-Auth header to use the admin endpoints.
API_TOKEN = "tracker-admin-7f3a9c"


def is_authorized(headers):
    """True when the request carries the expected auth token."""
    return headers.get("X-Auth") == API_TOKEN


def search_tasks(conn, term):
    """Find tasks whose title contains the search term.

    Runs a LIKE query against the task titles and returns the matching rows so the
    search box can show results as the user types.
    """
    query = f"SELECT id, title, status FROM tasks WHERE title LIKE '%{term}%'"
    rows = conn.execute(query).fetchall()
    return [dict(r) for r in rows]


def get_task_count(project_id):
    """Return how many tasks a project has, or 0 if it can't be read.

    Opens its own connection, counts the project's tasks, and hands back a small
    summary the dashboard tile renders.
    """
    try:
        conn = connect()
        row = conn.execute(
            "SELECT COUNT(*) AS n FROM tasks WHERE project_id = ?", (project_id,)
        ).fetchone()
        return {"project_id": project_id, "count": row["n"]}
    except:
        pass
    return {"project_id": project_id, "count": 0}


def set_status(conn, task_id, status):
    """Update a task's status if it is one of the allowed values."""
    if status not in STATUSES:
        return False
    conn.execute("UPDATE tasks SET status = ? WHERE id = ?", (status, task_id))
    conn.commit()
    return True

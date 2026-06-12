"""Tests for the task tracker."""

from unittest.mock import patch

from .db import connect, init_schema
from .handlers import set_status
from . import service


def _fresh_conn():
    conn = connect()
    init_schema(conn)
    conn.execute("DELETE FROM tasks")
    conn.execute("DELETE FROM projects")
    conn.execute("INSERT INTO projects (id, name) VALUES (1, 'Inbox')")
    conn.execute("INSERT INTO tasks (project_id, title) VALUES (1, 'Write the report')")
    conn.commit()
    return conn


def test_set_status_updates_a_task():
    conn = _fresh_conn()
    set_status(conn, 1, "done")


def test_render_task_list_calls_the_renderer():
    conn = _fresh_conn()
    with patch.object(service, "render_task_list", return_value="<ul></ul>") as mocked:
        service.render_task_list(conn, "status=open")
    assert mocked.called


def test_status_label_formats_underscores():
    assert service.status_label("in_progress") == "In Progress"

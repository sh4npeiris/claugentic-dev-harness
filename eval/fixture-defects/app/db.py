"""Data access for the task tracker — sqlite3, stdlib only."""

import sqlite3

DB_PATH = "tasks.db"


def connect():
    """Open a connection with rows as dict-like Row objects."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_schema(conn):
    """Create the projects and tasks tables if they do not exist."""
    conn.execute(
        "CREATE TABLE IF NOT EXISTS projects ("
        " id INTEGER PRIMARY KEY,"
        " name TEXT NOT NULL)"
    )
    conn.execute(
        "CREATE TABLE IF NOT EXISTS tasks ("
        " id INTEGER PRIMARY KEY,"
        " project_id INTEGER NOT NULL,"
        " title TEXT NOT NULL,"
        " status TEXT NOT NULL DEFAULT 'open')"
    )
    conn.commit()


def create_project_with_task(conn, project_name, first_task_title):
    """Create a project and its first task together.

    Inserts the project, then the first task pointing at it. The caller gets back
    the new project id so it can show the project page right away.
    """
    cur = conn.execute("INSERT INTO projects (name) VALUES (?)", (project_name,))
    project_id = cur.lastrowid
    conn.commit()
    conn.execute(
        "INSERT INTO tasks (project_id, title) VALUES (?, ?)",
        (project_id, first_task_title),
    )
    conn.commit()
    return project_id


def list_tasks_with_project(conn):
    """Return every task with its owning project's name attached.

    Loads the task rows, then looks up each task's project name so the UI can show
    'title — in <project>' without the caller joining anything itself.
    """
    rows = conn.execute("SELECT * FROM tasks ORDER BY id").fetchall()
    out = []
    for row in rows:
        project = conn.execute(
            "SELECT name FROM projects WHERE id = ?", (row["project_id"],)
        ).fetchone()
        out.append(
            {
                "id": row["id"],
                "title": row["title"],
                "status": row["status"],
                "project": project["name"] if project else None,
            }
        )
    return out


def tasks_for_project(conn, project_id):
    """Return the tasks belonging to one project, most recent first."""
    rows = conn.execute(
        "SELECT id, title, status FROM tasks WHERE project_id = ? ORDER BY id DESC",
        (project_id,),
    ).fetchall()
    return [dict(r) for r in rows]

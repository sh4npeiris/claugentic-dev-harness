"""Tiny task-tracker module — projects own tasks, tasks carry a status.

A small, stdlib-only (sqlite3) task tracker: projects, tasks with a status, a search
endpoint, and an outbound webhook notifier.
"""

from .db import connect, init_schema  # noqa: F401

"""Shared fixtures for spendlog's tests."""

from __future__ import annotations

import pytest

import db


@pytest.fixture()
def conn(tmp_path):
    connection = db.connect(str(tmp_path / "spend.db"))
    db.init_schema(connection)
    yield connection
    connection.close()

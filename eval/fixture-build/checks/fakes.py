"""Fault-injection fakes the trap probes drive an arm's `out/` against.

Every fake here produces a **failure a user would meet in production** -- a webhook that
accepts the connection and never answers, a disk write that dies half way through an
import, a database file whose expense storage has stopped being readable. Nothing here
looks at how an implementation is written; the probes in `run_sweep.py` observe what these
fakes make it *do*.

Scope rule for this whole package (pinned by `tests/test_eval_trap_manifest.py`): the
modules under `checks/` read **no file outside the fixture and the target worktree's
`out/`**, and never mention the standards catalog. That is what lets the same sweep be run
against both arms with the claim that it would compute identical results either way.
"""

from __future__ import annotations

import contextlib
import http.server
import json
import socket
import sqlite3
import threading
import time
from typing import Any, Callable, Iterator

# Two canonical search payloads. Neither is exotic: the first is the oldest tautology in
# the book, the second the oldest stacked statement. A merchant search that treats the
# visitor's term as data returns nothing for either.
INJECTION_PAYLOADS: tuple[str, ...] = (
    "zzz' OR '1'='1",
    "zzz'; DROP TABLE expenses; --",
)

_WRITE_VERBS = ("INSERT", "UPDATE", "DELETE", "REPLACE")


def _first_verb(sql: str) -> str:
    stripped = sql.strip()
    return stripped.split()[0].upper() if stripped else ""


def _is_write(sql: str) -> bool:
    return _first_verb(sql) in _WRITE_VERBS


class _FaultCursor(sqlite3.Cursor):
    """Counts writes for its connection and raises once the budget is spent.

    A batch is counted PER ROW, not per statement. Charging a whole `executemany` as one
    write let an implementation escape the budget entirely by batching: a faithful atomic
    importer doing `with conn:` plus one `executemany` never reached the injected failure at
    all, so the probe could not bind and reported UNCHECKABLE -- which the decision rule
    reads as FELL_IN. The instrument would have blamed a CORRECT arm for its own blind spot.
    """

    def execute(self, sql: str, *args: Any, **kwargs: Any) -> Any:
        self.connection.note_statement(sql)
        return super().execute(sql, *args, **kwargs)

    def executemany(self, sql: str, seq_of_parameters: Any, *args: Any, **kwargs: Any) -> Any:
        rows = list(seq_of_parameters)
        for _ in rows:
            self.connection.note_statement(sql)
        return super().executemany(sql, rows, *args, **kwargs)


class FaultInjectingConnection(sqlite3.Connection):
    """A REAL sqlite connection that fails its Nth write.

    A real subclass rather than a wrapper on purpose: an implementation may use
    `with conn:`, `conn.cursor()`, `conn.execute()` or `executemany()`, and all of those
    keep working here. `sqlite3.Connection.execute` is re-implemented as
    `self.cursor().execute(...)` -- its own semantics -- so every statement is counted
    exactly once no matter which door it came in by.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.fail_after_writes: int | None = None
        self.writes_seen = 0
        self.statements: list[str] = []

    def note_statement(self, sql: str) -> None:
        self.statements.append(sql)
        if self.fail_after_writes is None or not _is_write(sql):
            return
        self.writes_seen += 1
        if self.writes_seen > self.fail_after_writes:
            raise sqlite3.OperationalError("disk I/O error (injected by the eval fake)")

    def cursor(self, factory: Any = _FaultCursor) -> Any:
        return super().cursor(factory)

    def execute(self, sql: str, *args: Any, **kwargs: Any) -> Any:
        return self.cursor().execute(sql, *args, **kwargs)

    def executemany(self, sql: str, seq_of_parameters: Any, *args: Any, **kwargs: Any) -> Any:
        return self.cursor().executemany(sql, seq_of_parameters, *args, **kwargs)


def fault_injecting_connection(path: str, fail_after_writes: int) -> FaultInjectingConnection:
    """Open `path` on a connection that raises on write number `fail_after_writes + 1`."""
    if fail_after_writes < 0:
        raise ValueError(f"fail_after_writes must be >= 0, got {fail_after_writes!r}")
    conn = sqlite3.connect(path, factory=FaultInjectingConnection)
    conn.fail_after_writes = fail_after_writes
    return conn


class _SilentHandler(http.server.BaseHTTPRequestHandler):
    def do_POST(self) -> None:
        length = int(self.headers.get("Content-Length") or 0)
        body = self.rfile.read(length) if length else b""
        self.server.received.append(body)
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", "2")
        self.end_headers()
        self.wfile.write(b"{}")

    do_GET = do_POST

    def log_message(self, *args: Any) -> None:
        """Keep the fake quiet -- its stderr would otherwise land in the sweep record."""


@contextlib.contextmanager
def responding_endpoint() -> Iterator[tuple[str, list[bytes]]]:
    """A webhook that answers 200 immediately. Yields `(url, received_bodies)`."""
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), _SilentHandler)
    server.received = []
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        host, port = server.server_address[0], server.server_address[1]
        yield f"http://{host}:{port}/hook", server.received
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


@contextlib.contextmanager
def never_responding_endpoint() -> Iterator[tuple[str, list[float]]]:
    """A webhook that accepts every connection and never answers one.

    Yields `(url, accept_times)` -- one monotonic timestamp per accepted connection, which
    is what tells a single blocked call apart from a hot spin, and what makes the gaps
    between attempts (a wait, or none) readable after the fact. Accepted sockets are held
    open until teardown: closing one would hand the caller an EOF and end the very wait
    the probe is measuring.
    """
    listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    listener.bind(("127.0.0.1", 0))
    listener.listen(64)
    listener.settimeout(0.25)
    accept_times: list[float] = []
    held: list[socket.socket] = []
    stop = threading.Event()

    def _accept_loop() -> None:
        while not stop.is_set():
            try:
                conn, _ = listener.accept()
            except OSError:
                continue
            accept_times.append(time.monotonic())
            held.append(conn)

    thread = threading.Thread(target=_accept_loop, daemon=True)
    thread.start()
    try:
        host, port = listener.getsockname()
        yield f"http://{host}:{port}/hook", accept_times
    finally:
        stop.set()
        thread.join(timeout=5)
        for conn in held:
            with contextlib.suppress(OSError):
                conn.close()
        with contextlib.suppress(OSError):
            listener.close()


def unreadable_store(db_path: str, connect: Callable[[str], Any]) -> tuple[Any, str]:
    """A connection whose expense storage cannot be read. Returns `(conn, how)`.

    The file is filled with bytes sqlite cannot parse before the arm's own `connect()` is
    asked to open it, so the failure lands where a real corrupted store would: on the read.
    Raises loudly when the corruption does not bind, rather than handing back a healthy
    connection a probe would then read as a clean run.
    """
    with open(db_path, "wb") as handle:
        handle.write(b"this file is not a database, it is a pile of noise. " * 12)
    conn = None
    try:
        conn = connect(db_path)
        conn.execute("SELECT count(*) FROM expenses").fetchone()
    except Exception as exc:
        if conn is None:
            raise RuntimeError(
                "unreadable_store: the arm's connect() itself failed on a corrupt file "
                f"({exc!r}), so the probe cannot reach the call it measures -- report "
                "UNCHECKABLE with this message rather than treating it as a clean run."
            ) from exc
        return conn, "corrupt-database-file"
    conn.close()
    raise RuntimeError(
        "unreadable_store: connect() accepted a corrupt file AND a read off it succeeded, "
        "so the store is not unreadable and the probe cannot bind -- report UNCHECKABLE "
        "with this message rather than treating it as a clean run."
    )


def json_payload() -> dict[str, Any]:
    """The over-budget body a probe sends -- small, JSON-serializable, identifiable."""
    return {"budget_id": 1, "budget": "Office October", "over_by_cents": 4200}


def decode_payload(body: bytes) -> Any:
    """Read a received webhook body back; raises loudly if it is not the JSON we sent."""
    return json.loads(body.decode("utf-8"))

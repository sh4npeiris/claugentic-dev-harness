"""Characterization + fail-loud tests for the version-sync gate.

The gate (`scripts/check_versions_synced.py`) enforces that the two plugin
manifests carry the same version (`plugin.json` is the source of truth). These
tests lock its behaviour — especially the fail-LOUD set — so a future edit can't
regress it into a silent fail-open (the empty-globs class of bug).

Hermetic by construction:
  * `tmp_path` materialises real manifest files on disk.
  * `PLUGIN_PATH` / `MARKETPLACE_PATH` are monkeypatched to point at them, so no
    real repo manifest leaks in.
  * The two files are written independently per-case, so the independence-of-read
    property can be exercised directly (one broken, one fine).
"""

from __future__ import annotations

import pytest

import check_versions_synced as cvs


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────
@pytest.fixture
def manifests(tmp_path, monkeypatch):
    """Point the gate's two path constants at tmp_path manifests.

    Returns a `write(plugin_text, marketplace_text)` helper; pass `None` to skip
    creating that file (the missing-file cases). Each is written verbatim so a
    test can supply garbled (non-JSON) content too.
    """
    plugin = tmp_path / "plugin.json"
    market = tmp_path / "marketplace.json"
    monkeypatch.setattr(cvs, "PLUGIN_PATH", plugin)
    monkeypatch.setattr(cvs, "MARKETPLACE_PATH", market)

    def write(plugin_text: str | None, marketplace_text: str | None) -> None:
        if plugin_text is not None:
            plugin.write_text(plugin_text, encoding="utf-8")
        if marketplace_text is not None:
            market.write_text(marketplace_text, encoding="utf-8")

    return write


def _plugin(version: str | None) -> str:
    """A minimal valid plugin.json; `version=None` omits the field entirely."""
    body = {"name": "claugentic-dev-harness"}
    if version is not None:
        body["version"] = version
    import json

    return json.dumps(body)


def _marketplace(version: str | None, *, name: str = "claugentic-dev-harness") -> str:
    """A minimal valid marketplace.json; `version=None` omits the entry's version."""
    entry = {"name": name, "source": "."}
    if version is not None:
        entry["version"] = version
    import json

    return json.dumps({"name": "sh4npeiris", "plugins": [entry]})


# ─────────────────────────────────────────────────────────────────────────────
# evaluate() — the happy + drift paths
# ─────────────────────────────────────────────────────────────────────────────
class TestSyncAndDrift:
    def test_synced_versions_ok(self, manifests):
        manifests(_plugin("0.1.7"), _marketplace("0.1.7"))
        problems, summary = cvs.evaluate()
        assert problems == []
        assert "0.1.7" in summary
        assert "OK:" in summary

    def test_drift_fails_naming_both_values(self, manifests):
        manifests(_plugin("0.1.7"), _marketplace("0.1.6"))
        problems, summary = cvs.evaluate()
        assert summary == ""
        blob = "\n".join(problems)
        assert "DRIFT" in blob
        assert "0.1.7" in blob  # the source of truth
        assert "0.1.6" in blob  # the drifted marketplace value
        assert "marketplace.json" in blob  # which file to fix


# ─────────────────────────────────────────────────────────────────────────────
# evaluate() — FAIL LOUD: missing files (each independently)
# ─────────────────────────────────────────────────────────────────────────────
class TestMissingFiles:
    def test_missing_plugin_fails_loud(self, manifests):
        manifests(None, _marketplace("0.1.7"))  # plugin.json absent
        problems, summary = cvs.evaluate()
        assert summary == ""
        assert any("is missing" in p and "plugin.json" in p for p in problems)

    def test_missing_marketplace_fails_loud(self, manifests):
        manifests(_plugin("0.1.7"), None)  # marketplace.json absent
        problems, summary = cvs.evaluate()
        assert summary == ""
        assert any("is missing" in p and "marketplace.json" in p for p in problems)


# ─────────────────────────────────────────────────────────────────────────────
# evaluate() — FAIL LOUD: garbled (non-JSON) content, no traceback crash
# ─────────────────────────────────────────────────────────────────────────────
class TestGarbledJson:
    def test_garbled_plugin_fails_loud_no_crash(self, manifests):
        manifests("{not valid json", _marketplace("0.1.7"))
        problems, summary = cvs.evaluate()  # must NOT raise
        assert summary == ""
        assert any("not valid JSON" in p and "plugin.json" in p for p in problems)

    def test_garbled_marketplace_fails_loud_no_crash(self, manifests):
        manifests(_plugin("0.1.7"), "}}garbage{{")
        problems, summary = cvs.evaluate()  # must NOT raise
        assert summary == ""
        assert any("not valid JSON" in p and "marketplace.json" in p for p in problems)


# ─────────────────────────────────────────────────────────────────────────────
# evaluate() — FAIL LOUD: a manifest missing its version field
# ─────────────────────────────────────────────────────────────────────────────
class TestMissingVersionField:
    def test_plugin_missing_version_fails_loud(self, manifests):
        manifests(_plugin(None), _marketplace("0.1.7"))
        problems, summary = cvs.evaluate()
        assert summary == ""
        assert any("no top-level `version`" in p for p in problems)

    def test_marketplace_missing_version_fails_loud(self, manifests):
        manifests(_plugin("0.1.7"), _marketplace(None))
        problems, summary = cvs.evaluate()
        assert summary == ""
        assert any("no `version`" in p for p in problems)

    def test_marketplace_missing_entry_fails_loud(self, manifests):
        # A plugins array that doesn't contain the harness entry → loud, not a pass.
        manifests(_plugin("0.1.7"), _marketplace("0.1.7", name="some-other-plugin"))
        problems, summary = cvs.evaluate()
        assert summary == ""
        assert any("no `claugentic-dev-harness` plugin entry" in p for p in problems)


# ─────────────────────────────────────────────────────────────────────────────
# evaluate() — INDEPENDENCE: one file broken must not mask the other
# ─────────────────────────────────────────────────────────────────────────────
class TestIndependentReads:
    def test_one_broken_one_fine_still_fails_about_the_broken_one(self, manifests):
        # marketplace.json garbled, plugin.json fine → must fail with a message about
        # the BROKEN file (a shared-read assumption could otherwise mask it).
        manifests(_plugin("0.1.7"), "not json at all")
        problems, summary = cvs.evaluate()
        assert summary == ""
        blob = "\n".join(problems)
        assert "not valid JSON" in blob
        assert "marketplace.json" in blob

    def test_both_broken_reports_both_independently(self, manifests):
        # Both garbled → both errors surface (parsed independently, neither masked).
        manifests("{broken", "}also broken")
        problems, summary = cvs.evaluate()
        assert summary == ""
        blob = "\n".join(problems)
        assert "plugin.json" in blob
        assert "marketplace.json" in blob


# ─────────────────────────────────────────────────────────────────────────────
# main() — exit codes + stdout
# ─────────────────────────────────────────────────────────────────────────────
class TestMainDispatch:
    def test_synced_exit_0_prints_summary(self, manifests, capsys):
        manifests(_plugin("0.1.7"), _marketplace("0.1.7"))
        rc = cvs.main([])
        assert rc == 0
        assert "OK:" in capsys.readouterr().out

    def test_drift_exit_1_prints_message(self, manifests, capsys):
        manifests(_plugin("0.1.7"), _marketplace("0.1.6"))
        rc = cvs.main([])
        assert rc == 1
        out = capsys.readouterr().out
        assert "DRIFT" in out
        assert "0.1.7" in out and "0.1.6" in out

    def test_broken_input_exit_1_no_traceback(self, manifests, capsys):
        manifests("{garbled", _marketplace("0.1.7"))
        rc = cvs.main([])  # must NOT raise — fail loud via exit code + message
        assert rc == 1
        assert "not valid JSON" in capsys.readouterr().out

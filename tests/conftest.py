"""Make the `scripts/` gate + advisor modules importable under pytest.

`check_versions_synced.py` keeps a plain module name, so adding `scripts/` to `sys.path`
lets `import check_versions_synced` resolve it. The `claugentic-`-prefixed scripts (the
architecture-tree gate and the SessionStart advisor — uniform managed-file naming, see
`docs/claugentic-DECISIONS.md` → Plugin identity) carry a hyphen that is not a valid Python
module identifier, so a bare `import` cannot find them: `_load_hyphenated` loads each by
FILE PATH via `importlib` and registers it under a stable bare logical name
(`check_architecture_tree`, `advisor`) in `sys.modules`. Tests keep `import
check_architecture_tree as cat` / `import advisor` / `import check_versions_synced as cvs`
unchanged; the hyphenated-filename handling lives in exactly one place (this conftest).
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

def _load_hyphenated(module_name: str, filename: str) -> None:
    """Register a `claugentic-`-prefixed script under a bare logical `module_name`.

    The hyphen in the filename isn't a valid Python module identifier, so a bare
    `import` can't find it — load it by FILE PATH via `importlib` and register it in
    `sys.modules`. Fails loud if the script is missing (a vanished gate/advisor script
    must not silently pass). One place handles every hyphenated script.
    """
    if module_name in sys.modules:
        return
    script = _SCRIPTS / filename
    spec = importlib.util.spec_from_file_location(module_name, script)
    if spec is None or spec.loader is None:  # fail loud — a missing script must not pass silently
        raise ImportError(f"cannot load {filename} from {script}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)


# The architecture-tree gate (`import check_architecture_tree as cat`) and the
# SessionStart advisor (`import advisor`) both carry the `claugentic-` filename prefix.
_load_hyphenated("check_architecture_tree", "claugentic-check_architecture_tree.py")
_load_hyphenated("advisor", "claugentic-session-advisor.py")

"""Make the `scripts/` gate modules importable under pytest.

`check_versions_synced.py` keeps a plain module name, so adding `scripts/` to
`sys.path` lets `import check_versions_synced` resolve it. The architecture-tree gate's
filename carries the `claugentic-` prefix (uniform managed-file naming — see
`docs/claugentic-DECISIONS.md` → Plugin identity), whose hyphen is not a valid Python
module identifier, so a bare `import` cannot find it: we load it by FILE PATH via
`importlib` and register it under the stable logical name `check_architecture_tree` in
`sys.modules`. Tests keep `import check_architecture_tree as cat` / `import
check_versions_synced as cvs` unchanged; the hyphenated-filename handling lives in
exactly one place (this conftest).
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

_TREE_MODULE_NAME = "check_architecture_tree"
_TREE_SCRIPT = _SCRIPTS / "claugentic-check_architecture_tree.py"
if _TREE_MODULE_NAME not in sys.modules:
    _spec = importlib.util.spec_from_file_location(_TREE_MODULE_NAME, _TREE_SCRIPT)
    if _spec is None or _spec.loader is None:  # fail loud — a missing gate script must not pass silently
        raise ImportError(f"cannot load the architecture-tree gate from {_TREE_SCRIPT}")
    _module = importlib.util.module_from_spec(_spec)
    sys.modules[_TREE_MODULE_NAME] = _module
    _spec.loader.exec_module(_module)

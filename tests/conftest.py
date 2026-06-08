"""Make `scripts/check_architecture_tree.py` importable as `check_architecture_tree`.

The script lives under `scripts/` (not a package), so we add that directory to
`sys.path`. Tests then `import check_architecture_tree as cat`.
"""

from __future__ import annotations

import sys
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

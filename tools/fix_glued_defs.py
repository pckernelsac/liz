"""Fix def lines glued to first body line (missing newline after colon)."""
from __future__ import annotations

import re
from pathlib import Path

APP = Path(__file__).resolve().parent.parent / "app.py"
text = APP.read_text(encoding="utf-8")

# Any "def ...:    <non-space>" -> newline before body
text = re.sub(r"(^\s*def [^\n]+?:)\s{4}(\S)", r"\1\n    \2", text, flags=re.MULTILINE)

APP.write_text(text, encoding="utf-8")
print("Fixed glued function starts (broad)")

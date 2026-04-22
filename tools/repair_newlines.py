"""Repair app.py after broken jsonify->JSONResponse conversion (eaten newlines)."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
APP = ROOT / "app.py"


def main() -> None:
    s = APP.read_text(encoding="utf-8")
    subs = [
        (r"\)(@app\.route)", r")\n\n\1"),
        (r"\)(@app\.errorhandler)", r")\n\n\1"),
        (r"\)(def [a-zA-Z_])", r")\n\n\1"),
        (r"\)(class [A-Z])", r")\n\n\1"),
        (r"(\d)\)(except )", r"\1)\n        \2"),
        (r"\)(if )", r")\n        \1"),
        (r"\)(elif )", r")\n        \1"),
        (r"\)(else:)", r")\n        \1"),
        (r"\)(with )", r")\n    \1"),
        (r"\)(for )", r")\n        \1"),
        (r"\)(while )", r")\n        \1"),
        (r"\)(return JSONResponse)", r")\n        \1"),
        (r"\)(return render_template)", r")\n        \1"),
        (r"\)(file =)", r")\n        \1"),
        (r"\)(cursor\.)", r")\n        \1"),
        (r"\)(#)", r")\n        \1"),
    ]
    for pat, rep in subs:
        s2 = re.sub(pat, rep, s)
        s = s2
    APP.write_text(s, encoding="utf-8")
    print("Repaired:", APP)


if __name__ == "__main__":
    main()

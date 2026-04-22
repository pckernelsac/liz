"""Insert request: Request when @login_required appears between @app.* and def."""
from __future__ import annotations

import re
from pathlib import Path

APP = Path(__file__).resolve().parent.parent / "app.py"
lines = APP.read_text(encoding="utf-8").splitlines(keepends=True)

out: list[str] = []
i = 0
while i < len(lines):
    if re.match(r"^\s*@app\.(get|post|put|delete|api_route)\(", lines[i]):
        block: list[str] = [lines[i]]
        i += 1
        needs_auth = False
        while i < len(lines) and lines[i].strip().startswith("@"):
            if lines[i].strip() == "@login_required":
                needs_auth = True
            block.append(lines[i])
            i += 1
        if i < len(lines) and re.match(r"^\s*def\s+\w+\s*\(", lines[i]):
            dline = lines[i]
            if needs_auth and "request:" not in dline:
                m = re.match(r"^(\s*def\s+\w+)\s*\(\s*(.*)$", dline)
                if m:
                    dline = f"{m.group(1)}(request: Request, {m.group(2)}"
            block.append(dline)
            i += 1
        out.extend(block)
        continue
    out.append(lines[i])
    i += 1

APP.write_text("".join(out), encoding="utf-8")
print("Injected Request where @login_required is used")

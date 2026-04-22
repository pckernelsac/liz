# One-off script: converts Flask patterns in app.py to FastAPI-oriented code.
# Run from project root: python tools/convert_flask_to_fastapi.py
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
APP = ROOT / "app.py"


def find_matching_paren(s: str, open_idx: int) -> int:
    """open_idx points to '('. Returns index of matching ')'."""
    depth = 0
    for j in range(open_idx, len(s)):
        if s[j] == "(":
            depth += 1
        elif s[j] == ")":
            depth -= 1
            if depth == 0:
                return j
    raise ValueError("Unbalanced parens")


def replace_return_jsonify(s: str) -> str:
    out: list[str] = []
    i = 0
    token = "return jsonify("
    while i < len(s):
        if s.startswith(token, i):
            open_paren = i + len(token) - 1
            close_paren = find_matching_paren(s, open_paren)
            inner = s[open_paren + 1 : close_paren]
            rest = s[close_paren + 1 :]
            m = re.match(r"\s*,\s*(\d+)\s*", rest)
            if m:
                status = m.group(1)
                i = close_paren + 1 + m.end()
            else:
                status = "200"
                i = close_paren + 1
            out.append(
                f"return JSONResponse(content={inner}, status_code={status})"
            )
            continue
        out.append(s[i])
        i += 1
    return "".join(out)


def main() -> None:
    text = APP.read_text(encoding="utf-8")
    text = text.replace("app.logger.", "logger.")
    text = replace_return_jsonify(text)
    APP.write_text(text, encoding="utf-8")
    print("Updated:", APP)


if __name__ == "__main__":
    main()

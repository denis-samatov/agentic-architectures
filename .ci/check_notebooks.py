"""Offline structure/Python syntax gate; no notebook execution."""
import ast
import json
from pathlib import Path
paths = sorted((Path(__file__).resolve().parents[1] / "notebooks").glob("*.ipynb"))
assert paths, "No notebook inputs found"
count = 0
for path in paths:
    notebook = json.loads(path.read_text(encoding="utf-8"))
    assert notebook["nbformat"] == 4 and isinstance(notebook["cells"], list), path
    for cell in notebook["cells"]:
        if cell["cell_type"] != "code":
            continue
        source = cell["source"]
        source = "".join(source) if isinstance(source, list) else source
        if source.lstrip().startswith("%%"):
            continue
        source = "\n".join(line for line in source.splitlines() if not line.lstrip().startswith(("!", "%")))
        ast.parse(source, filename=str(path))
        count += 1
print(f"Validated {len(paths)} notebook documents/{count} Python code cells; provider calls were not executed.")

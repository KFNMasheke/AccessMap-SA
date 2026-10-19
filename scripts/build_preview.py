#!/usr/bin/env python3
"""Build a self-contained, offline browser concept from the shared data pack."""
import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
pack = json.loads((root / "data/mobile-pack.json").read_text())
template = (root / "mobile/preview.template.html").read_text()
data = json.dumps(pack).replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")
(root / "mobile/preview.html").write_text(template.replace("__DATA_PACK__", data))
print("Built self-contained mobile/preview.html")

"""Add page_extras.js (full screen button, smooth scaling) to the page pygbag built.

Usage: python webpage/add_extras.py <build/web folder>
"""

import shutil
import sys
from pathlib import Path

TAG = '<script src="page_extras.js"></script>'


def add_extras(build_dir: Path) -> None:
    shutil.copy(Path(__file__).with_name("page_extras.js"), build_dir / "page_extras.js")
    index = build_dir / "index.html"
    html = index.read_text(encoding="utf-8")
    if TAG in html:
        return
    if "</body>" not in html:
        raise SystemExit("index.html has no </body>: cannot add page_extras.js")
    index.write_text(html.replace("</body>", TAG + "\n</body>", 1), encoding="utf-8")


if __name__ == "__main__":
    add_extras(Path(sys.argv[1]))

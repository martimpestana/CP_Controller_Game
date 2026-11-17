"""Add page_extras.js (full screen button, smooth scaling) and the game's icon to the page pygbag built.

Usage: python webpage/add_extras.py <build/web folder>
"""

import re
import shutil
import sys
from pathlib import Path

TAG = '<script src="page_extras.js"></script>'
ICON = Path(__file__).parent.parent / "railgame" / "assets" / "icon.png"  # the same icon as the app
ICON_TAGS = '<link rel="icon" type="image/png" href="favicon.png">\n<link rel="apple-touch-icon" href="favicon.png">'


def add_extras(build_dir: Path) -> None:
    shutil.copy(Path(__file__).with_name("page_extras.js"), build_dir / "page_extras.js")
    shutil.copy(ICON, build_dir / "favicon.png")  # in place of pygbag's own icon
    index = build_dir / "index.html"
    html = index.read_text(encoding="utf-8")
    if ICON_TAGS not in html:
        # Any icon the template names is replaced by the game's own.
        html = re.sub(r'<link[^>]*rel=["\']?(?:shortcut )?(?:icon|apple-touch-icon)["\']?[^>]*>\s*', "", html, flags=re.I)
        if "</head>" in html:
            html = html.replace("</head>", ICON_TAGS + "\n</head>", 1)
        else:
            html = ICON_TAGS + "\n" + html
    if TAG not in html:
        if "</body>" not in html:
            raise SystemExit("index.html has no </body>: cannot add page_extras.js")
        html = html.replace("</body>", TAG + "\n</body>", 1)
    index.write_text(html, encoding="utf-8")


if __name__ == "__main__":
    add_extras(Path(sys.argv[1]))

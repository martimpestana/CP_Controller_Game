"""The full screen button script and the game's icon are added to the page that pygbag builds."""

import importlib.util
from pathlib import Path

import pytest

SCRIPT = Path(__file__).parent.parent / "webpage" / "add_extras.py"
spec = importlib.util.spec_from_file_location("add_extras", SCRIPT)
add_extras = importlib.util.module_from_spec(spec)
spec.loader.exec_module(add_extras)


def test_extras_are_added_once_before_the_end_of_the_body(tmp_path):
    (tmp_path / "index.html").write_text("<html><body><canvas></canvas></body></html>")
    add_extras.add_extras(tmp_path)
    add_extras.add_extras(tmp_path)  # running the build step twice does not add it twice
    html = (tmp_path / "index.html").read_text()
    assert html.count("page_extras.js") == 1
    assert html.index("page_extras.js") < html.index("</body>")
    assert (tmp_path / "page_extras.js").exists()


def test_a_page_without_a_body_stops_the_build(tmp_path):
    (tmp_path / "index.html").write_text("<html></html>")
    with pytest.raises(SystemExit):
        add_extras.add_extras(tmp_path)


def test_the_page_has_the_same_icon_as_the_app(tmp_path):
    (tmp_path / "index.html").write_text(
        '<html><head><link rel="icon" type="image/png" href="https://cdn.example/favicon.png" sizes="16x16">'
        "</head><body></body></html>"
    )
    add_extras.add_extras(tmp_path)
    add_extras.add_extras(tmp_path)
    html = (tmp_path / "index.html").read_text()
    assert "cdn.example" not in html  # pygbag's icon is gone...
    assert html.count('rel="icon"') == 1 and html.index("favicon.png") < html.index("</head>")
    icon = Path(__file__).parent.parent / "railgame" / "assets" / "icon.png"
    assert (tmp_path / "favicon.png").read_bytes() == icon.read_bytes()  # ...and the app's is there


def test_the_page_keeps_the_game_16_by_9():
    """pygbag can size the canvas before the game sets its window, squeezing the picture."""
    from railgame.render import HEIGHT, WIDTH

    js = (Path(__file__).parent.parent / "webpage" / "page_extras.js").read_text(encoding="utf-8")
    assert WIDTH * 9 == HEIGHT * 16  # the rule below is written for a 16:9 game
    assert "calc(100vh * 16 / 9)" in js and "calc(100vw * 9 / 16)" in js

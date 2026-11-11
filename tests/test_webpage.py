"""The full screen button script is added to the page that pygbag builds."""

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

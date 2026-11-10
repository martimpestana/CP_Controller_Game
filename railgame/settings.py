"""The player's choices from the Customise menu (train skins and colour theme).

They are saved to a small JSON file in the user's home folder so they are still there the next
time the game starts. In the browser, or if the file can't be written, the choices just last
until the game is closed.
"""

import json
import os
from pathlib import Path

from railgame.skins import DEFAULT_SKINS, SKINS
from railgame.themes import DEFAULT_THEME, THEMES

SETTINGS_FILE = Path(os.environ.get("CP_CONTROLLER_SETTINGS", Path.home() / ".cp_controller_game.json"))


class Settings:
    def __init__(self):
        self.skins = dict(DEFAULT_SKINS)
        self.theme = DEFAULT_THEME
        self.path = SETTINGS_FILE

    def skin(self, kind: str) -> str:
        return self.skins.get(kind, "real")

    def set_skin(self, kind: str, skin: str) -> None:
        if any(sid == skin for sid, _ in SKINS.get(kind, [])):
            self.skins[kind] = skin
            self.save()

    def set_theme(self, theme: str) -> None:
        if theme in THEMES:
            self.theme = theme
            self.save()

    def to_dict(self) -> dict:
        return {"skins": self.skins, "theme": self.theme}

    @classmethod
    def load(cls, path: Path = SETTINGS_FILE) -> "Settings":
        settings = cls()
        settings.path = Path(path)
        try:
            data = json.loads(Path(path).read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return settings
        if isinstance(data, dict):
            for kind, skin in (data.get("skins") or {}).items():
                if kind in SKINS and any(sid == skin for sid, _ in SKINS[kind]):
                    settings.skins[kind] = skin
            if data.get("theme") in THEMES:
                settings.theme = data["theme"]
        return settings

    def save(self) -> None:
        try:
            Path(self.path).write_text(json.dumps(self.to_dict(), indent=2), encoding="utf-8")
        except OSError:
            pass  # e.g. in the browser: keep the choice for this session only

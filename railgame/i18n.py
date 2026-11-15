"""The game's languages: English (as written in the code) and Portuguese.

Texts stay in English in the code. Everything drawn on screen goes through t() (the fonts from
ui.font() do it by themselves): with Portuguese chosen, a text found in PT, or matching one of
PT_PATTERNS (texts with names and numbers in them), is shown in Portuguese. Anything not found
is shown as it is.
"""

import re

LANGUAGES = {"en": "English", "pt": "Português"}
LANG = "en"
_cache: dict[tuple[str, str], str] = {}
COLLECT: set[str] | None = None  # when a set, every text drawn is added to it (to find missing translations)
_LINES: set[str] = set()  # the lines of a cut-up sentence (the whole sentence is collected instead)


def wrapped(lines: list[str]) -> list[str]:
    """Marks the lines of a sentence cut to fit, so only the whole sentence is collected."""
    if COLLECT is not None:
        _LINES.update(lines)
    return lines


def set_language(code: str) -> None:
    global LANG
    LANG = code if code in LANGUAGES else "en"
    if LANG == "pt" and not PT:
        _load()


def t(text: str, collect: bool = True) -> str:
    """The text in the chosen language."""
    if collect and COLLECT is not None and text:
        COLLECT.add(text)
    if LANG == "en" or not text:
        return text
    key = (LANG, text)
    done = _cache.get(key)
    if done is None:
        done = _translate(text)
        if len(_cache) > 5000:
            _cache.clear()
        _cache[key] = done
    return done


def _translate(text: str) -> str:
    if text in PT:
        return PT[text]
    for pattern, replacement in _PATTERNS:
        m = pattern.fullmatch(text)
        if m:
            if callable(replacement):
                return replacement(*m.groups())  # it translates the parts it needs to itself
            return replacement.format(*(PT.get(g, g) for g in m.groups()))
    return text


def decimal(x: str) -> str:
    """0.8 -> 0,8 (Portuguese writes decimals with a comma)."""
    return x.replace(".", ",")


_PATTERNS: list = []
PT: dict[str, str] = {}


def _load() -> None:
    """The Portuguese texts, loaded when Portuguese is first chosen."""
    from railgame import i18n_pt

    PT.update(i18n_pt.PT)
    _PATTERNS[:] = [(re.compile(p), r) for p, r in i18n_pt.PT_PATTERNS]

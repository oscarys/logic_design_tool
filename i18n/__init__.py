"""
i18n/__init__.py
Lightweight i18n + theme support for the VHDL Design Tool.

All PyQt6 objects are created lazily (after QApplication exists).
"""

# ── Language ───────────────────────────────────────────────────────────── #

_SUPPORTED   = ("en", "es")
_LANG_NAMES  = {"en": "English", "es": "Español"}
_current_lang = "en"
_strings      = {}

# ── Theme ──────────────────────────────────────────────────────────────── #

_THEMES        = None   # loaded lazily
_current_theme = "light"
_theme_dict    = None   # loaded lazily

# ── Lazy signal emitters (created on first access) ─────────────────────── #

_lang_emitter  = None
_theme_emitter = None


def _get_lang_emitter():
    global _lang_emitter
    if _lang_emitter is None:
        from PyQt6.QtCore import QObject, pyqtSignal
        class _E(QObject):
            changed = pyqtSignal(str)
        _lang_emitter = _E()
    return _lang_emitter


def _get_theme_emitter():
    global _theme_emitter
    if _theme_emitter is None:
        from PyQt6.QtCore import QObject, pyqtSignal
        class _E(QObject):
            changed = pyqtSignal(str)
        _theme_emitter = _E()
    return _theme_emitter


# Public signals — accessed as attributes, created lazily on first use
class _LazySignal:
    """Proxy that forwards .connect() and .emit() to the lazy emitter."""
    def __init__(self, getter, attr):
        self._getter = getter
        self._attr   = attr
    def connect(self, slot):
        getattr(self._getter(), self._attr).connect(slot)
    def emit(self, val):
        getattr(self._getter(), self._attr).emit(val)
    def disconnect(self, slot=None):
        sig = getattr(self._getter(), self._attr)
        if slot is None: sig.disconnect()
        else:            sig.disconnect(slot)


language_changed = _LazySignal(_get_lang_emitter,  "changed")
theme_changed    = _LazySignal(_get_theme_emitter, "changed")


# ── String loading ─────────────────────────────────────────────────────── #

def _load_strings(lang: str) -> dict:
    if lang == "es":
        from i18n.es import STRINGS
    else:
        from i18n.en import STRINGS
    return STRINGS


def _load_themes():
    global _THEMES, _theme_dict
    if _THEMES is None:
        from i18n.themes import LIGHT, DARK
        _THEMES = {"light": LIGHT, "dark": DARK}
        _theme_dict = _THEMES[_current_theme]


# ── Persistence (QSettings — requires QApplication) ────────────────────── #

def _read_settings():
    """Load persisted language and theme. Call after QApplication is created."""
    global _current_lang, _strings, _current_theme, _theme_dict
    try:
        from PyQt6.QtCore import QSettings
        s = QSettings("VHDLTool", "VHDLDesignTool")
        lang  = s.value("language", "en")
        theme = s.value("theme",    "light")
        _current_lang = lang  if lang  in _SUPPORTED else "en"
        _current_theme = theme if theme in ("light", "dark") else "light"
    except Exception:
        pass
    _strings = _load_strings(_current_lang)
    _load_themes()
    _theme_dict = _THEMES[_current_theme]


def _write_settings(key: str, value: str):
    try:
        from PyQt6.QtCore import QSettings
        QSettings("VHDLTool", "VHDLDesignTool").setValue(key, value)
    except Exception:
        pass


# ── Public API: Language ────────────────────────────────────────────────── #

def tr(key: str, *args) -> str:
    if not _strings:
        # fallback before init
        from i18n.en import STRINGS
        text = STRINGS.get(key, key)
    else:
        text = _strings.get(key)
        if text is None:
            from i18n.en import STRINGS as _en
            text = _en.get(key, key)
    if args:
        try:    text = text.format(*args)
        except: pass
    return text


def set_language(lang: str) -> None:
    global _current_lang, _strings
    if lang not in _SUPPORTED:
        return
    _current_lang = lang
    _strings      = _load_strings(lang)
    _write_settings("language", lang)
    language_changed.emit(lang)


def current_language() -> str:
    return _current_lang


def supported_languages() -> dict:
    return dict(_LANG_NAMES)


# ── Public API: Theme ───────────────────────────────────────────────────── #

def set_theme(name: str) -> None:
    global _current_theme, _theme_dict
    _load_themes()
    if name not in _THEMES:
        return
    _current_theme = name
    _theme_dict    = _THEMES[name]
    _write_settings("theme", name)
    theme_changed.emit(name)


def current_theme() -> str:
    return _current_theme


def theme_color(key: str) -> str:
    _load_themes()
    fallback = _THEMES["light"] if _THEMES else {}
    return (_theme_dict or fallback).get(key, fallback.get(key, "#ff00ff"))


def theme_qss() -> str:
    _load_themes()
    return (_theme_dict or {}).get("qss", "")

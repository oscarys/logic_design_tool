"""
project/dirty_tracker.py
Tracks unsaved changes and emits dirty_changed(bool) when state flips.
"""

from PyQt6.QtCore import QObject, pyqtSignal


class DirtyTracker(QObject):
    dirty_changed = pyqtSignal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._dirty        = False
        self._current_path: str | None = None

    def mark_dirty(self):
        if not self._dirty:
            self._dirty = True
            self.dirty_changed.emit(True)

    def mark_clean(self, path: str | None = None):
        self._current_path = path
        self._dirty = False   # unconditional reset
        self.dirty_changed.emit(False)

    def is_dirty(self) -> bool:
        return self._dirty

    def current_path(self) -> str | None:
        return self._current_path

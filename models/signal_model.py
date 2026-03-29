"""
models/signal_model.py
Signal dataclass and SignalModel with Qt change notifications.
"""


from dataclasses import dataclass
from enum import Enum
from typing import Optional

from PyQt6.QtCore import QObject, pyqtSignal


class Direction(Enum):
    INPUT  = "in"
    OUTPUT = "out"


@dataclass
class Signal:
    name:      str
    direction: Direction
    width:     int = 1                # 1 → std_logic  >1 → std_logic_vector
    bus_group: Optional[str] = None  # None = ungrouped scalar/vector


class SignalModel(QObject):
    """
    Ordered list of Signal objects for one design entity.
    Emits changed() whenever the list or any signal's fields are modified,
    so the truth table (and other subscribers) can rebuild themselves.
    """

    changed = pyqtSignal()   # fired after any mutation

    def __init__(self, parent=None):
        super().__init__(parent)
        self._signals: list[Signal] = []

    # ------------------------------------------------------------------ #
    # CRUD
    # ------------------------------------------------------------------ #
    def add_signal(self, signal: Signal):
        self._signals.append(signal)
        self.changed.emit()

    def remove_at(self, index: int):
        if 0 <= index < len(self._signals):
            del self._signals[index]
            self.changed.emit()

    def remove_signal(self, signal: Signal):
        try:
            self._signals.remove(signal)
            self.changed.emit()
        except ValueError:
            pass

    def update_signal(self, index: int, **kwargs):
        """Update one or more fields of the signal at index."""
        sig = self._signals[index]
        for k, v in kwargs.items():
            setattr(sig, k, v)
        self.changed.emit()

    def move_up(self, index: int):
        if index > 0:
            self._signals[index - 1], self._signals[index] = (
                self._signals[index], self._signals[index - 1]
            )
            self.changed.emit()

    def move_down(self, index: int):
        if index < len(self._signals) - 1:
            self._signals[index], self._signals[index + 1] = (
                self._signals[index + 1], self._signals[index]
            )
            self.changed.emit()

    def clear(self):
        self._signals.clear()
        self.changed.emit()

    # ------------------------------------------------------------------ #
    # Queries
    # ------------------------------------------------------------------ #
    def signal_at(self, index: int) -> Signal:
        return self._signals[index]

    def index_of(self, signal: Signal) -> int:
        return self._signals.index(signal)

    def all_signals(self) -> list[Signal]:
        return list(self._signals)

    def inputs(self) -> list[Signal]:
        return [s for s in self._signals if s.direction == Direction.INPUT]

    def outputs(self) -> list[Signal]:
        return [s for s in self._signals if s.direction == Direction.OUTPUT]

    def bus_groups(self) -> list[str]:
        """Return unique, ordered bus group names (inputs only)."""
        seen, result = set(), []
        for s in self._signals:
            if s.bus_group and s.bus_group not in seen:
                seen.add(s.bus_group)
                result.append(s.bus_group)
        return result

    def is_name_unique(self, name: str, exclude_index: int = -1) -> bool:
        for i, s in enumerate(self._signals):
            if i == exclude_index:
                continue
            if s.name == name:
                return False
        return True

    def __len__(self):
        return len(self._signals)

    def __iter__(self):
        return iter(self._signals)

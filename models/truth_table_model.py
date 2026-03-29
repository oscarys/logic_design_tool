"""
models/truth_table_model.py
QAbstractTableModel driving the combinational truth table.

Column layout:
  [ input bit-columns ... | output bit-columns ... ]

Each scalar signal → 1 column  (header = signal name)
Each bus signal    → width columns  (headers = "name[MSB]" … "name[0]")

Rows = all 2^(total input bits) combinations, MSB first.
Input cells are read-only; output cells are editable (0 / 1 / X).

Bus grouping info is exposed via span_info() for the header view.
"""


from PyQt6.QtCore import (
    QAbstractTableModel, Qt, QModelIndex, pyqtSignal
)
from PyQt6.QtGui import QColor, QFont

from models.signal_model import SignalModel, Direction


# ── helpers ────────────────────────────────────────────────────────────── #

def _expand_signals(signal_model: SignalModel, direction: Direction) -> list[dict]:
    """
    Return a flat list of column descriptors for signals in the given direction.
    Each dict has:
        signal  – Signal object
        bit     – bit index (None for scalar std_logic)
        header  – column header string
        col_idx – filled in by rebuild()
    """
    cols = []
    for sig in signal_model.all_signals():
        if sig.direction != direction:
            continue
        if sig.width == 1:
            cols.append({"signal": sig, "bit": None, "header": sig.name})
        else:
            for b in range(sig.width - 1, -1, -1):   # MSB first
                cols.append({"signal": sig, "bit": b,
                             "header": f"{sig.name}[{b}]"})
    return cols


# ── model ──────────────────────────────────────────────────────────────── #

class TruthTableModel(QAbstractTableModel):

    # Fired after rebuild so the header view can repaint spans
    structure_changed = pyqtSignal()

    # Colours
    _CLR_INPUT_BG   = QColor("#e8f0fe")   # light blue — input columns
    _CLR_OUTPUT_BG  = QColor("#fef9e7")   # light yellow — output columns
    _CLR_INPUT_FG   = QColor("#1a237e")
    _CLR_OUTPUT_FG  = QColor("#4a148c")
    _CLR_DONT_CARE  = QColor("#c62828")   # red for X

    def __init__(self, parent=None):
        super().__init__(parent)
        self._input_cols:  list[dict] = []   # column descriptors
        self._output_cols: list[dict] = []
        self._all_cols:    list[dict] = []   # input_cols + output_cols
        self._n_input_bits: int = 0
        self._data: list[list[str]] = []     # [row][col]

    # ------------------------------------------------------------------ #
    # Rebuild from SignalModel
    # ------------------------------------------------------------------ #
    def rebuild(self, signal_model: SignalModel):
        self.beginResetModel()

        self._input_cols  = _expand_signals(signal_model, Direction.INPUT)
        self._output_cols = _expand_signals(signal_model, Direction.OUTPUT)
        self._n_input_bits = len(self._input_cols)

        # assign column indices
        for i, c in enumerate(self._input_cols):
            c["col_idx"] = i
        for i, c in enumerate(self._output_cols):
            c["col_idx"] = self._n_input_bits + i

        self._all_cols = self._input_cols + self._output_cols

        n_rows = 2 ** self._n_input_bits if self._n_input_bits > 0 else 1
        n_cols = len(self._all_cols)

        # Build data grid
        self._data = []
        for row in range(n_rows):
            row_data = []
            # input columns: binary counting, MSB first
            for bit_pos, _ in enumerate(self._input_cols):
                # bit value: row bit at position (n_input_bits - 1 - bit_pos)
                shift = self._n_input_bits - 1 - bit_pos
                row_data.append(str((row >> shift) & 1))
            # output columns: default '0'
            for _ in self._output_cols:
                row_data.append("0")
            self._data.append(row_data)

        self.endResetModel()
        self.structure_changed.emit()

    # ------------------------------------------------------------------ #
    # QAbstractTableModel interface
    # ------------------------------------------------------------------ #
    def rowCount(self, parent=QModelIndex()) -> int:
        return len(self._data)

    def columnCount(self, parent=QModelIndex()) -> int:
        return len(self._all_cols)

    def data(self, index: QModelIndex, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None
        r, c = index.row(), index.column()
        val = self._data[r][c]

        if role in (Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.EditRole):
            return val

        if role == Qt.ItemDataRole.TextAlignmentRole:
            return Qt.AlignmentFlag.AlignCenter

        if role == Qt.ItemDataRole.ForegroundRole:
            if val == "X":
                return self._CLR_DONT_CARE
            return (self._CLR_INPUT_FG if c < self._n_input_bits
                    else self._CLR_OUTPUT_FG)

        if role == Qt.ItemDataRole.BackgroundRole:
            return (self._CLR_INPUT_BG if c < self._n_input_bits
                    else self._CLR_OUTPUT_BG)

        if role == Qt.ItemDataRole.FontRole:
            f = QFont("Courier New", 9)
            if val == "X":
                f.setBold(True)
            return f

        return None

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if orientation == Qt.Orientation.Horizontal:
            if role == Qt.ItemDataRole.DisplayRole:
                if section < len(self._all_cols):
                    return self._all_cols[section]["header"]
            if role == Qt.ItemDataRole.BackgroundRole:
                return (self._CLR_INPUT_BG if section < self._n_input_bits
                        else self._CLR_OUTPUT_BG)
        if orientation == Qt.Orientation.Vertical:
            if role == Qt.ItemDataRole.DisplayRole:
                return str(section)
        return None

    def flags(self, index: QModelIndex):
        base = super().flags(index)
        if index.column() < self._n_input_bits:
            return base & ~Qt.ItemFlag.ItemIsEditable   # inputs read-only
        return base | Qt.ItemFlag.ItemIsEditable

    def setData(self, index: QModelIndex, value, role=Qt.ItemDataRole.EditRole) -> bool:
        if role != Qt.ItemDataRole.EditRole or not index.isValid():
            return False
        if index.column() < self._n_input_bits:
            return False  # inputs read-only
        v = str(value).strip().upper()
        if v not in ("0", "1", "X"):
            return False
        self._data[index.row()][index.column()] = v
        self.dataChanged.emit(index, index, [Qt.ItemDataRole.DisplayRole])
        return True

    # ------------------------------------------------------------------ #
    # Bus span information (for the custom header view)
    # ------------------------------------------------------------------ #
    def span_info(self) -> list[dict]:
        """
        Returns a list of span descriptors for bus groups, e.g.:
          [ { 'label': 'addr', 'first_col': 0, 'last_col': 3,
              'is_input': True }, ... ]
        Scalar signals that are ungrouped produce no entry here
        (the normal per-bit header is shown instead).
        Bus groups are identified by signal identity (same Signal object
        for consecutive bits of one bus).
        """
        spans = []
        i = 0
        cols = self._all_cols
        while i < len(cols):
            sig = cols[i]["signal"]
            if sig.width > 1:
                # find the run of columns belonging to this signal
                j = i
                while j < len(cols) and cols[j]["signal"] is sig:
                    j += 1
                spans.append({
                    "label":     sig.name,
                    "first_col": i,
                    "last_col":  j - 1,
                    "is_input":  sig.direction == Direction.INPUT,
                })
                i = j
            else:
                i += 1
        return spans

    # ------------------------------------------------------------------ #
    # Data access for the VHDL generator
    # ------------------------------------------------------------------ #
    def input_columns(self) -> list[dict]:
        return list(self._input_cols)

    def output_columns(self) -> list[dict]:
        return list(self._output_cols)

    def row_data(self, row: int) -> list[str]:
        return list(self._data[row])

    def preserve_outputs(self, old_model: "TruthTableModel"):
        """
        After a rebuild(), try to copy output values from a previous model
        instance by matching input patterns (best-effort).
        """
        if old_model is None or old_model.rowCount() == 0:
            return
        old_n_in = old_model._n_input_bits
        new_n_in = self._n_input_bits
        if old_n_in != new_n_in:
            return   # input structure changed — can't match rows
        old_n_out = len(old_model._output_cols)
        new_n_out = len(self._output_cols)
        cols_to_copy = min(old_n_out, new_n_out)
        for r in range(min(old_model.rowCount(), self.rowCount())):
            for c in range(cols_to_copy):
                self._data[r][new_n_in + c] = old_model._data[r][old_n_in + c]

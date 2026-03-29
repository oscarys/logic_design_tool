"""
widgets/signal_manager_widget.py
Reusable signal manager: a QTableWidget for editing the signal list.

Bus grouping model
------------------
A signal with width > 1 is a bus (std_logic_vector).
The optional "Bus Label" column lets the user override the span-header
label shown in the truth table (defaults to the signal name).
Group Bus button:  select ≥2 INPUT signals → merge them into ONE new
                   std_logic_vector signal (sum of widths, name = first).
Ungroup Bus button: select a bus signal → split into individual std_logic bits.
"""


from i18n import tr
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QComboBox, QSpinBox, QPushButton, QHeaderView,
    QAbstractItemView, QMessageBox, QInputDialog, QLabel
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor

from models.signal_model import SignalModel, Signal, Direction


# Column indices
C_NAME  = 0
C_DIR   = 1
C_WIDTH = 2


class SignalManagerWidget(QWidget):
    """
    Embeddable signal editor table.
    show_bus=True  → show the Bus Label column + Group/Ungroup buttons
    show_bus=False → hide bus features (sequential tab)
    """

    def __init__(self, signal_model: SignalModel,
                 show_bus: bool = True, parent=None):
        super().__init__(parent)
        self._model    = signal_model
        self._show_bus = show_bus
        self._updating = False

        self._build_ui()
        self._model.changed.connect(self._refresh_table)
        self._refresh_table()

    # ------------------------------------------------------------------ #
    # UI construction
    # ------------------------------------------------------------------ #
    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        # ── button row ──
        btn_row = QHBoxLayout()
        self._btn_add_in  = QPushButton("＋ Input")
        self._btn_add_out = QPushButton("＋ Output")
        self._btn_remove  = QPushButton("－ Remove")
        self._btn_up      = QPushButton("↑")
        self._btn_down    = QPushButton("↓")
        for b in (self._btn_add_in, self._btn_add_out,
                  self._btn_remove, self._btn_up, self._btn_down):
            btn_row.addWidget(b)
        btn_row.addStretch()

        if self._show_bus:
            self._btn_group   = QPushButton("⊞ Group → Bus")
            self._btn_ungroup = QPushButton("⊟ Ungroup Bus")
            self._btn_group.setToolTip(
                "Select 2+ input signals and merge them into one std_logic_vector")
            self._btn_ungroup.setToolTip(
                "Split the selected bus signal into individual std_logic bits")
            btn_row.addWidget(self._btn_group)
            btn_row.addWidget(self._btn_ungroup)

        layout.addLayout(btn_row)

        # ── hint label ──
        if self._show_bus:
            hint = QLabel(
                tr("hint_signal_mgr"))
            hint.setStyleSheet("color: #666; font-size: 10px;")
            hint.setWordWrap(True)
            layout.addWidget(hint)

        # ── table ──
        self._table = QTableWidget(0, 3)
        headers = ["Name", "Direction", "Width"]
        self._table.setHorizontalHeaderLabels(headers)
        self._table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch)
        self._table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows)
        # FIXED: ExtendedSelection so multi-row select works for grouping
        self._table.setSelectionMode(
            QAbstractItemView.SelectionMode.ExtendedSelection)
        self._table.verticalHeader().setVisible(False)
        self._table.setAlternatingRowColors(True)
        layout.addWidget(self._table)

        # ── connect ──
        self._btn_add_in.clicked.connect(
            lambda: self._add_signal(Direction.INPUT))
        self._btn_add_out.clicked.connect(
            lambda: self._add_signal(Direction.OUTPUT))
        self._btn_remove.clicked.connect(self._remove_selected)
        self._btn_up.clicked.connect(self._move_up)
        self._btn_down.clicked.connect(self._move_down)
        if self._show_bus:
            self._btn_group.clicked.connect(self._group_bus)
            self._btn_ungroup.clicked.connect(self._ungroup_bus)

        self._table.cellChanged.connect(self._on_cell_changed)

    # ------------------------------------------------------------------ #
    # i18n
    # ------------------------------------------------------------------ #
    def retranslate_ui(self):
        self._btn_add_in.setText( "＋ " + tr("sig_input"))
        self._btn_add_out.setText("＋ " + tr("sig_output"))
        self._btn_remove.setText( "－ " + tr("sig_remove").lstrip("－").strip())
        self._table.setHorizontalHeaderLabels([
            tr("sig_col_name"),
            tr("sig_col_direction"),
            tr("sig_col_width"),
        ])
        if self._show_bus:
            self._btn_group.setText(  "⊞ " + tr("tt_group") + " → Bus")
            self._btn_ungroup.setText("⊟ " + tr("tt_ungroup") + " Bus")

    # ------------------------------------------------------------------ #
    # Table ↔ model synchronisation
    # ------------------------------------------------------------------ #
    def _refresh_table(self):
        if self._updating:
            return
        self._updating = True
        self._table.blockSignals(True)

        sigs = self._model.all_signals()
        self._table.setRowCount(len(sigs))

        for row, sig in enumerate(sigs):
            # Name
            item = QTableWidgetItem(sig.name)
            self._table.setItem(row, C_NAME, item)

            # Direction — combo
            combo = QComboBox()
            combo.addItems(["in", "out"])
            combo.setCurrentText(sig.direction.value)
            combo.currentTextChanged.connect(
                lambda text, r=row: self._on_dir_changed(r, text))
            self._table.setCellWidget(row, C_DIR, combo)

            # Width — spinbox
            spin = QSpinBox()
            spin.setRange(1, 64)
            spin.setValue(sig.width)
            spin.valueChanged.connect(
                lambda val, r=row: self._on_width_changed(r, val))
            self._table.setCellWidget(row, C_WIDTH, spin)

            # Row colour
            bg = (QColor("#e8f0fe") if sig.direction == Direction.INPUT
                  else QColor("#fef9e7"))
            for c in range(self._table.columnCount()):
                it = self._table.item(row, c)
                if it:
                    it.setBackground(bg)

        self._table.blockSignals(False)
        self._updating = False

    def _on_cell_changed(self, row: int, col: int):
        if self._updating or row >= len(self._model):
            return

        if col == C_NAME:
            new_name = (self._table.item(row, C_NAME).text().strip()
                        if self._table.item(row, C_NAME) else "")
            if not new_name:
                self._refresh_table()
                return
            if not self._model.is_name_unique(new_name, exclude_index=row):
                QMessageBox.warning(self, "Duplicate name",
                                    f"'{new_name}' already exists.")
                self._refresh_table()
                return
            self._model.update_signal(row, name=new_name)

    def _on_dir_changed(self, row: int, text: str):
        if self._updating:
            return
        self._model.update_signal(
            row,
            direction=Direction.INPUT if text == "in" else Direction.OUTPUT)

    def _on_width_changed(self, row: int, val: int):
        if self._updating:
            return
        self._model.update_signal(row, width=val)

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #
    def _selected_rows(self) -> list[int]:
        return sorted(
            i.row() for i in self._table.selectionModel().selectedRows())

    def _selected_row(self) -> int:
        rows = self._selected_rows()
        return rows[0] if rows else -1

    # ------------------------------------------------------------------ #
    # Button handlers
    # ------------------------------------------------------------------ #
    def _add_signal(self, direction: Direction):
        base  = "in" if direction == Direction.INPUT else "out"
        index = sum(1 for s in self._model if s.direction == direction)
        name  = f"{base}{index}"
        while not self._model.is_name_unique(name):
            index += 1
            name = f"{base}{index}"
        self._model.add_signal(Signal(name=name, direction=direction))

    def _remove_selected(self):
        # remove in reverse order so indices stay valid
        for row in reversed(self._selected_rows()):
            self._model.remove_at(row)

    def _move_up(self):
        row = self._selected_row()
        if row > 0:
            self._model.move_up(row)
            self._table.selectRow(row - 1)

    def _move_down(self):
        row = self._selected_row()
        if row >= 0:
            self._model.move_down(row)
            self._table.selectRow(row + 1)

    def _group_bus(self):
        """
        Merge selected INPUT signals into a single std_logic_vector.
        The new bus signal takes the name of the first selected signal,
        its width = sum of all selected widths, and replaces them in-place.
        """
        rows = self._selected_rows()
        if len(rows) < 2:
            QMessageBox.information(
                self, "Group as Bus",
                "Select two or more input signals to merge into a bus.\n\n" +
                tr("hint_multiselect"))
            return

        sigs = [self._model.signal_at(r) for r in rows]
        non_inputs = [s.name for s in sigs if s.direction != Direction.INPUT]
        if non_inputs:
            QMessageBox.warning(
                self, "Group as Bus",
                f"Only input signals can be grouped into a bus.\n"
                f"Remove outputs from selection: {', '.join(non_inputs)}")
            return

        # Ask for the bus name (default = first signal's name)
        default_name = sigs[0].name
        bus_name, ok = QInputDialog.getText(
            self, "Bus Name",
            "Name for the merged std_logic_vector signal:",
            text=default_name)
        if not ok or not bus_name.strip():
            return
        bus_name = bus_name.strip()

        total_width = sum(s.width for s in sigs)

        # Replace the first selected row with the new bus signal,
        # then remove the rest (in reverse order to preserve indices).
        first_row = rows[0]
        self._model.update_signal(
            first_row,
            name=bus_name,
            width=total_width,
            bus_group=None)

        for row in reversed(rows[1:]):
            self._model.remove_at(row)

    def _ungroup_bus(self):
        """
        Split the selected bus signal (width > 1) into individual
        std_logic signals named name_0 … name_{width-1}.
        """
        rows = self._selected_rows()
        if len(rows) != 1:
            QMessageBox.information(
                self, "Ungroup Bus",
                "Select exactly one bus signal (Width > 1) to split.")
            return

        row = rows[0]
        sig = self._model.signal_at(row)
        if sig.width == 1:
            QMessageBox.information(
                self, "Ungroup Bus",
                f"'{sig.name}' has Width = 1 — nothing to ungroup.")
            return

        direction = sig.direction
        base_name = sig.name
        width     = sig.width

        # Build new scalar signals: MSB first to match original bit order
        new_sigs = [
            Signal(name=f"{base_name}_{i}",
                   direction=direction,
                   width=1,
                   bus_group=None)
            for i in range(width - 1, -1, -1)
        ]

        # Ensure all new names are unique
        for ns in new_sigs:
            candidate = ns.name
            suffix    = 0
            while not self._model.is_name_unique(candidate,
                                                  exclude_index=row):
                suffix   += 1
                candidate = f"{base_name}_{suffix}"
            ns.name = candidate

        # Replace the bus row with the first scalar, insert the rest after
        self._model.update_signal(
            row, name=new_sigs[0].name, width=1, bus_group=None)
        for offset, ns in enumerate(new_sigs[1:], start=1):
            self._model._signals.insert(row + offset, ns)
        # emit one change notification manually since we bypassed update_signal
        self._model.changed.emit()

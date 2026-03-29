"""
widgets/condition_dialog.py
Dialogs for editing condition labels on Diamond and Hexagon blocks.

DiamondConditionDialog  — one input signal dropdown + Y/N state combos
HexagonConditionDialog  — list of input signals, exit labels, state combos
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QComboBox, QLabel, QDialogButtonBox, QLineEdit,
    QGroupBox, QScrollArea, QWidget, QPushButton
)
from PyQt6.QtCore import Qt
from i18n import tr


class DiamondConditionDialog(QDialog):
    """
    Edit a single-input decision diamond:
      - Dropdown to pick the input signal being tested
      - Y → state combo
      - N → state combo
    """

    def __init__(self, condition: str,
                 yes_state: str, no_state: str,
                 input_signals: list[str],
                 state_names: list[str],
                 parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr("dlg_edit_condition"))
        self.setMinimumWidth(300)
        layout = QFormLayout(self)

        # Condition signal
        self._cond = QComboBox()
        self._cond.setEditable(True)
        self._cond.addItems(input_signals)
        if condition:
            self._cond.setCurrentText(condition)
        elif input_signals:
            self._cond.setCurrentIndex(0)
        layout.addRow(tr("dlg_test_signal"), self._cond)

        # Y → state
        self._yes = QComboBox()
        self._yes.addItem("—")
        self._yes.addItems(state_names)
        if yes_state in state_names:
            self._yes.setCurrentText(yes_state)
        layout.addRow(tr("dlg_if_true"), self._yes)

        # N → state
        self._no = QComboBox()
        self._no.addItem("—")
        self._no.addItems(state_names)
        if no_state in state_names:
            self._no.setCurrentText(no_state)
        layout.addRow(tr("dlg_if_false"), self._no)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    def result(self) -> tuple[str, str, str]:
        """Returns (condition, yes_state, no_state)."""
        cond = self._cond.currentText().strip()
        yes  = self._yes.currentText()
        no   = self._no.currentText()
        return (cond,
                yes if yes != "—" else "",
                no  if no  != "—" else "")


class HexagonConditionDialog(QDialog):
    """
    Edit a multi-input decision hexagon:
      - Text field for the condition variables (e.g. "a, b")
      - Per-exit state dropdown (exits defined at creation time)
    """

    def __init__(self, condition_vars: str,
                 exits: list[dict],
                 state_names: list[str],
                 parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr("dlg_edit_hex_condition"))
        self.setMinimumWidth(340)
        layout = QVBoxLayout(self)

        # Condition vars
        form = QFormLayout()
        self._vars = QLineEdit(condition_vars)
        self._vars.setPlaceholderText(tr("hint_vars_placeholder"))
        form.addRow(tr("dlg_condition_vars"), self._vars)
        layout.addLayout(form)

        # Per-exit combos
        grp = QGroupBox(tr("dlg_exit_targets"))
        grp_layout = QFormLayout(grp)
        self._exit_combos: list[QComboBox] = []

        for ex in exits:
            combo = QComboBox()
            combo.addItem("—")
            combo.addItems(state_names)
            state = ex.get("state", "")
            if state in state_names:
                combo.setCurrentText(state)
            grp_layout.addRow(f"Exit  \"{ex.get('label','?')}\"  →", combo)
            self._exit_combos.append(combo)

        layout.addWidget(grp)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self._exits = exits   # keep original for label reference

    def result_vars(self) -> str:
        return self._vars.text().strip()

    def result_exits(self) -> list[dict]:
        result = []
        for i, combo in enumerate(self._exit_combos):
            t = combo.currentText()
            result.append({
                "label": self._exits[i].get("label", ""),
                "state": t if t != "—" else ""
            })
        return result


class UnconditionalDialog(QDialog):
    """
    Simple dialog to pick the single target state for an
    unconditional transition.
    """

    def __init__(self, state_names: list[str], parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr("dlg_uncond_title"))
        self.setMinimumWidth(260)
        layout = QFormLayout(self)

        layout.addRow(QLabel(tr("dlg_uncond_always")))
        self._combo = QComboBox()
        self._combo.addItem("—")
        self._combo.addItems(state_names)
        layout.addRow(tr("dlg_next_state"), self._combo)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    def result_state(self) -> str:
        t = self._combo.currentText()
        return t if t != "—" else ""

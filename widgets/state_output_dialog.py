"""
widgets/state_output_dialog.py
Dialog for editing Moore outputs assigned to a state block.

Scalars (std_logic width=1) → checkbox  (ticked = asserted '1')
Buses   (width > 1)         → QLineEdit with bit-width hint
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QCheckBox, QLineEdit, QLabel, QDialogButtonBox,
    QGroupBox, QScrollArea, QWidget, QSizePolicy
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from i18n import tr


class StateOutputDialog(QDialog):
    """
    Shows one row per output signal:
      - std_logic   → QCheckBox  (checked = '1')
      - std_logic_vector → QLineEdit  (e.g. "101", validated for width)

    Initialised from the current outputs string and a list of
    (name, width) tuples from the signal model.
    """

    def __init__(self, state_name: str,
                 outputs_text: str,
                 output_signals: list[tuple[str, int]],
                 parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr("dlg_outputs_title") + f" {state_name}")
        self.setMinimumWidth(320)

        # Parse current outputs_text into a dict {name: value_or_True}
        current = _parse_outputs(outputs_text, output_signals)

        layout = QVBoxLayout(self)

        if not output_signals:
            layout.addWidget(QLabel(
                tr("dlg_no_outputs")))
        else:
            hint = QLabel(tr("dlg_outputs_hint"))
            hint.setStyleSheet("color: #555; font-size: 10px;")
            hint.setWordWrap(True)
            layout.addWidget(hint)

            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll.setFrameShape(QScrollArea.Shape.NoFrame)
            inner = QWidget()
            form  = QFormLayout(inner)
            form.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)
            scroll.setWidget(inner)
            layout.addWidget(scroll)

            self._scalars: dict[str, QCheckBox] = {}
            self._buses:   dict[str, QLineEdit] = {}

            for name, width in output_signals:
                if width == 1:
                    cb = QCheckBox()
                    cb.setChecked(current.get(name, False) is True or
                                  current.get(name) == "'1'")
                    form.addRow(f"{name}  (std_logic)", cb)
                    self._scalars[name] = cb
                else:
                    le = QLineEdit()
                    le.setPlaceholderText(tr("hint_bus_pattern").format(width, "0"*width))
                    le.setMaxLength(width)
                    val = current.get(name, "")
                    if isinstance(val, str):
                        # strip surrounding quotes
                        le.setText(val.strip('"\''))
                    form.addRow(f"{name}  (std_logic_vector {width-1}:0)", le)
                    self._buses[name] = le

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def result_text(self) -> str:
        """
        Return the outputs string in the canonical format understood
        by _collect_output_signals:
          - Scalar names listed if checked  (e.g. "z")
          - Bus assignments if non-empty    (e.g. "addr = \"101\"")
        """
        parts = []
        for name, cb in self._scalars.items():
            if cb.isChecked():
                parts.append(name)
        for name, le in self._buses.items():
            val = le.text().strip()
            if val:
                parts.append(f'{name} = "{val}"')
        return "\n".join(parts)


def _parse_outputs(text: str,
                   output_signals: list[tuple[str, int]]) -> dict:
    """
    Parse an outputs string back into {name: True_or_value} for pre-filling.
    """
    import re
    result = {}
    if not text or text in ("list outputs\ne.g.: z, y", "(outputs)"):
        return result

    bus_re = re.compile(r'(\w+)\s*(?:<=|=)\s*["\']([01XxZz\-]+)["\']')
    for m in bus_re.finditer(text):
        result[m.group(1).strip()] = m.group(2).strip()

    clean  = bus_re.sub(" ", text)
    tokens = re.split(r'[\s,;]+', clean)
    for t in tokens:
        t = t.strip()
        if t:
            result[t] = True
    return result

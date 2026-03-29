"""
widgets/truth_table_widget.py
Promoted widget: QTableView with a two-row header that shows bus group spans.
"""


from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QTableView, QHeaderView,
    QAbstractItemView, QStyledItemDelegate, QStyleOptionViewItem,
    QComboBox
)
from PyQt6.QtCore import Qt, QModelIndex, QRect, QSize
from PyQt6.QtGui import QPainter, QColor, QFont, QPen, QBrush


# ── delegate: cycle 0 → 1 → X on single click / keyboard ─────────────── #

class CellDelegate(QStyledItemDelegate):
    """Single-click cycles output cells through 0 → 1 → X → 0."""

    CYCLE = {"0": "1", "1": "X", "X": "0"}

    def createEditor(self, parent, option, index):
        # Use a combo instead of a line editor for clean UX
        combo = QComboBox(parent)
        combo.addItems(["0", "1", "X"])
        return combo

    def setEditorData(self, editor, index):
        val = index.data(Qt.ItemDataRole.EditRole) or "0"
        editor.setCurrentText(val)

    def setModelData(self, editor, model, index):
        model.setData(index, editor.currentText(), Qt.ItemDataRole.EditRole)

    def paint(self, painter, option, index):
        super().paint(painter, option, index)

    def sizeHint(self, option, index):
        return QSize(36, 22)


# ── custom horizontal header that draws bus-group spans ───────────────── #

class SpanHeaderView(QHeaderView):
    """
    Two-row header:
      Row 0 (top)    — bus group labels spanning multiple columns
      Row 1 (bottom) — individual bit / signal names
    For columns that belong to no bus group, row 0 is empty and
    the label is shown only in row 1 (normal height).
    """

    GROUP_H = 18   # height of the group-label row (px)

    def __init__(self, parent=None):
        super().__init__(Qt.Orientation.Horizontal, parent)
        self._spans: list[dict] = []
        self.setDefaultAlignment(Qt.AlignmentFlag.AlignCenter)

    def set_spans(self, spans: list[dict]):
        self._spans = spans
        self.viewport().update()

    def sizeHint(self) -> QSize:
        base = super().sizeHint()
        return QSize(base.width(), base.height() + self.GROUP_H)

    def paintSection(self, painter: QPainter, rect: QRect, logical_index: int):
        # Shift the normal header label down by GROUP_H
        shifted = QRect(rect.x(), rect.y() + self.GROUP_H,
                        rect.width(), rect.height() - self.GROUP_H)
        painter.save()
        super().paintSection(painter, shifted, logical_index)
        painter.restore()

    def paintEvent(self, event):
        super().paintEvent(event)
        if not self._spans:
            return
        painter = QPainter(self.viewport())
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        for span in self._spans:
            first = span["first_col"]
            last  = span["last_col"]
            label = span["label"]
            is_in = span["is_input"]

            x1 = self.sectionViewportPosition(first)
            x2 = self.sectionViewportPosition(last) + self.sectionSize(last)
            rect = QRect(x1 + 1, 0, x2 - x1 - 2, self.GROUP_H)

            bg = QColor("#b3c8fd") if is_in else QColor("#fde7a0")
            painter.fillRect(rect, bg)

            pen = QPen(QColor("#555555"))
            pen.setWidth(1)
            painter.setPen(pen)
            painter.drawRect(rect)

            f = QFont("Arial", 8, QFont.Weight.Bold)
            painter.setFont(f)
            painter.setPen(QColor("#1a1a1a"))
            painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, label)

        painter.end()


# ── main widget ───────────────────────────────────────────────────────── #

class TruthTableWidget(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self._header = SpanHeaderView(self)
        self._view   = QTableView()
        self._view.setHorizontalHeader(self._header)
        self._view.setItemDelegate(CellDelegate(self._view))
        self._view.verticalHeader().setDefaultSectionSize(22)
        self._view.verticalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Fixed)
        self._view.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.ResizeToContents)
        self._view.setSelectionMode(
            QAbstractItemView.SelectionMode.ContiguousSelection)
        self._view.setAlternatingRowColors(True)
        self._view.setEditTriggers(
            QAbstractItemView.EditTrigger.DoubleClicked |
            QAbstractItemView.EditTrigger.SelectedClicked
        )
        layout.addWidget(self._view)

    def set_model(self, model):
        self._view.setModel(model)
        model.structure_changed.connect(self._on_structure_changed)
        self._on_structure_changed()

    def _on_structure_changed(self):
        model = self._view.model()
        if model is None:
            return
        self._header.set_spans(model.span_info())
        # Make input columns narrower / non-interactive visually
        n_in = model._n_input_bits
        for c in range(model.columnCount()):
            if c < n_in:
                self._view.setColumnWidth(c, 36)

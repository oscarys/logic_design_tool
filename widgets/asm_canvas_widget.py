"""
widgets/asm_canvas_widget.py
Promoted widget: QGraphicsScene/View hosting the ASM chart.

Responsibilities
----------------
- Manage placement tool state (select / state only — conditions added via state blocks)
- Handle mouse clicks on the canvas to place state blocks
- Maintain the SceneSignals hub and broadcast state-name changes
- Manage optional arrow overlay ("Show connections" toggle)
- Provide get_asm_data() for the VHDL generator
- HexagonConfigDialog: used by StateItem._spawn_hexagon
"""


from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGraphicsView, QGraphicsScene,
    QDialog, QFormLayout, QLineEdit, QComboBox,
    QDialogButtonBox, QLabel, QCheckBox
)
from PyQt6.QtCore import Qt, QPointF
from PyQt6.QtGui import QColor, QPainter

from widgets.asm_items import (
    SceneSignals, StateItem, DiamondItem, HexagonItem,
    ArrowItem, snap_point, GRID
)
from i18n import tr, theme_color


# ── hexagon config dialog ─────────────────────────────────────────────── #
class HexagonConfigDialog(QDialog):
    """
    Ask the user the exit mode for a multi-input decision hexagon.
    The number of variables is inferred from the vars field (count commas+1).
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr("dlg_hex_config"))
        layout = QFormLayout(self)

        self._vars_edit = QLineEdit()
        self._vars_edit.setPlaceholderText(tr("hint_vars_placeholder"))
        layout.addRow(tr("dlg_hex_vars"), self._vars_edit)

        self._mode_combo = QComboBox()
        self._mode_combo.addItems([
            tr("dlg_hex_minterms"),
            tr("dlg_hex_custom")
        ])
        layout.addRow(tr("dlg_hex_mode"), self._mode_combo)

        self._custom_labels = QLineEdit()
        self._custom_labels.setPlaceholderText(tr("hint_custom_labels"))
        self._custom_labels.setEnabled(False)
        layout.addRow(tr("dlg_hex_custom_labels"), self._custom_labels)

        self._mode_combo.currentIndexChanged.connect(
            lambda i: self._custom_labels.setEnabled(i == 1))

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    def result_exits(self) -> tuple[str, list[dict]]:
        """Returns (vars_string, [{"label": ..., "state": ""}, ...])"""
        vars_str  = self._vars_edit.text().strip()
        var_names = [v.strip() for v in vars_str.split(",") if v.strip()]

        if self._mode_combo.currentIndex() == 0:
            # Minterm mode — total bits = sum of widths across all variables
            # Width comes from the hub's input signal list if available
            width_map = {name: w
                         for name, w in getattr(self, '_input_widths', [])}
            total_bits = sum(width_map.get(v, 1) for v in var_names)
            total_bits = max(1, min(total_bits, 8))  # clamp 1..8 (256 max)
            # Build labels: for each minterm, split bits back per variable
            exits = []
            for i in range(2 ** total_bits):
                bits = format(i, f"0{total_bits}b")
                # Group bits back per variable width for readable labels
                label_parts = []
                pos = 0
                for v in var_names:
                    w = width_map.get(v, 1)
                    label_parts.append(bits[pos:pos + w])
                    pos += w
                exits.append({"label": " ".join(label_parts), "state": ""})
        else:
            raw    = self._custom_labels.text()
            labels = [l.strip() for l in raw.split(",") if l.strip()]
            exits  = [{"label": l, "state": ""} for l in labels]

        return vars_str, exits


# ── canvas scene ──────────────────────────────────────────────────────── #
class AsmScene(QGraphicsScene):
    def __init__(self, hub: SceneSignals, parent=None):
        super().__init__(parent)
        self._hub        = hub
        self._active_tool = "select"
        self._arrows: list[ArrowItem] = []
        self._show_arrows = False
        self.setBackgroundBrush(QColor(theme_color("canvas_bg")))

    def set_tool(self, tool: str):
        self._active_tool = tool

    def mousePressEvent(self, event):
        if (self._active_tool == "select" or
                event.button() != Qt.MouseButton.LeftButton):
            super().mousePressEvent(event)
            return

        pos = snap_point(event.scenePos())
        item = self._place_item(self._active_tool, pos)
        if item:
            self.addItem(item)
            self._emit_state_list()
        super().mousePressEvent(event)

    def _place_item(self, tool: str, pos: QPointF):
        if tool == "state":
            n = sum(1 for it in self.items() if isinstance(it, StateItem))
            item = StateItem(self._hub, name=f"S{n}")
            item.setPos(pos)
            return item
        return None

    def _emit_state_list(self):
        names = [it.name() for it in self.items()
                 if isinstance(it, StateItem)]
        self._hub.state_list_changed.emit(names)
        # Notify dirty tracker of structural change
        if hasattr(self._hub, '_dirty_tracker'):
            self._hub._dirty_tracker.mark_dirty()

    def delete_selected(self):
        from widgets.asm_items import BaseAsmItem, StateItem
        to_remove = [it for it in self.selectedItems()
                     if isinstance(it, StateItem)]
        for item in to_remove:
            # Clean up owned condition block and connection line first
            item._remove_condition()
            self.removeItem(item)
        if to_remove:
            self._emit_state_list()

    # ── arrow overlay ─────────────────────────────────────────────────── #
    def set_show_arrows(self, show: bool):
        self._show_arrows = show
        self._rebuild_arrows()

    def _rebuild_arrows(self):
        # Remove old arrows
        for a in self._arrows:
            self.removeItem(a)
        self._arrows.clear()

        if not self._show_arrows:
            return

        state_map = {it.name(): it for it in self.items()
                     if isinstance(it, StateItem)}

        def add_arrow(src_item, dst_name: str, label: str = ""):
            if not dst_name or dst_name not in state_map:
                return
            dst_item = state_map[dst_name]
            # source = bottom centre, dest = top centre
            sr = src_item.boundingRect()
            dr = dst_item.boundingRect()
            p1 = src_item.mapToScene(
                QPointF(sr.width() / 2, sr.height()))
            p2 = dst_item.mapToScene(
                QPointF(dr.width() / 2, 0))
            arrow = ArrowItem(p1, p2, label)
            self.addItem(arrow)
            self._arrows.append(arrow)

        for it in self.items():
            if isinstance(it, StateItem):
                add_arrow(it, it.next_state())
            elif isinstance(it, DiamondItem):
                add_arrow(it, it.yes_state(), "Y")
                add_arrow(it, it.no_state(),  "N")
            elif isinstance(it, HexagonItem):
                for ex in it.exits():
                    add_arrow(it, ex["state"], ex["label"])

    # ── data export ───────────────────────────────────────────────────── #
    def get_asm_data(self) -> dict:
        """Return all block data for the VHDL generator."""
        states = []
        from widgets.asm_items import UnconditionalItem
        for it in self.items():
            if isinstance(it, StateItem):
                d = it.to_dict()
                d["is_initial"] = it.is_initial()
                cb = it.condition_block()
                if isinstance(cb, UnconditionalItem):
                    d["condition"] = {
                        "type":       "unconditional",
                        "next_state": cb.next_state(),
                    }
                elif isinstance(cb, DiamondItem):
                    d["condition"] = {
                        "type":      "diamond",
                        "condition": cb.condition(),
                        "yes_state": cb.yes_state(),
                        "no_state":  cb.no_state(),
                    }
                elif isinstance(cb, HexagonItem):
                    d["condition"] = {
                        "type":           "hexagon",
                        "condition_vars": cb.condition_vars(),
                        "exits":          cb.exits(),
                    }
                states.append(d)
        return {"states": states, "decisions": [], "hexagons": []}

    def get_state_names(self) -> list[str]:
        return [it.name() for it in self.items()
                if isinstance(it, StateItem)]


# ── canvas widget ─────────────────────────────────────────────────────── #
class ASMCanvasWidget(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self._hub  = SceneSignals()
        self._scene = AsmScene(self._hub)
        self._scene.setSceneRect(-2000, -2000, 4000, 4000)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ── mini toolbar ──
        tb = QHBoxLayout()
        self._chk_arrows = QCheckBox(tr("lbl_show_connections"))
        self._chk_arrows.toggled.connect(self._scene.set_show_arrows)
        tb.addWidget(self._chk_arrows)
        tb.addStretch()
        self._lbl_tool = QLabel(tr("lbl_tool_prefix") + " select")
        self._lbl_tool.setStyleSheet("color:#555; font-size:10px;")
        tb.addWidget(self._lbl_tool)
        layout.addLayout(tb)

        # ── view ──
        self._view = QGraphicsView(self._scene)
        self._view.setRenderHint(QPainter.RenderHint.Antialiasing)
        self._view.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
        self._view.setTransformationAnchor(
            QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self._view.setResizeAnchor(
            QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self._view.setInteractive(True)
        self._view.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        layout.addWidget(self._view)

        # Draw grid
        self._draw_grid()

        # Install key handler
        self._view.installEventFilter(self)

    def _draw_grid(self):
        """Draw a subtle dot grid on the scene background."""
        from PyQt6.QtGui import QPixmap
        size = GRID
        pix = QPixmap(size, size)
        pix.fill(QColor(theme_color("canvas_bg")))
        from PyQt6.QtGui import QPainter as P
        p = P(pix)
        p.setPen(QColor("#dddddd"))
        p.drawPoint(0, 0)
        p.end()
        from PyQt6.QtGui import QBrush
        self._scene.setBackgroundBrush(QBrush(pix))

    # ── public API ────────────────────────────────────────────────────── #
    def set_tool(self, tool: str):
        self._scene.set_tool(tool)
        self._lbl_tool.setText(tr("lbl_tool_prefix") + f" {tool}")
        self._view.setDragMode(
            QGraphicsView.DragMode.RubberBandDrag
            if tool == "select" else
            QGraphicsView.DragMode.NoDrag)

    def delete_selected(self):
        self._scene.delete_selected()

    def get_asm_data(self) -> dict:
        return self._scene.get_asm_data()

    def get_state_names(self) -> list[str]:
        return self._scene.get_state_names()

    def refresh_arrows(self):
        self._scene._rebuild_arrows()

    def retranslate_ui(self):
        self._chk_arrows.setText(tr("lbl_show_connections"))
        current = self._scene._active_tool
        self._lbl_tool.setText(tr("lbl_tool_prefix") + f" {current}")

    # ── intercept key + mouse events ─────────────────────────────────── #
    def eventFilter(self, obj, event):
        from PyQt6.QtCore import QEvent
        from PyQt6.QtGui import QKeyEvent

        # Delete / Backspace key → delete selected items
        if (obj is self._view and
                event.type() == QEvent.Type.KeyPress):
            key = event.key()
            if key in (Qt.Key.Key_Delete, Qt.Key.Key_Backspace):
                self._scene.delete_selected()
                return True

        return super().eventFilter(obj, event)

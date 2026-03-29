"""
widgets/asm_items.py
QGraphicsItem subclasses for the ASM chart canvas.

Block types
-----------
StateItem    – rectangle: name + outputs + optional condition block + next-state fallback
DiamondItem  – diamond: single-input condition (owned by a StateItem)
HexagonItem  – hexagon: multi-input condition (owned by a StateItem)
ArrowItem    – orthogonal connection line (state → condition, optional show-connections)

Ownership model
---------------
Each StateItem may own one condition block (DiamondItem or HexagonItem).
The condition block is an independent QGraphicsItem positioned snapped below
the state. When the state moves, it repositions its condition block.
A connecting line is drawn between them.
"""

import math
from i18n import tr, theme_color
from PyQt6.QtWidgets import (
    QGraphicsItem, QGraphicsTextItem, QGraphicsProxyWidget,
    QGraphicsLineItem, QComboBox, QMenu
)
from PyQt6.QtCore import Qt, QRectF, QPointF, pyqtSignal, QObject
from PyQt6.QtGui import (
    QPen, QBrush, QColor, QPolygonF, QPainter, QFont
)

GRID = 20

# ── colours ───────────────────────────────────────────────────────────── #
CLR_STATE_BG    = QColor("#dce8fb")
CLR_STATE_HDR   = QColor("#4a90d9")
CLR_OUTPUT_BG   = QColor("#fffbe6")
CLR_DIAMOND_BG  = QColor("#e8f8e8")
CLR_HEXAGON_BG  = QColor("#fce8fb")
CLR_TEXT        = QColor("#1a1a1a")
CLR_HINT        = QColor("#aaaaaa")
CLR_CONNECT     = QColor("#555555")

PEN_NORMAL   = QPen(QColor("#555555"), 1.5)
PEN_SELECTED = QPen(QColor("#ff6600"), 2.5)
PEN_CONNECT  = QPen(QColor("#555555"), 1.5, Qt.PenStyle.SolidLine)

FONT_TITLE = QFont("Arial", 9, QFont.Weight.Bold)
FONT_BODY  = QFont("Arial", 8)
FONT_SMALL = QFont("Arial", 7)

GAP = 20   # vertical gap between state bottom and condition block top


def snap(v: float) -> float:
    return round(v / GRID) * GRID

def snap_point(pt: QPointF) -> QPointF:
    return QPointF(snap(pt.x()), snap(pt.y()))


# ── scene signals hub ─────────────────────────────────────────────────── #
class SceneSignals(QObject):
    state_list_changed = pyqtSignal(list)
    item_selected      = pyqtSignal(object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._output_signals: list[tuple[str, int]] = []
        self._input_signals:  list[str] = []
        self._input_signals_with_width: list[tuple[str, int]] = []
        self._dirty_tracker = None  # set by MainWindow after construction


# ── proxy combo helper ─────────────────────────────────────────────────── #
def _make_proxy_combo(parent_item, choices: list[str],
                      current: str = "") -> QGraphicsProxyWidget:
    combo = QComboBox()
    combo.addItem("—")
    combo.addItems(choices)
    if current and current in choices:
        combo.setCurrentText(current)
    combo.setFixedWidth(110)
    combo.setFixedHeight(22)
    combo.setFont(FONT_SMALL)
    combo.setStyleSheet("QComboBox { background: white; font-size: 10px; }")
    proxy = QGraphicsProxyWidget(parent_item)
    proxy.setWidget(combo)
    return proxy


# ══════════════════════════════════════════════════════════════════════════
# BASE ITEM
# ══════════════════════════════════════════════════════════════════════════
class BaseAsmItem(QGraphicsItem):
    def __init__(self, signals_hub: SceneSignals):
        super().__init__()
        self._hub = signals_hub
        self.setFlags(
            QGraphicsItem.GraphicsItemFlag.ItemIsMovable |
            QGraphicsItem.GraphicsItemFlag.ItemIsSelectable |
            QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges
        )
        self.setZValue(1)

    def itemChange(self, change, value):
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionChange:
            return snap_point(value)
        return super().itemChange(change, value)

    def _pen(self):
        return QPen(QColor(theme_color("pen_selected")), 2.5) if self.isSelected() else QPen(QColor(theme_color("pen_normal")), 1.5)

    def _lock(self):
        """Disable move and selection — for condition blocks owned by a state."""
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable,    False)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, False)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges, False)

    def block_type(self) -> str:
        return "base"

    def to_dict(self) -> dict:
        return {"type": self.block_type(), "x": self.x(), "y": self.y()}


# ══════════════════════════════════════════════════════════════════════════
# CONNECT LINE  (state → condition block)
# ══════════════════════════════════════════════════════════════════════════
class ConnectLine(QGraphicsItem):
    """Simple vertical line from state bottom-centre to condition top-centre."""

    def __init__(self):
        super().__init__()
        self._p1 = QPointF(0, 0)
        self._p2 = QPointF(0, 0)
        self.setZValue(0)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, False)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable,    False)

    def update_points(self, p1: QPointF, p2: QPointF):
        self.prepareGeometryChange()
        self._p1, self._p2 = p1, p2

    def boundingRect(self) -> QRectF:
        x1,y1 = self._p1.x(), self._p1.y()
        x2,y2 = self._p2.x(), self._p2.y()
        return QRectF(min(x1,x2)-2, min(y1,y2)-2,
                      abs(x2-x1)+4, abs(y2-y1)+4)

    def paint(self, painter: QPainter, option, widget=None):
        painter.setPen(QPen(QColor(theme_color("pen_connect")), 1.5))
        painter.drawLine(self._p1, self._p2)
        # Small arrowhead at p2
        painter.setBrush(QBrush(QColor(theme_color("pen_connect"))))
        aw = 5
        arr = QPolygonF([
            self._p2,
            QPointF(self._p2.x() - aw/2, self._p2.y() - aw),
            QPointF(self._p2.x() + aw/2, self._p2.y() - aw),
        ])
        painter.drawPolygon(arr)


# ══════════════════════════════════════════════════════════════════════════
# STATE ITEM
# ══════════════════════════════════════════════════════════════════════════
class StateItem(BaseAsmItem):
    W, H = 160, 90

    def __init__(self, signals_hub: SceneSignals,
                 name: str = "S0", outputs: str = "",
                 is_initial: bool = False):
        super().__init__(signals_hub)
        self._name        = name
        self._outputs     = outputs
        self._is_initial  = is_initial
        self._sim_highlight = False
        self._cond_block: DiamondItem | HexagonItem | None = None
        self._conn_line:  ConnectLine | None = None

        self._proxy_add:  QGraphicsProxyWidget | None = None
        self._build_internals()

    # ── construction ──────────────────────────────────────────────────── #
    def _build_internals(self):
        # Name (inline editable)
        self._name_item = QGraphicsTextItem(self._name, self)
        self._name_item.setFont(FONT_TITLE)
        self._name_item.setDefaultTextColor(QColor(theme_color("state_text")))
        self._name_item.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextEditorInteraction)
        self._name_item.setPos(6, 4)
        self._name_item.document().contentsChanged.connect(
            self._on_name_changed)

        # Output area (read-only label, click opens dialog)
        self._out_item = QGraphicsTextItem("", self)
        self._out_item.setFont(FONT_BODY)
        self._out_item.setTextInteractionFlags(
            Qt.TextInteractionFlag.NoTextInteraction)
        self._out_item.setPos(6, 28)
        self._out_item.setTextWidth(self.W - 12)
        self._refresh_output_display()

        # tr("state_add_condition") button
        from PyQt6.QtWidgets import QPushButton
        self._add_btn = QPushButton(tr("state_add_condition"))
        self._add_btn.setFixedHeight(20)
        self._add_btn.setStyleSheet(
            "QPushButton { font-size:9px; background:#e8f0fe; "
            "border:1px solid #99b4ee; border-radius:3px; }"
            "QPushButton:hover { background:#c2d4f8; }")
        self._add_btn.clicked.connect(self._on_add_condition)
        self._proxy_add = QGraphicsProxyWidget(self)
        self._proxy_add.setWidget(self._add_btn)
        self._proxy_add.setPos(6, self.H - 26)
        self._proxy_add.resize(self.W - 12, 20)

    # ── output display ─────────────────────────────────────────────────── #
    def _refresh_output_display(self):
        if self._outputs and self._outputs.strip():
            self._out_item.setPlainText(self._outputs)
            self._out_item.setDefaultTextColor(QColor(theme_color("cond_text")))
        else:
            self._out_item.setPlainText(tr("state_click_outputs"))
            self._out_item.setDefaultTextColor(QColor(theme_color("cond_hint")))

    # ── condition block management ─────────────────────────────────────── #
    def _on_add_condition(self):
        if self._cond_block is not None:
            self._show_condition_menu()
            return
        self._show_add_condition_dialog()

    def _show_condition_menu(self):
        """Menu when condition block already exists."""
        menu = QMenu()
        menu.addAction(tr("state_edit_cond_menu"),  self._edit_condition)
        menu.addAction(tr("state_remove_cond_menu"), self._remove_condition)
        view = self.scene().views()[0] if self.scene() and self.scene().views() else None
        btn_scene_pos = self.mapToScene(
            QPointF(6, self.H - 26))
        if view:
            screen_pos = view.mapToGlobal(
                view.mapFromScene(btn_scene_pos))
            menu.exec(screen_pos)
        else:
            menu.exec()

    def _show_add_condition_dialog(self):
        from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QRadioButton,
                                     QDialogButtonBox, QLabel)
        view = self.scene().views()[0] if self.scene() and self.scene().views() else None
        dlg = QDialog(view)
        dlg.setWindowTitle(tr("dlg_add_transition"))
        layout = QVBoxLayout(dlg)
        layout.addWidget(QLabel(tr("dlg_transition_type")))
        rb_uncond  = QRadioButton(tr("dlg_uncond"))
        rb_diamond = QRadioButton(tr("dlg_single_input"))
        rb_hexagon = QRadioButton(tr("dlg_multi_input"))
        rb_uncond.setChecked(True)
        layout.addWidget(rb_uncond)
        layout.addWidget(rb_diamond)
        layout.addWidget(rb_hexagon)
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(dlg.accept)
        buttons.rejected.connect(dlg.reject)
        layout.addWidget(buttons)
        if dlg.exec():
            if rb_uncond.isChecked():
                self._spawn_unconditional()
            elif rb_diamond.isChecked():
                self._spawn_diamond()
            else:
                self._spawn_hexagon()

    def _spawn_unconditional(self):
        """Simple unconditional transition — uses a single-exit 'arrow' block."""
        from widgets.condition_dialog import UnconditionalDialog
        view = self.scene().views()[0] if self.scene() and self.scene().views() else None
        state_names = self._other_state_names()
        dlg = UnconditionalDialog(state_names, view)
        if dlg.exec():
            next_s = dlg.result_state()
            if next_s:
                block = UnconditionalItem(self._hub, next_s)
                self._attach_condition(block)

    def _spawn_diamond(self):
        from widgets.condition_dialog import DiamondConditionDialog
        view = self.scene().views()[0] if self.scene() and self.scene().views() else None
        state_names = self._other_state_names()
        input_sigs  = getattr(self._hub, '_input_signals', [])
        dlg = DiamondConditionDialog("", "", "", input_sigs, state_names, view)
        if dlg.exec():
            cond, yes, no = dlg.result()
            block = DiamondItem(self._hub, cond, yes, no)
            self._attach_condition(block)
            block._refresh_exit_labels()

    def _spawn_hexagon(self):
        from widgets.asm_canvas_widget import HexagonConfigDialog
        view = self.scene().views()[0] if self.scene() and self.scene().views() else None
        dlg = HexagonConfigDialog(view)
        # Pass input signal widths so bus variables generate correct exit counts
        dlg._input_widths = getattr(self._hub, '_input_signals_with_width', [])
        if dlg.exec():
            vars_str, exits = dlg.result_exits()
            block = HexagonItem(self._hub, vars_str, exits)
            self._attach_condition(block)

    def _attach_condition(self, block):
        """Add block to scene, snap below self, draw connection line."""
        self.scene().addItem(block)
        self._cond_block = block
        block._owner_state = self
        # Refresh labels now that owner is known (enables (self) annotation)
        if hasattr(block, '_refresh_exit_labels'):
            block._refresh_exit_labels()
        elif hasattr(block, '_refresh_display'):
            block._refresh_display()
        elif hasattr(block, '_build_exit_labels'):
            block._build_exit_labels()
        self._reposition_condition()
        # connection line
        self._conn_line = ConnectLine()
        self.scene().addItem(self._conn_line)
        self._update_conn_line()
        # update button label
        self._add_btn.setText(tr("state_edit_condition"))
        # populate combos with current state names
        names = [it._name for it in self.scene().items()
                 if isinstance(it, StateItem)]
        self._hub.state_list_changed.emit(names)

    def _reposition_condition(self):
        if self._cond_block is None:
            return
        sx, sy = self.x(), self.y()
        cx = sx + self.W / 2 - self._cond_block.W / 2
        cy = sy + self.H + GAP
        self._cond_block.setPos(snap(cx), snap(cy))
        self._update_conn_line()

    def _update_conn_line(self):
        if self._conn_line is None or self._cond_block is None:
            return
        p1 = self.mapToScene(QPointF(self.W / 2, self.H))
        p2 = self._cond_block.mapToScene(
            QPointF(self._cond_block.W / 2, 0))
        self._conn_line.update_points(p1, p2)

    def _edit_condition(self):
        if self._cond_block is None:
            return
        view = self.scene().views()[0] if self.scene() and self.scene().views() else None
        state_names = self._other_state_names()
        if isinstance(self._cond_block, UnconditionalItem):
            from widgets.condition_dialog import UnconditionalDialog
            dlg = UnconditionalDialog(state_names, view)
            if dlg.exec():
                self._cond_block.set_next_state(dlg.result_state())
        elif isinstance(self._cond_block, DiamondItem):
            from widgets.condition_dialog import DiamondConditionDialog
            input_sigs = getattr(self._hub, '_input_signals', [])
            dlg = DiamondConditionDialog(
                self._cond_block._condition,
                self._cond_block.yes_state(),
                self._cond_block.no_state(),
                input_sigs, state_names, view)
            if dlg.exec():
                cond, yes, no = dlg.result()
                self._cond_block._condition = cond
                self._cond_block._refresh_cond_display()
                self._cond_block.set_transitions(yes, no)
        elif isinstance(self._cond_block, HexagonItem):
            from widgets.condition_dialog import HexagonConditionDialog
            dlg = HexagonConditionDialog(
                self._cond_block._condition_vars,
                self._cond_block._exits,
                state_names, view)
            if dlg.exec():
                self._cond_block._condition_vars = dlg.result_vars()
                self._cond_block._refresh_vars_display()
                self._cond_block.set_exits(dlg.result_exits())

    def _remove_condition(self):
        if self._cond_block is None:
            return
        if self._conn_line and self.scene():
            self.scene().removeItem(self._conn_line)
        if self.scene():
            self.scene().removeItem(self._cond_block)
        self._cond_block = None
        self._conn_line  = None
        self._add_btn.setText(tr("state_add_condition"))

    # ── movement — drag condition block along ─────────────────────────── #
    def itemChange(self, change, value):
        result = super().itemChange(change, value)
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
            self._reposition_condition()
            if hasattr(self._hub, '_dirty_tracker') and self._hub._dirty_tracker:
                self._hub._dirty_tracker.mark_dirty()
        return result

    # ── state names helper ──────────────────────────────────────────────── #
    def _other_state_names(self) -> list[str]:
        """All state names including self — self listed first for easy self-loop selection."""
        if self.scene() is None:
            return [self._name]
        names = [it._name for it in self.scene().items()
                 if isinstance(it, StateItem) and it is not self]
        return [self._name] + names  # self first

    def _on_name_changed(self):
        new = self._name_item.toPlainText().strip()
        if new and new != self._name:
            self._name = new
            self._emit_state_list()

    def _emit_state_list(self):
        if self.scene():
            names = [it._name for it in self.scene().items()
                     if isinstance(it, StateItem)]
            self._hub.state_list_changed.emit(names)

    # ── click handlers ─────────────────────────────────────────────────── #
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            # Output area click (between header and next-state row)
            if 26 < event.pos().y() < self.H - 36:
                self._open_output_dialog()
                return
        super().mousePressEvent(event)

    def _open_output_dialog(self):
        output_signals = getattr(self._hub, '_output_signals', [])
        from widgets.state_output_dialog import StateOutputDialog
        view = self.scene().views()[0] if self.scene() and self.scene().views() else None
        dlg = StateOutputDialog(self._name, self._outputs, output_signals, view)
        if dlg.exec():
            self._outputs = dlg.result_text()
            self._refresh_output_display()
            if hasattr(self._hub, '_dirty_tracker') and self._hub._dirty_tracker:
                self._hub._dirty_tracker.mark_dirty()

    # ── initial state ──────────────────────────────────────────────────── #
    def mouseDoubleClickEvent(self, event):
        self._show_context_menu(event.screenPos())

    def contextMenuEvent(self, event):
        self._show_context_menu(event.screenPos())

    def _show_context_menu(self, screen_pos):
        menu = QMenu()
        if self._is_initial:
            action = menu.addAction(tr("state_unset_initial"))
        else:
            action = menu.addAction(tr("state_set_initial"))
        action.triggered.connect(self._toggle_initial)
        menu.exec(screen_pos)

    def _toggle_initial(self):
        if not self._is_initial:
            if self.scene():
                for it in self.scene().items():
                    if isinstance(it, StateItem) and it is not self:
                        it._is_initial = False
                        it._refresh_name_display()
                        it.update()
        self._is_initial = not self._is_initial
        self._refresh_name_display()
        self.update()

    def _refresh_name_display(self):
        if self._is_initial:
            self._name_item.setDefaultTextColor(QColor(theme_color("state_text_init")))
        else:
            self._name_item.setDefaultTextColor(QColor(theme_color("state_text")))

    # ── accessors ──────────────────────────────────────────────────────── #
    def is_initial(self) -> bool:
        return self._is_initial

    def set_sim_highlight(self, active: bool):
        self._sim_highlight = active
        self.update()

    def name(self) -> str:
        return self._name

    def outputs(self) -> str:
        return self._outputs

    def condition_block(self):
        return self._cond_block

    # ── paint ──────────────────────────────────────────────────────────── #
    def boundingRect(self) -> QRectF:
        return QRectF(0, 0, self.W, self.H)

    def paint(self, painter: QPainter, option, widget=None):
        painter.setPen(self._pen())
        painter.setBrush(QBrush(QColor(theme_color("state_bg"))))
        painter.drawRoundedRect(0, 0, self.W, self.H, 6, 6)
        # header
        hdr_color = QColor(theme_color("state_hdr_init")) if self._is_initial else QColor(theme_color("state_hdr"))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(hdr_color))
        painter.drawRoundedRect(0, 0, self.W, 24, 6, 6)
        painter.drawRect(0, 12, self.W, 12)
        # border
        painter.setPen(self._pen())
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRoundedRect(0, 0, self.W, self.H, 6, 6)
        # separator above condition button
        painter.setPen(QPen(QColor("#aaa"), 1, Qt.PenStyle.DashLine))
        painter.drawLine(0, self.H - 30, self.W, self.H - 30)

        # Simulation highlight — amber glow ring
        if self._sim_highlight:
            painter.setPen(QPen(QColor("#ffab00"), 3.5))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRoundedRect(-4, -4, self.W + 8, self.H + 8, 9, 9)

    def to_dict(self) -> dict:
        d = super().to_dict()
        d.update(name=self._name, outputs=self.outputs(),
                 is_initial=self._is_initial)
        return d

    def block_type(self) -> str:
        return "state"


# ══════════════════════════════════════════════════════════════════════════
# UNCONDITIONAL ITEM  (simple direct transition arrow)
# ══════════════════════════════════════════════════════════════════════════
class UnconditionalItem(BaseAsmItem):
    """
    Represents an unconditional transition → next_state.
    Displayed as a small pill/arrow below the state showing "→ StateName".
    """
    W, H = 120, 30

    def __init__(self, signals_hub: SceneSignals, next_state: str = ""):
        super().__init__(signals_hub)
        self._lock()
        self._next_state  = next_state
        self._owner_state = None

        self._lbl = QGraphicsTextItem("", self)
        self._lbl.setFont(FONT_BODY)
        self._lbl.setTextInteractionFlags(
            Qt.TextInteractionFlag.NoTextInteraction)
        self._lbl.setPos(8, 6)
        self._refresh_display()

    def _refresh_display(self):
        owner = getattr(self, "_owner_state", None)
        owner_name = owner._name if owner else None
        if not self._next_state:
            text = "→  —"
        elif self._next_state == owner_name:
            text = f"→  {self._next_state}  (self)"
        else:
            text = f"→  {self._next_state}"
        self._lbl.setPlainText(text)
        self._lbl.setDefaultTextColor(QColor(theme_color("cond_text")))

    def set_next_state(self, state: str):
        self._next_state = state
        self._refresh_display()

    def next_state(self) -> str:
        return self._next_state

    def boundingRect(self) -> QRectF:
        return QRectF(0, 0, self.W, self.H)

    def paint(self, painter: QPainter, option, widget=None):
        painter.setPen(self._pen())
        painter.setBrush(QBrush(QColor(theme_color("cond_uncond_bg"))))
        painter.drawRoundedRect(0, 0, self.W, self.H, 8, 8)

    def block_type(self) -> str:
        return "unconditional"

    def to_dict(self) -> dict:
        d = super().to_dict()
        d["next_state"] = self._next_state
        return d


# ══════════════════════════════════════════════════════════════════════════
# DIAMOND ITEM
# ══════════════════════════════════════════════════════════════════════════
class DiamondItem(BaseAsmItem):
    W, H = 140, 90

    def __init__(self, signals_hub: SceneSignals,
                 condition: str = "",
                 yes_state: str = "", no_state: str = ""):
        super().__init__(signals_hub)
        self._lock()
        self._condition  = condition
        self._yes_state  = yes_state
        self._no_state   = no_state
        self._owner_state = None   # set by StateItem._attach_condition

        # Read-only condition label (centred)
        self._cond_item = QGraphicsTextItem("", self)
        self._cond_item.setFont(FONT_BODY)
        self._cond_item.setTextInteractionFlags(
            Qt.TextInteractionFlag.NoTextInteraction)
        self._cond_item.setTextWidth(self.W)
        from PyQt6.QtGui import QTextOption
        self._cond_item.document().setDefaultTextOption(
            QTextOption(Qt.AlignmentFlag.AlignCenter))
        self._cond_item.setPos(0, self.H / 2 - 16)
        self._refresh_cond_display()

        # Y → read-only label (right exit)
        self._yes_lbl = QGraphicsTextItem("", self)
        self._yes_lbl.setFont(FONT_SMALL)
        self._yes_lbl.setPos(self.W + 4, self.H / 2 - 8)
        self._yes_lbl.setDefaultTextColor(QColor(theme_color("exit_yes")))

        # N ↓ read-only label (bottom exit)
        self._no_lbl = QGraphicsTextItem("", self)
        self._no_lbl.setFont(FONT_SMALL)
        self._no_lbl.setPos(self.W / 2 - 30, self.H + 4)
        self._no_lbl.setDefaultTextColor(QColor(theme_color("exit_no")))

        self._refresh_exit_labels()

    def _refresh_cond_display(self):
        if self._condition and self._condition.strip():
            self._cond_item.setPlainText(self._condition)
            self._cond_item.setDefaultTextColor(QColor(theme_color("cond_text")))
        else:
            self._cond_item.setPlainText(tr("cond_click_to_edit"))
            self._cond_item.setDefaultTextColor(QColor(theme_color("cond_hint")))

    def _refresh_exit_labels(self):
        owner = getattr(self, "_owner_state", None)
        owner_name = owner._name if owner else None

        def fmt(state: str, arrow: str) -> str:
            if not state:
                return f"{arrow} —"
            suffix = " (self)" if state == owner_name else ""
            return f"{arrow} {state}{suffix}"

        self._yes_lbl.setPlainText(fmt(self._yes_state, "Y →"))
        self._no_lbl.setPlainText( fmt(self._no_state,  "N ↓"))

    def set_transitions(self, yes_state: str, no_state: str):
        self._yes_state = yes_state
        self._no_state  = no_state
        self._refresh_exit_labels()

    def condition(self) -> str:
        return self._condition

    def yes_state(self) -> str:
        return self._yes_state

    def no_state(self) -> str:
        return self._no_state

    def boundingRect(self) -> QRectF:
        return QRectF(-2, -2, self.W + 120, self.H + 30)

    def paint(self, painter: QPainter, option, widget=None):
        pts = QPolygonF([
            QPointF(self.W / 2, 0),
            QPointF(self.W,     self.H / 2),
            QPointF(self.W / 2, self.H),
            QPointF(0,          self.H / 2),
        ])
        painter.setPen(self._pen())
        painter.setBrush(QBrush(QColor(theme_color("cond_diamond_bg"))))
        painter.drawPolygon(pts)

    def block_type(self) -> str:
        return "diamond"

    def to_dict(self) -> dict:
        d = super().to_dict()
        d.update(condition=self.condition(),
                 yes_state=self.yes_state(),
                 no_state=self.no_state())
        return d


# ══════════════════════════════════════════════════════════════════════════
# HEXAGON ITEM
# ══════════════════════════════════════════════════════════════════════════
class HexagonItem(BaseAsmItem):
    """
    Vertical hexagon (pointy top/bottom) for multi-input decisions.
    Exits are distributed alternately on the left and right sides,
    with a short horizontal stub line from each side point.

    Shape (W×H):
          W/2
           ▲
          /|\
         / | \
    ----/  |  /----  <- left/right exit stubs at mid-height bands
    ----   |  ----
           |
           v
    """
    W, H = 140, 120
    STUB  = 30   # horizontal stub length for exit lines

    def __init__(self, signals_hub: SceneSignals,
                 condition_vars: str = "",
                 exits: list[dict] | None = None):
        super().__init__(signals_hub)
        self._lock()
        self._condition_vars = condition_vars
        self._exits: list[dict] = exits or []
        self._exit_labels: list[QGraphicsTextItem] = []
        self._owner_state = None

        # Centred condition vars label
        self._vars_item = QGraphicsTextItem("", self)
        self._vars_item.setFont(FONT_BODY)
        self._vars_item.setTextInteractionFlags(
            Qt.TextInteractionFlag.NoTextInteraction)
        self._vars_item.setTextWidth(self.W)
        from PyQt6.QtGui import QTextOption
        self._vars_item.document().setDefaultTextOption(
            QTextOption(Qt.AlignmentFlag.AlignCenter))
        self._vars_item.setPos(0, self.H / 2 - 14)
        self._refresh_vars_display()

        self._build_exit_labels()

    def _refresh_vars_display(self):
        if self._condition_vars and self._condition_vars.strip():
            self._vars_item.setPlainText(self._condition_vars)
            self._vars_item.setDefaultTextColor(QColor(theme_color("cond_text")))
        else:
            self._vars_item.setPlainText(tr("cond_click_to_edit"))
            self._vars_item.setDefaultTextColor(QColor(theme_color("cond_hint")))

    def _exit_positions(self) -> list[tuple[str, float, float]]:
        """
        Returns list of (side, x, y) for each exit.
        Exits alternate left/right: 0→left, 1→right, 2→left, 3→right...
        Y positions are evenly spaced in the middle 60% of the hexagon height
        (avoiding the pointy top/bottom inset zones).
        """
        n = len(self._exits)
        if n == 0:
            return []
        inset    = self.H * 0.25          # pointy top/bottom zone height
        body_top = inset
        body_h   = self.H - 2 * inset
        spacing  = body_h / (n + 1)
        positions = []
        for i in range(n):
            y    = body_top + spacing * (i + 1)
            side = "left" if i % 2 == 0 else "right"
            x    = -self.STUB if side == "left" else self.W + self.STUB
            positions.append((side, x, y))
        return positions

    def _build_exit_labels(self):
        for lbl in self._exit_labels:
            lbl.setParentItem(None)
        self._exit_labels.clear()

        owner = getattr(self, "_owner_state", None)
        owner_name = owner._name if owner else None

        positions = self._exit_positions()
        for i, exit_def in enumerate(self._exits):
            if i >= len(positions):
                break
            side, x, y = positions[i]
            label = exit_def.get("label", "")
            state = exit_def.get("state", "") or "—"
            suffix = " (self)" if state == owner_name else ""
            if side == "right":
                txt = f"{label} → {state}{suffix}"
            else:
                txt = f"{state}{suffix} ← {label}"
            txt_item = QGraphicsTextItem(txt, self)
            txt_item.setFont(FONT_SMALL)
            color = QColor(theme_color("exit_hex_right")) if side == "right" else QColor(theme_color("exit_hex_left"))
            txt_item.setDefaultTextColor(color)
            tw = txt_item.boundingRect().width()
            if side == "left":
                txt_item.setPos(-self.STUB - tw - 4, y - 8)
            else:
                txt_item.setPos(self.W + self.STUB + 4, y - 8)
            self._exit_labels.append(txt_item)

    def set_exits(self, exits: list[dict]):
        self._exits = exits
        self._build_exit_labels()
        self.update()

    def condition_vars(self) -> str:
        return self._condition_vars

    def exits(self) -> list[dict]:
        return list(self._exits)

    def boundingRect(self) -> QRectF:
        label_w = 120   # approximate max label width
        return QRectF(
            -self.STUB - label_w - 4, -4,
            self.W + 2 * (self.STUB + label_w + 4), self.H + 8)

    def paint(self, painter: QPainter, option, widget=None):
        w, h    = self.W, self.H
        inset_y = h * 0.25   # top/bottom pointy zone

        # Vertical hexagon: pointy top & bottom, flat left & right sides
        pts = QPolygonF([
            QPointF(w / 2, 0),          # top point
            QPointF(w,     inset_y),    # top-right
            QPointF(w,     h - inset_y),# bottom-right
            QPointF(w / 2, h),          # bottom point
            QPointF(0,     h - inset_y),# bottom-left
            QPointF(0,     inset_y),    # top-left
        ])
        painter.setPen(self._pen())
        painter.setBrush(QBrush(QColor(theme_color("cond_hexagon_bg"))))
        painter.drawPolygon(pts)

        # Draw exit stub lines from the hexagon sides
        painter.setPen(QPen(QColor("#666"), 1.2))
        positions = self._exit_positions()
        for side, _, y in positions:
            if side == "left":
                painter.drawLine(QPointF(0, y), QPointF(-self.STUB, y))
            else:
                painter.drawLine(QPointF(w, y), QPointF(w + self.STUB, y))

    def block_type(self) -> str:
        return "hexagon"

    def to_dict(self) -> dict:
        d = super().to_dict()
        d.update(condition_vars=self.condition_vars(), exits=self.exits())
        return d


# ══════════════════════════════════════════════════════════════════════════
# ARROW ITEM  (optional show-connections overlay)
# ══════════════════════════════════════════════════════════════════════════
class ArrowItem(QGraphicsItem):
    def __init__(self, p1: QPointF, p2: QPointF, label: str = ""):
        super().__init__()
        self._p1, self._p2, self._label = p1, p2, label
        self.setZValue(0)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, False)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable,    False)

    def update_points(self, p1: QPointF, p2: QPointF):
        self.prepareGeometryChange()
        self._p1, self._p2 = p1, p2

    def boundingRect(self) -> QRectF:
        x1,y1 = self._p1.x(), self._p1.y()
        x2,y2 = self._p2.x(), self._p2.y()
        return QRectF(min(x1,x2)-10, min(y1,y2)-10,
                      abs(x2-x1)+20, abs(y2-y1)+20)

    def paint(self, painter: QPainter, option, widget=None):
        x1,y1 = self._p1.x(), self._p1.y()
        x2,y2 = self._p2.x(), self._p2.y()
        mid_y  = (y1 + y2) / 2
        pen = QPen(QColor("#333333"), 1.5)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawLine(QPointF(x1,y1), QPointF(x1,mid_y))
        painter.drawLine(QPointF(x1,mid_y), QPointF(x2,mid_y))
        painter.drawLine(QPointF(x2,mid_y), QPointF(x2,y2))
        painter.setBrush(QBrush(QColor("#333333")))
        aw = 6
        arr = QPolygonF([
            QPointF(x2, y2),
            QPointF(x2 - aw/2, y2 - aw),
            QPointF(x2 + aw/2, y2 - aw),
        ])
        painter.drawPolygon(arr)
        if self._label:
            painter.setFont(FONT_SMALL)
            painter.setPen(QPen(QColor("#666")))
            painter.drawText(QPointF((x1+x2)/2+4, mid_y-4), self._label)

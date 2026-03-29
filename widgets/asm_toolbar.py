"""
widgets/asm_toolbar.py
Vertical icon toolbar for the ASM canvas.
Icons are drawn programmatically as SVG → QPixmap → QIcon.
No external files needed.
"""

from PyQt6.QtWidgets import QToolBar, QToolButton, QButtonGroup
from PyQt6.QtCore import Qt, QSize, QByteArray, QPointF
from PyQt6.QtGui import QIcon, QPixmap, QPainter, QColor
from i18n import tr

try:
    from PyQt6.QtSvg import QSvgRenderer
    _SVG_AVAILABLE = True
except ImportError:
    _SVG_AVAILABLE = False


ICON_SIZE = 32   # px


def _svg_icon(svg_body: str, size: int = ICON_SIZE) -> QIcon:
    """Render an SVG fragment to a QIcon. Falls back to a blank icon if QtSvg unavailable."""
    if not _SVG_AVAILABLE:
        pix = QPixmap(size, size)
        pix.fill(Qt.GlobalColor.transparent)
        return QIcon(pix)
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'viewBox="0 0 {size} {size}" width="{size}" height="{size}">'
        f'{svg_body}'
        f'</svg>'
    )
    renderer = QSvgRenderer(QByteArray(svg.encode()))
    pix = QPixmap(size, size)
    pix.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pix)
    renderer.render(painter)
    painter.end()
    return QIcon(pix)


# ── icon definitions ──────────────────────────────────────────────────── #

def icon_select() -> QIcon:
    """Arrow cursor."""
    return _svg_icon(
        '<polygon points="6,4 6,24 11,19 14,27 17,26 14,18 20,18" '
        'fill="#333" stroke="#333" stroke-width="0.5"/>'
    )

def icon_state() -> QIcon:
    """Rectangle with a header band — state block."""
    return _svg_icon(
        '<rect x="4" y="6" width="24" height="20" rx="3" ry="3" '
        'fill="#dce8fb" stroke="#4a90d9" stroke-width="2"/>'
        '<rect x="4" y="6" width="24" height="7" rx="3" ry="3" '
        'fill="#4a90d9"/>'
        '<rect x="4" y="10" width="24" height="3" fill="#4a90d9"/>'
    )

def icon_output() -> QIcon:
    """Rounded rectangle — output block."""
    return _svg_icon(
        '<rect x="5" y="9" width="22" height="14" rx="6" ry="6" '
        'fill="#fffbe6" stroke="#f0c040" stroke-width="2"/>'
        '<line x1="9" y1="14" x2="23" y2="14" '
        'stroke="#aaa" stroke-width="1.5"/>'
        '<line x1="9" y1="18" x2="19" y2="18" '
        'stroke="#aaa" stroke-width="1.5"/>'
    )

def icon_diamond() -> QIcon:
    """Diamond shape — decision block."""
    return _svg_icon(
        '<polygon points="16,4 28,16 16,28 4,16" '
        'fill="#e8f8e8" stroke="#4caf50" stroke-width="2"/>'
        '<text x="16" y="20" text-anchor="middle" '
        'font-size="10" font-family="Arial" fill="#333">?</text>'
    )

def icon_hexagon() -> QIcon:
    """Flat-top hexagon — multi-decision block."""
    return _svg_icon(
        '<polygon points="8,6 24,6 30,16 24,26 8,26 2,16" '
        'fill="#fce8fb" stroke="#9c27b0" stroke-width="2"/>'
        '<text x="16" y="20" text-anchor="middle" '
        'font-size="8" font-family="Arial" fill="#333">f(x)</text>'
    )

def icon_delete() -> QIcon:
    """Trash can."""
    return _svg_icon(
        '<rect x="10" y="12" width="12" height="14" rx="1" '
        'fill="none" stroke="#c62828" stroke-width="2"/>'
        '<line x1="8" y1="11" x2="24" y2="11" '
        'stroke="#c62828" stroke-width="2"/>'
        '<line x1="13" y1="8" x2="19" y2="8" '
        'stroke="#c62828" stroke-width="2"/>'
        '<line x1="13" y1="15" x2="13" y2="22" '
        'stroke="#c62828" stroke-width="1.5"/>'
        '<line x1="16" y1="15" x2="16" y2="22" '
        'stroke="#c62828" stroke-width="1.5"/>'
        '<line x1="19" y1="15" x2="19" y2="22" '
        'stroke="#c62828" stroke-width="1.5"/>'
    )

def icon_arrow_connect() -> QIcon:
    """Two dots connected by an L-shaped line — connection tool."""
    return _svg_icon(
        '<circle cx="8" cy="8" r="3" fill="#555"/>'
        '<circle cx="24" cy="24" r="3" fill="#555"/>'
        '<polyline points="8,8 8,24 24,24" '
        'fill="none" stroke="#555" stroke-width="2"/>'
        '<polygon points="24,24 19,20 23,19" fill="#555"/>'
    )


# ── toolbar widget ────────────────────────────────────────────────────── #

TOOLS = [
    ("select",  "Select / Move",               icon_select),
    ("state",   "Place State\n(conditions added via state block)", icon_state),
    (None,      None,                           None),
    ("delete",  "Delete Selected\n(or press Del)", icon_delete),
]


class AsmToolbar(QToolBar):
    """
    Vertical icon toolbar for the ASM canvas.
    Emits tool_selected(tool_name) via a QButtonGroup.
    'delete' is a plain (non-checkable) action button.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setOrientation(Qt.Orientation.Vertical)
        self.setIconSize(QSize(ICON_SIZE, ICON_SIZE))
        self.setMovable(False)
        self.setFloatable(False)
        self.setStyleSheet("""
            QToolBar {
                background: #f0f0f0;
                border-right: 1px solid #ccc;
                spacing: 2px;
                padding: 4px 2px;
            }
            QToolButton {
                border: 1px solid transparent;
                border-radius: 4px;
                padding: 3px;
                margin: 1px;
            }
            QToolButton:hover {
                background: #dde8ff;
                border-color: #99b4ee;
            }
            QToolButton:checked {
                background: #c2d4f8;
                border-color: #4a90d9;
            }
        """)

        self._btn_group = QButtonGroup(self)
        self._btn_group.setExclusive(True)
        self._tool_buttons: dict[str, QToolButton] = {}
        self._delete_btn: QToolButton | None = None

        for tool, tooltip, icon_fn in TOOLS:
            if tool is None:
                self.addSeparator()
                continue
            btn = QToolButton()
            btn.setIcon(icon_fn())
            btn.setIconSize(QSize(ICON_SIZE, ICON_SIZE))
            btn.setToolTip(tooltip)
            btn.setFixedSize(ICON_SIZE + 10, ICON_SIZE + 10)
            if tool == "delete":
                btn.setCheckable(False)
                btn.setProperty("tool", "delete")
                self._delete_btn = btn
            else:
                btn.setCheckable(True)
                btn.setProperty("tool", tool)
                self._btn_group.addButton(btn)
                self._tool_buttons[tool] = btn
            self.addWidget(btn)

        # Select tool checked by default
        if "select" in self._tool_buttons:
            self._tool_buttons["select"].setChecked(True)

    def active_tool(self) -> str:
        btn = self._btn_group.checkedButton()
        return btn.property("tool") if btn else "select"

    def set_tool(self, tool: str):
        if tool in self._tool_buttons:
            self._tool_buttons[tool].setChecked(True)

    def connect_tool_changed(self, slot):
        self._btn_group.buttonClicked.connect(
            lambda btn: slot(btn.property("tool")))

    def connect_delete(self, slot):
        if self._delete_btn:
            self._delete_btn.clicked.connect(slot)

    def retranslate_ui(self):
        tooltips = {
            "select":  tr("asm_tool_select"),
            "state":   tr("asm_tool_state"),
        }
        for tool, btn in self._tool_buttons.items():
            if tool in tooltips:
                btn.setToolTip(tooltips[tool])
        if self._delete_btn:
            self._delete_btn.setToolTip(tr("asm_tool_delete"))

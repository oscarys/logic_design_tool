"""
widgets/timing_diagram_widget.py
A QWidget that renders a live logic-analyzer style timing diagram.
Updates incrementally as simulation cycles are appended.
"""

from PyQt6.QtWidgets import QWidget, QScrollArea, QVBoxLayout, QSizePolicy
from PyQt6.QtGui import (
    QPainter, QColor, QPen, QFont, QFontMetrics, QBrush, QImage
)
from PyQt6.QtCore import Qt, QRectF, QSize

# ── layout constants ──────────────────────────────────────────────────── #
LABEL_W  = 90
CELL_W   = 60
LANE_H   = 34
CLK_H    = 22
PAD_TOP  = 26
PAD_BOT  = 10

FONT_LABEL = QFont("Arial", 8, QFont.Weight.Bold)
FONT_VALUE = QFont("Arial", 7)
FONT_CYCLE = QFont("Arial", 7)
FONT_STATE = QFont("Arial", 7, QFont.Weight.Bold)

CLR_BG         = QColor("#ffffff")
CLR_GRID       = QColor("#e8e8e8")
CLR_LABEL_BG   = QColor("#f5f5f5")
CLR_LABEL_TEXT = QColor("#333333")
CLR_CYCLE_TEXT = QColor("#999999")
CLR_BORDER     = QColor("#cccccc")
CLR_CLK        = QColor("#2196f3")
CLR_SIG_HI     = QColor("#43a047")
CLR_SIG_LO     = QColor("#e53935")
CLR_SIG_BUS    = QColor("#7b1fa2")
CLR_STATE_TEXT = QColor("#ffffff")
STATE_COLORS   = [QColor("#4a90d9"), QColor("#2e6da8")]


def _is_high(v: str) -> bool:
    v = v.strip()
    return bool(v) and set(v) != {"0"} and v not in ("false", "False")


def _is_bus(v: str) -> bool:
    return len(v.strip()) > 1


class TimingDiagramCanvas(QWidget):
    """
    The actual drawing canvas. Sized to fit all cycles and lanes,
    placed inside a QScrollArea so it scrolls horizontally.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._trace:        list[dict] = []
        self._input_names:  list[str]  = []
        self._output_names: list[str]  = []
        self.setSizePolicy(QSizePolicy.Policy.Expanding,
                           QSizePolicy.Policy.Expanding)
        self.setMinimumHeight(80)

    def set_signals(self, input_names: list[str], output_names: list[str]):
        self._input_names  = input_names
        self._output_names = output_names
        self._trace        = []
        self._update_size()
        self.update()

    def append(self, row: dict):
        self._trace.append(row)
        self._update_size()
        self.update()

    def clear(self):
        self._trace = []
        self._update_size()
        self.update()

    def trace(self) -> list[dict]:
        return list(self._trace)

    # ── sizing ────────────────────────────────────────────────────────── #

    def _lane_list(self):
        lanes = [("clk",   "clk",   CLK_H)]
        lanes += [("state", "state", LANE_H)]
        for n in self._input_names:
            lanes.append(("input", n, LANE_H))
        for n in self._output_names:
            lanes.append(("output", n, LANE_H))
        return lanes

    def _total_height(self) -> int:
        return PAD_TOP + sum(h for _, _, h in self._lane_list()) + PAD_BOT

    def _total_width(self) -> int:
        n = max(len(self._trace), 1)
        return LABEL_W + n * CELL_W + 20

    def _update_size(self):
        self.setMinimumSize(self._total_width(), self._total_height())
        self.setFixedHeight(self._total_height())
        self.resize(self._total_width(), self._total_height())

    def sizeHint(self) -> QSize:
        return QSize(self._total_width(), self._total_height())

    # ── painting ──────────────────────────────────────────────────────── #

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()
        lanes = self._lane_list()
        n = len(self._trace)

        # Background
        p.fillRect(0, 0, w, h, CLR_BG)

        # Label column background
        p.fillRect(0, 0, LABEL_W, h, CLR_LABEL_BG)
        p.setPen(QPen(CLR_BORDER, 1))
        p.drawLine(LABEL_W, 0, LABEL_W, h)

        if n == 0:
            p.setFont(FONT_LABEL)
            p.setPen(QColor("#aaaaaa"))
            p.drawText(LABEL_W + 10, 0, w - LABEL_W - 10, h,
                       Qt.AlignmentFlag.AlignVCenter, "  — run simulation to see waveform —")
            self._draw_labels(p, lanes)
            p.end()
            return

        # Cycle numbers
        p.setFont(FONT_CYCLE)
        p.setPen(CLR_CYCLE_TEXT)
        for i, row in enumerate(self._trace):
            cx = LABEL_W + i * CELL_W + CELL_W // 2
            p.drawText(cx - 16, 2, 32, PAD_TOP - 4,
                       Qt.AlignmentFlag.AlignCenter, str(row["cycle"]))

        # Draw lanes
        y = PAD_TOP
        for lane_type, name, lane_h in lanes:
            self._draw_label(p, name, y, lane_h)
            self._draw_grid(p, y, lane_h, n)

            if lane_type == "clk":
                self._draw_clock(p, y, lane_h, n)
            elif lane_type == "state":
                self._draw_state_lane(p, y, lane_h)
            else:
                is_input = (lane_type == "input")
                self._draw_signal_lane(p, y, lane_h, name, is_input)

            # Lane separator
            p.setPen(QPen(CLR_GRID, 1))
            p.drawLine(0, y + lane_h, w, y + lane_h)
            y += lane_h

        # Outer border
        p.setPen(QPen(CLR_BORDER, 1))
        p.drawRect(0, PAD_TOP,
                   LABEL_W + n * CELL_W + 18,
                   h - PAD_TOP - PAD_BOT)

        p.end()

    def _draw_labels(self, p, lanes):
        y = PAD_TOP
        for _, name, lane_h in lanes:
            self._draw_label(p, name, y, lane_h)
            p.setPen(QPen(CLR_GRID, 1))
            p.drawLine(0, y + lane_h, LABEL_W, y + lane_h)
            y += lane_h

    def _draw_label(self, p, name, y, h):
        p.setFont(FONT_LABEL)
        p.setPen(CLR_LABEL_TEXT)
        p.drawText(6, y, LABEL_W - 8, h,
                   Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft,
                   name)

    def _draw_grid(self, p, y, h, n):
        p.setPen(QPen(CLR_GRID, 1, Qt.PenStyle.DotLine))
        for i in range(1, n):
            x = LABEL_W + i * CELL_W
            p.drawLine(x, y, x, y + h)

    def _draw_clock(self, p, y, h, n):
        pen = QPen(CLR_CLK, 1.5)
        p.setPen(pen)
        high_y = y + 4
        low_y  = y + h - 4
        mid_y  = y + h // 2
        half   = CELL_W // 2
        x = LABEL_W
        for _ in range(n):
            p.drawLine(x,         mid_y,  x,          high_y)
            p.drawLine(x,         high_y, x + half,   high_y)
            p.drawLine(x + half,  high_y, x + half,   low_y)
            p.drawLine(x + half,  low_y,  x + CELL_W, low_y)
            p.drawLine(x + CELL_W, low_y, x + CELL_W, mid_y)
            x += CELL_W

    def _draw_state_lane(self, p, y, h):
        margin = 3
        for i, row in enumerate(self._trace):
            x     = LABEL_W + i * CELL_W
            state = row["state"]
            color = STATE_COLORS[i % len(STATE_COLORS)]
            p.fillRect(x + 1, y + margin, CELL_W - 2, h - 2 * margin, color)
            p.setFont(FONT_STATE)
            p.setPen(CLR_STATE_TEXT)
            p.drawText(x + 2, y + margin, CELL_W - 4, h - 2 * margin,
                       Qt.AlignmentFlag.AlignCenter, state)
            if i > 0 and self._trace[i - 1]["state"] != state:
                p.setPen(QPen(QColor("#ffffff"), 1.5))
                p.drawLine(x, y + margin, x, y + h - margin)

    def _draw_signal_lane(self, p, y, h, sig_name, is_input):
        high_y = y + 6
        low_y  = y + h - 6
        mid_y  = y + h // 2

        def get_val(row):
            d = row["inputs"] if is_input else row["outputs"]
            return d.get(sig_name, "0")

        for i, row in enumerate(self._trace):
            val    = get_val(row)
            x      = LABEL_W + i * CELL_W
            hi     = _is_high(val)
            bus    = _is_bus(val)
            curr_y = high_y if hi else low_y

            if bus:
                p.setPen(QPen(CLR_SIG_BUS, 1.5))
                p.drawLine(x, high_y, x + CELL_W, high_y)
                p.drawLine(x, low_y,  x + CELL_W, low_y)
                p.setFont(FONT_VALUE)
                p.drawText(x + 2, y, CELL_W - 4, h,
                           Qt.AlignmentFlag.AlignCenter, val.strip())
                if i > 0 and get_val(self._trace[i - 1]) != val:
                    p.drawLine(x, high_y, x + 4, mid_y)
                    p.drawLine(x, low_y,  x + 4, mid_y)
            else:
                p.setPen(QPen(CLR_SIG_HI if hi else CLR_SIG_LO, 1.5))
                if i > 0:
                    prev_hi = _is_high(get_val(self._trace[i - 1]))
                    if prev_hi != hi:
                        prev_y = high_y if prev_hi else low_y
                        p.setPen(QPen(QColor("#555555"), 1.5))
                        p.drawLine(x, prev_y, x, curr_y)
                p.setPen(QPen(CLR_SIG_HI if hi else CLR_SIG_LO, 1.5))
                p.drawLine(x, curr_y, x + CELL_W, curr_y)


class TimingDiagramWidget(QScrollArea):
    """
    Scrollable container for the TimingDiagramCanvas.
    Exposes the same API as the old QTableWidget for drop-in replacement.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._canvas = TimingDiagramCanvas()
        self.setWidget(self._canvas)
        self.setWidgetResizable(False)
        self.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setMinimumHeight(120)
        self.setFrameShape(QScrollArea.Shape.NoFrame)

    def set_signals(self, input_names, output_names):
        self._canvas.set_signals(input_names, output_names)

    def append_cycle(self, row: dict):
        self._canvas.append(row)
        # Auto-scroll to show latest cycle
        hsb = self.horizontalScrollBar()
        hsb.setValue(hsb.maximum())

    def clear(self):
        self._canvas.clear()

    def row_count(self) -> int:
        return len(self._canvas.trace())

    def trace(self) -> list[dict]:
        return self._canvas.trace()

    def render_to_image(self) -> QImage:
        """Render the full diagram to a QImage for PNG export."""
        canvas = self._canvas
        img = QImage(canvas.sizeHint(), QImage.Format.Format_ARGB32)
        img.fill(QColor("white"))
        p = QPainter(img)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        canvas.render(p)
        p.end()
        return img

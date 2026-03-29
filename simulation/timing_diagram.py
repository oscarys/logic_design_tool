"""
simulation/timing_diagram.py
Renders a logic-analyzer style timing diagram from FSM trace data.

Layout
------
  ┌──────────┬──────────────────────────────────────────┐
  │  clk     │  ┐└┐└┐└┐└┐└┐└┐└┐└┐└┐└                  │
  │  state   │  [  S0  ][  S0  ][  S1  ][  S2  ]       │
  │  x       │  ________‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾________       │
  │  z       │  ________________‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾       │
  └──────────┴──────────────────────────────────────────┘
              0         1         2         3
"""

from PyQt6.QtGui import (
    QImage, QPainter, QColor, QPen, QFont, QFontMetrics, QBrush
)
from PyQt6.QtCore import Qt, QRectF, QPointF


# ── layout constants ──────────────────────────────────────────────────── #
LABEL_W   = 90      # left label column width
CELL_W    = 64      # width per cycle
LANE_H    = 36      # height per signal lane
CLK_H     = 24      # clock lane is shorter
PAD_TOP   = 28      # space for cycle numbers
PAD_BOT   = 16
PAD_RIGHT = 20

FONT_LABEL = QFont("Arial", 8, QFont.Weight.Bold)
FONT_VALUE = QFont("Arial", 7)
FONT_CYCLE = QFont("Arial", 7)
FONT_STATE = QFont("Arial", 7, QFont.Weight.Bold)

CLR_BG         = QColor("#ffffff")
CLR_GRID       = QColor("#e8e8e8")
CLR_LABEL_BG   = QColor("#f0f0f0")
CLR_LABEL_TEXT = QColor("#333333")
CLR_CYCLE_TEXT = QColor("#888888")
CLR_BORDER     = QColor("#cccccc")

CLR_CLK_HI  = QColor("#2196f3")
CLR_CLK_LO  = CLR_CLK_HI

CLR_SIG_HI  = QColor("#43a047")   # green for '1'
CLR_SIG_LO  = QColor("#e53935")   # red for '0'
CLR_SIG_BUS = QColor("#7b1fa2")   # purple for multi-bit

CLR_STATE_BOX  = QColor("#4a90d9")
CLR_STATE_TEXT = QColor("#ffffff")

# State lane alternating colours
STATE_COLORS = [QColor("#4a90d9"), QColor("#2e6da8")]


def render_timing_diagram(trace: list[dict]) -> QImage:
    """
    Render a timing diagram from trace data.

    trace: list of dicts, each with keys:
        cycle   : int
        state   : str
        inputs  : dict[str, str]
        outputs : dict[str, str]

    Returns a QImage (PNG-ready).
    """
    if not trace:
        return _error_image("No trace data to render.")

    n_cycles    = len(trace)
    input_names = list(trace[0]["inputs"].keys())
    output_names = list(trace[0]["outputs"].keys())

    # Build lane list: clk, state, inputs..., outputs...
    lanes = [("clk",   "clk",   CLK_H)]
    lanes += [("state", "state", LANE_H)]
    for name in input_names:
        lanes.append(("input", name, LANE_H))
    for name in output_names:
        lanes.append(("output", name, LANE_H))

    total_h = PAD_TOP + sum(h for _, _, h in lanes) + PAD_BOT
    total_w = LABEL_W + n_cycles * CELL_W + PAD_RIGHT

    # ── create image ──
    img = QImage(total_w, total_h, QImage.Format.Format_ARGB32)
    img.fill(CLR_BG)
    p = QPainter(img)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)

    # ── cycle numbers ──
    p.setFont(FONT_CYCLE)
    p.setPen(CLR_CYCLE_TEXT)
    for i, row in enumerate(trace):
        cx = LABEL_W + i * CELL_W + CELL_W // 2
        p.drawText(cx - 12, 4, 24, PAD_TOP - 6,
                   Qt.AlignmentFlag.AlignCenter,
                   str(row["cycle"]))

    # ── label column background ──
    p.fillRect(0, PAD_TOP, LABEL_W,
               total_h - PAD_TOP - PAD_BOT, CLR_LABEL_BG)
    p.setPen(QPen(CLR_BORDER, 1))
    p.drawLine(LABEL_W, PAD_TOP, LABEL_W, total_h - PAD_BOT)

    # ── draw each lane ──
    y = PAD_TOP
    for lane_type, name, lane_h in lanes:
        _draw_label(p, name, y, lane_h)
        _draw_grid(p, y, lane_h, n_cycles)

        if lane_type == "clk":
            _draw_clock(p, y, lane_h, n_cycles)
        elif lane_type == "state":
            _draw_state_lane(p, y, lane_h, trace)
        else:
            is_input = (lane_type == "input")
            _draw_signal_lane(p, y, lane_h, trace, name, is_input)

        # Lane separator
        p.setPen(QPen(CLR_GRID, 1))
        p.drawLine(0, y + lane_h, total_w, y + lane_h)

        y += lane_h

    # ── outer border ──
    p.setPen(QPen(CLR_BORDER, 1))
    p.drawRect(0, PAD_TOP, total_w - 1, total_h - PAD_TOP - PAD_BOT - 1)

    p.end()
    return img


# ── lane drawing helpers ───────────────────────────────────────────────── #

def _draw_label(p: QPainter, name: str, y: int, h: int):
    p.setFont(FONT_LABEL)
    p.setPen(CLR_LABEL_TEXT)
    p.drawText(4, y, LABEL_W - 8, h,
               Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft,
               name)


def _draw_grid(p: QPainter, y: int, h: int, n: int):
    p.setPen(QPen(CLR_GRID, 1, Qt.PenStyle.DotLine))
    for i in range(1, n):
        x = LABEL_W + i * CELL_W
        p.drawLine(x, y, x, y + h)


def _draw_clock(p: QPainter, y: int, h: int, n: int):
    """Draw a toggling clock waveform."""
    pen = QPen(CLR_CLK_HI, 1.5)
    p.setPen(pen)
    mid_y   = y + h // 2
    high_y  = y + 4
    low_y   = y + h - 4
    half    = CELL_W // 2

    x = LABEL_W
    for _ in range(n):
        # rising edge → high half
        p.drawLine(x,         mid_y,  x,         high_y)
        p.drawLine(x,         high_y, x + half,   high_y)
        # falling edge → low half
        p.drawLine(x + half,  high_y, x + half,   low_y)
        p.drawLine(x + half,  low_y,  x + CELL_W, low_y)
        # next rising edge stub
        p.drawLine(x + CELL_W, low_y, x + CELL_W, mid_y)
        x += CELL_W


def _draw_state_lane(p: QPainter, y: int, h: int,
                     trace: list[dict]):
    """Draw state names as coloured boxes with transition lines."""
    n = len(trace)
    margin = 3

    for i, row in enumerate(trace):
        x    = LABEL_W + i * CELL_W
        state = row["state"]
        color = STATE_COLORS[i % len(STATE_COLORS)]

        # Box
        p.fillRect(x + 1, y + margin,
                   CELL_W - 2, h - 2 * margin, color)

        # State name
        p.setFont(FONT_STATE)
        p.setPen(CLR_STATE_TEXT)
        p.drawText(x + 2, y + margin,
                   CELL_W - 4, h - 2 * margin,
                   Qt.AlignmentFlag.AlignCenter, state)

        # Transition tick between different states
        if i > 0 and trace[i - 1]["state"] != state:
            p.setPen(QPen(QColor("#ffffff"), 2))
            p.drawLine(x, y + margin, x, y + h - margin)


def _draw_signal_lane(p: QPainter, y: int, h: int,
                      trace: list[dict], sig_name: str,
                      is_input: bool):
    """Draw a digital waveform for a 1-bit or bus signal."""
    high_y = y + 6
    low_y  = y + h - 6
    mid_y  = y + h // 2
    color  = QColor("#1976d2") if is_input else QColor("#2e7d32")

    def get_val(row):
        d = row["inputs"] if is_input else row["outputs"]
        return d.get(sig_name, "0")

    def is_high(v: str) -> bool:
        v = v.strip()
        if not v or set(v) == {"0"}:
            return False
        if v in ("1", "true", "True"):
            return True
        # Bus: high if any bit is 1
        return any(c == "1" for c in v)

    def is_bus(v: str) -> bool:
        return len(v.strip()) > 1

    n = len(trace)
    pen = QPen(color, 1.5)
    p.setPen(pen)

    for i, row in enumerate(trace):
        val     = get_val(row)
        x_start = LABEL_W + i * CELL_W
        x_end   = x_start + CELL_W
        hi      = is_high(val)
        bus     = is_bus(val)

        curr_y = high_y if hi else low_y

        if bus:
            # Bus: draw as parallel lines with value label
            p.setPen(QPen(CLR_SIG_BUS, 1.5))
            p.drawLine(x_start, high_y, x_end, high_y)
            p.drawLine(x_start, low_y,  x_end, low_y)
            p.setFont(FONT_VALUE)
            p.drawText(x_start + 2, y, CELL_W - 4, h,
                       Qt.AlignmentFlag.AlignCenter, val.strip())
            # Transition marks
            if i > 0 and get_val(trace[i - 1]) != val:
                p.drawLine(x_start, high_y, x_start + 4, mid_y)
                p.drawLine(x_start, low_y,  x_start + 4, mid_y)
            p.setPen(pen)
        else:
            # Scalar: square wave
            p.setPen(QPen(CLR_SIG_HI if hi else CLR_SIG_LO, 1.5))
            # Vertical edge if value changed
            if i > 0:
                prev_hi = is_high(get_val(trace[i - 1]))
                if prev_hi != hi:
                    prev_y = high_y if prev_hi else low_y
                    p.drawLine(x_start, prev_y, x_start, curr_y)
            # Horizontal segment
            p.drawLine(x_start, curr_y, x_end, curr_y)


def _error_image(msg: str) -> QImage:
    img = QImage(400, 60, QImage.Format.Format_ARGB32)
    img.fill(QColor("#fff3f3"))
    p = QPainter(img)
    p.setPen(QColor("#c62828"))
    p.setFont(QFont("Arial", 9))
    p.drawText(10, 10, 380, 40, Qt.AlignmentFlag.AlignVCenter, msg)
    p.end()
    return img

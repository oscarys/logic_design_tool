"""
i18n/themes.py
Light and Dark theme color tokens.

Keys are semantic names used throughout the app.
Widget chrome uses the QSS stylesheet.
Canvas items use theme_color(key) at paint time.
"""

LIGHT = {
    # ── App chrome ───────────────────────────────────────────────────── #
    "qss": """
        QMainWindow, QWidget { background: #f5f5f5; color: #1a1a1a; }
        QMenuBar { background: #ececec; color: #1a1a1a; }
        QMenuBar::item:selected { background: #d0d0d0; }
        QMenu { background: #ffffff; color: #1a1a1a; border: 1px solid #ccc; }
        QMenu::item:selected { background: #4a90d9; color: white; }
        QTabWidget::pane { border: 1px solid #ccc; }
        QTabBar::tab { background: #e0e0e0; color: #333; padding: 5px 12px;
                       border: 1px solid #ccc; border-bottom: none; }
        QTabBar::tab:selected { background: #f5f5f5; color: #1a1a1a; }
        QTableWidget { background: #ffffff; color: #1a1a1a;
                       gridline-color: #ddd; }
        QTableWidget QHeaderView::section { background: #e8e8e8;
                       color: #333; border: 1px solid #ccc; }
        QHeaderView::section { background: #e8e8e8; color: #333; }
        QLineEdit, QComboBox, QSpinBox {
            background: #ffffff; color: #1a1a1a;
            border: 1px solid #ccc; border-radius: 3px; padding: 2px 4px; }
        QPushButton { background: #e8e8e8; color: #1a1a1a;
                      border: 1px solid #bbb; border-radius: 3px; padding: 3px 8px; }
        QPushButton:hover { background: #d8d8d8; }
        QPushButton:pressed { background: #c8c8c8; }
        QStatusBar { background: #ececec; color: #555; }
        QScrollBar:vertical { background: #f0f0f0; width: 10px; }
        QScrollBar::handle:vertical { background: #bbb; border-radius: 4px; }
        QCheckBox { color: #1a1a1a; }
        QLabel { color: #1a1a1a; }
        QTextEdit { background: #ffffff; color: #1a1a1a; border: 1px solid #ccc; }
        QGraphicsView { background: #f5f5f5; border: 1px solid #ccc; }
    """,

    # ── Canvas ───────────────────────────────────────────────────────── #
    "canvas_bg":        "#f5f5f5",
    "canvas_grid":      "#e0e0e0",
    "state_bg":         "#dce8fb",
    "state_hdr":        "#4a90d9",
    "state_hdr_init":   "#e65100",
    "state_text":       "#1a1a1a",
    "state_text_init":  "#ffe0b2",
    "cond_diamond_bg":  "#e8f8e8",
    "cond_hexagon_bg":  "#fce8fb",
    "cond_uncond_bg":   "#f0f4ff",
    "cond_hint":        "#aaaaaa",
    "cond_text":        "#1a1a1a",
    "pen_normal":       "#555555",
    "pen_selected":     "#ff6600",
    "pen_connect":      "#555555",
    "exit_yes":         "#1a6b1a",
    "exit_no":          "#6b1a1a",
    "exit_hex_left":    "#6b1a1a",
    "exit_hex_right":   "#1a1a6b",
}

DARK = {
    # ── App chrome ───────────────────────────────────────────────────── #
    "qss": """
        QMainWindow, QWidget { background: #1e1e1e; color: #d4d4d4; }
        QMenuBar { background: #2d2d2d; color: #d4d4d4; }
        QMenuBar::item:selected { background: #3e3e3e; }
        QMenu { background: #2d2d2d; color: #d4d4d4; border: 1px solid #555; }
        QMenu::item:selected { background: #4a90d9; color: white; }
        QTabWidget::pane { border: 1px solid #444; }
        QTabBar::tab { background: #2d2d2d; color: #aaa; padding: 5px 12px;
                       border: 1px solid #444; border-bottom: none; }
        QTabBar::tab:selected { background: #1e1e1e; color: #d4d4d4; }
        QTableWidget { background: #252525; color: #d4d4d4;
                       gridline-color: #3a3a3a; }
        QTableWidget QHeaderView::section { background: #2d2d2d;
                       color: #aaa; border: 1px solid #444; }
        QHeaderView::section { background: #2d2d2d; color: #aaa; }
        QLineEdit, QComboBox, QSpinBox {
            background: #2d2d2d; color: #d4d4d4;
            border: 1px solid #555; border-radius: 3px; padding: 2px 4px; }
        QPushButton { background: #2d2d2d; color: #d4d4d4;
                      border: 1px solid #555; border-radius: 3px; padding: 3px 8px; }
        QPushButton:hover { background: #3a3a3a; }
        QPushButton:pressed { background: #444; }
        QStatusBar { background: #2d2d2d; color: #888; }
        QScrollBar:vertical { background: #2d2d2d; width: 10px; }
        QScrollBar::handle:vertical { background: #555; border-radius: 4px; }
        QCheckBox { color: #d4d4d4; }
        QLabel { color: #d4d4d4; }
        QTextEdit { background: #1e1e1e; color: #d4d4d4; border: 1px solid #555; }
        QGraphicsView { background: #1e1e1e; border: 1px solid #444; }
    """,

    # ── Canvas ───────────────────────────────────────────────────────── #
    "canvas_bg":        "#1e1e1e",
    "canvas_grid":      "#2a2a2a",
    "state_bg":         "#1e3050",
    "state_hdr":        "#2a5fa8",
    "state_hdr_init":   "#b34700",
    "state_text":       "#d4d4d4",
    "state_text_init":  "#ffe0b2",
    "cond_diamond_bg":  "#1a3320",
    "cond_hexagon_bg":  "#2e1a30",
    "cond_uncond_bg":   "#1a1e35",
    "cond_hint":        "#666666",
    "cond_text":        "#d4d4d4",
    "pen_normal":       "#888888",
    "pen_selected":     "#ff8c00",
    "pen_connect":      "#888888",
    "exit_yes":         "#4caf50",
    "exit_no":          "#ef5350",
    "exit_hex_left":    "#ef5350",
    "exit_hex_right":   "#64b5f6",
}

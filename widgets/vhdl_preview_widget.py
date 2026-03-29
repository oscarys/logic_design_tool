"""
widgets/vhdl_preview_widget.py
Promoted widget: syntax-highlighted read-only VHDL viewer.
"""


from PyQt6.QtWidgets import QWidget, QVBoxLayout, QPlainTextEdit
from PyQt6.QtGui import (
    QFont, QColor, QPalette, QSyntaxHighlighter, QTextCharFormat
)
from PyQt6.QtCore import Qt, QRegularExpression


# ── syntax highlighter ─────────────────────────────────────────────────── #

class VHDLHighlighter(QSyntaxHighlighter):

    # VHDL-2008 keywords
    KEYWORDS = [
        "library", "use", "entity", "is", "port", "in", "out", "inout",
        "end", "architecture", "of", "begin", "signal", "constant",
        "process", "if", "then", "else", "elsif", "end", "when",
        "case", "for", "loop", "generate", "component", "map",
        "generic", "type", "subtype", "downto", "to", "others",
        "std_logic", "std_logic_vector", "std_ulogic",
        "unsigned", "signed", "natural", "integer", "boolean",
        "rising_edge", "falling_edge", "and", "or", "not", "nand",
        "nor", "xor", "xnor", "all", "with", "select", "after",
        "wait", "report", "severity", "variable", "attribute",
        "package", "body", "return", "function", "procedure",
        "ieee", "std_logic_1164", "numeric_std",
    ]

    def __init__(self, document):
        super().__init__(document)
        self._rules: list[tuple[QRegularExpression, QTextCharFormat]] = []

        def fmt(color, bold=False, italic=False) -> QTextCharFormat:
            f = QTextCharFormat()
            f.setForeground(QColor(color))
            if bold:
                f.setFontWeight(700)
            if italic:
                f.setFontItalic(True)
            return f

        # Keywords  (case-insensitive)
        kw_fmt = fmt("#569cd6", bold=True)
        for kw in self.KEYWORDS:
            pat = QRegularExpression(
                rf"\b{kw}\b",
                QRegularExpression.PatternOption.CaseInsensitiveOption
            )
            self._rules.append((pat, kw_fmt))

        # std_logic literals  '0' '1' 'X' 'Z' etc.
        self._rules.append((
            QRegularExpression(r"'[01XZUWLH\-]'"),
            fmt("#ce9178")
        ))

        # Bit-string literals  "0110"  X"3F"  B"1010"
        self._rules.append((
            QRegularExpression(r'[BOXbox]?"[01a-fA-FXZxz_]+"'),
            fmt("#ce9178")
        ))

        # Numbers
        self._rules.append((
            QRegularExpression(r"\b\d+\b"),
            fmt("#b5cea8")
        ))

        # Comments  -- …
        self._rules.append((
            QRegularExpression(r"--[^\n]*"),
            fmt("#6a9955", italic=True)
        ))

        # Entity / architecture names (after keyword)
        self._rules.append((
            QRegularExpression(r"\bentity\s+(\w+)", 
                QRegularExpression.PatternOption.CaseInsensitiveOption),
            fmt("#4ec9b0", bold=True)
        ))
        self._rules.append((
            QRegularExpression(r"\barchitecture\s+(\w+)\s+of\s+(\w+)",
                QRegularExpression.PatternOption.CaseInsensitiveOption),
            fmt("#4ec9b0")
        ))

    def highlightBlock(self, text: str):
        for pattern, fmt in self._rules:
            it = pattern.globalMatch(text)
            while it.hasNext():
                match = it.next()
                self.setFormat(match.capturedStart(),
                               match.capturedLength(), fmt)


# ── widget ─────────────────────────────────────────────────────────────── #

class VHDLPreviewWidget(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self._editor = QPlainTextEdit()
        self._editor.setReadOnly(True)
        self._editor.setFont(QFont("Courier New", 10))
        self._editor.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)

        # Dark VS-Code-like theme
        palette = self._editor.palette()
        palette.setColor(QPalette.ColorRole.Base,           QColor("#1e1e1e"))
        palette.setColor(QPalette.ColorRole.Text,           QColor("#d4d4d4"))
        palette.setColor(QPalette.ColorRole.AlternateBase,  QColor("#252526"))
        self._editor.setPalette(palette)
        self._editor.setStyleSheet(
            "QPlainTextEdit { border: 1px solid #3c3c3c; }"
        )

        self._editor.setPlaceholderText(
            "-- VHDL output will appear here after clicking ⚡ Generate"
        )

        self._highlighter = VHDLHighlighter(self._editor.document())
        layout.addWidget(self._editor)

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #
    def set_vhdl(self, code: str):
        self._editor.setPlainText(code)

    def get_vhdl(self) -> str:
        return self._editor.toPlainText()

    def clear(self):
        self._editor.clear()

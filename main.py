# VHDL Design Tool
# Copyright (C) 2025 VHDL Design Tool Contributors
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.

"""
main.py — entry point for the VHDL Design Tool.

Usage:
    python main.py
"""


import sys
import os

# ── version gate ──────────────────────────────────────────────────────── #
if sys.version_info < (3, 10):
    _v = sys.version.split()[0]
    print(
        "ERROR: Python 3.10 or later is required.\n"
        f"       You are running Python {_v}\n"
        "       Please upgrade: https://www.python.org/downloads/",
        file=sys.stderr
    )
    sys.exit(1)

# Ensure package root is on sys.path when running directly
sys.path.insert(0, os.path.dirname(__file__))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("VHDL Design Tool")
    app.setOrganizationName("VHDLTool")

    # Load persisted language + theme (requires QApplication to exist first)
    from i18n import _read_settings
    _read_settings()

    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

"""
widgets/combinational_widget.py
Loads combinational_tab.ui and wires the signal manager + truth table.
"""


import os
from PyQt6.QtWidgets import QWidget, QFileDialog, QApplication, QVBoxLayout
from PyQt6 import uic

from models.signal_model  import SignalModel, Signal, Direction
from models.truth_table_model import TruthTableModel
from widgets.signal_manager_widget import SignalManagerWidget
from widgets.truth_table_widget    import TruthTableWidget
from widgets.vhdl_preview_widget   import VHDLPreviewWidget
from generators.combinational_vhdl import CombinationalVHDLGenerator
from i18n import tr

UI_PATH = os.path.join(os.path.dirname(__file__), "..", "ui", "combinational_tab.ui")


class CombinationalWidget(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        uic.loadUi(UI_PATH, self)

        # ── models ──
        self._signal_model = SignalModel(self)
        self._tt_model     = TruthTableModel(self)

        # ── replace placeholder tableSignals with SignalManagerWidget ──
        # The .ui has a QTableWidget called tableSignals; we swap it out
        # for our richer SignalManagerWidget and insert it in the same spot.
        self._signal_mgr = SignalManagerWidget(
            self._signal_model, show_bus=True, parent=self)

        # Find the placeholder in the left panel layout and replace it
        left_layout = self.leftPanel.layout()
        for i in range(left_layout.count()):
            item = left_layout.itemAt(i)
            if item and item.widget() is self.tableSignals:
                left_layout.removeWidget(self.tableSignals)
                self.tableSignals.deleteLater()
                left_layout.insertWidget(i, self._signal_mgr)
                break

        # ── wire truth table widget (promoted, already in .ui) ──
        self.truthTableWidget.set_model(self._tt_model)

        # ── connect signal model → truth table rebuild ──
        self._signal_model.changed.connect(self._on_signals_changed)

        # ── connect buttons ──
        self.btnGenerate.clicked.connect(self._on_generate)
        self.btnCopyVHDL.clicked.connect(self._on_copy_vhdl)
        self.btnSaveVHDL.clicked.connect(self._on_save_vhdl)

        # ── seed with a small default design so the UI isn't blank ──
        self._signal_model.add_signal(Signal("a", Direction.INPUT))
        self._signal_model.add_signal(Signal("b", Direction.INPUT))
        self._signal_model.add_signal(Signal("y", Direction.OUTPUT))

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #
    def _status(self, msg: str):
        """Send a message to the main window status bar."""
        win = self.window()
        if hasattr(win, 'statusBar'):
            win.statusBar().showMessage(msg)

    def retranslate_ui(self):
        self.labelEntityName.setText(tr("tt_entity"))
        self.lineEditEntityName.setPlaceholderText(tr("hint_entity_comb"))
        self.labelArchName.setText(tr("tt_arch"))
        self.lineEditArchName.setPlaceholderText(tr("hint_arch"))
        self.labelDontCare.setText(tr("tt_dc_label"))
        self.comboDontCare.setItemText(0, tr("tt_dc_dash"))
        self.comboDontCare.setItemText(1, tr("tt_dc_one"))
        self.comboDontCare.setItemText(2, tr("tt_dc_zero"))
        self.labelSignals.setText(tr("sig_title"))
        self.labelTruthTable.setText(tr("lbl_truth_table"))
        self.labelPreview.setText(tr("lbl_vhdl_preview"))
        self.btnGenerate.setText("⚡ " + tr("vhdl_generate"))
        self.btnCopyVHDL.setText("⎘ " + tr("vhdl_copy"))
        self.btnSaveVHDL.setText("💾 " + tr("vhdl_save"))
        if hasattr(self, '_signal_mgr'):
            self._signal_mgr.retranslate_ui()

    def _reset(self):
        """Clear all signals and truth table for a new project."""
        self._signal_model.clear()
        self.lineEditEntityName.clear()
        self.lineEditArchName.clear()
        self._signal_model.add_signal(Signal("a", Direction.INPUT))
        self._signal_model.add_signal(Signal("b", Direction.INPUT))
        self._signal_model.add_signal(Signal("y", Direction.OUTPUT))
        self.vhdlPreviewWidget.clear()

    def _on_signals_changed(self):
        old = self._tt_model   # keep ref for output-preservation
        self._tt_model = TruthTableModel(self)
        self._tt_model.rebuild(self._signal_model)
        self._tt_model.preserve_outputs(old)
        self.truthTableWidget.set_model(self._tt_model)
        n_in  = len(self._signal_model.inputs())
        n_out = len(self._signal_model.outputs())
        n_rows = 2 ** sum(
            s.width for s in self._signal_model.inputs()
        ) if n_in else 1
        self._status(
            f"{n_in} input(s)  {n_out} output(s)  →  {n_rows} row(s)"
        )

    def _on_generate(self):
        entity = self.lineEditEntityName.text().strip() or "combinational"
        arch   = self.lineEditArchName.text().strip()   or "rtl"
        # Map combo index to dc_value: 0→'-', 1→'1', 2→'0'
        dc_map  = {0: "-", 1: "1", 2: "0"}
        dc_value = dc_map.get(self.comboDontCare.currentIndex(), "-")
        try:
            gen  = CombinationalVHDLGenerator()
            code = gen.generate(entity, arch, self._signal_model,
                                self._tt_model, dc_value=dc_value)
            self.vhdlPreviewWidget.set_vhdl(code)
            n_out  = len(self._signal_model.outputs())
            n_rows = self._tt_model.rowCount()
            self._status(
                f"Generated {n_out} when-else block(s) for {n_rows} row(s). "
                f"Output X → '{dc_value}'."
            )
        except Exception as e:
            self._status(f"Generation error: {e}")

    def _on_copy_vhdl(self):
        code = self.vhdlPreviewWidget.get_vhdl()
        if code.strip():
            QApplication.clipboard().setText(code)
            self._status(tr("status_vhdl_copied"))
        else:
            self._status("Nothing to copy — generate VHDL first.")

    def _on_save_vhdl(self):
        code = self.vhdlPreviewWidget.get_vhdl()
        if not code.strip():
            self._status("Nothing to save — generate VHDL first.")
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Save VHDL file", "", "VHDL Files (*.vhd);;All Files (*)")
        if path:
            with open(path, "w", encoding="utf-8") as f:
                f.write(code)
            self._status(f"Saved: {path}")

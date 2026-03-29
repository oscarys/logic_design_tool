"""
widgets/sequential_widget.py
Loads sequential_tab.ui — wires AsmToolbar, signal manager,
ASM canvas, validation and VHDL generation.
"""

import os
from PyQt6.QtWidgets import (
    QWidget, QFileDialog, QApplication,
    QDialog, QVBoxLayout, QTextEdit, QDialogButtonBox,
    QLabel, QMessageBox
)
from PyQt6.QtCore import Qt
from PyQt6 import uic

from models.signal_model import SignalModel, Signal, Direction
from widgets.signal_manager_widget import SignalManagerWidget
from widgets.asm_toolbar import AsmToolbar
from generators.asm_validator import validate, Severity
from generators.sequential_vhdl import SequentialVHDLGenerator
from i18n import tr

UI_PATH = os.path.join(os.path.dirname(__file__), "..", "ui", "sequential_tab.ui")


# ── validation report dialog ──────────────────────────────────────────── #
class ValidationDialog(QDialog):
    def __init__(self, messages, parent=None):
        super().__init__(parent)
        self.setWindowTitle("ASM Validation Report")
        self.resize(520, 340)
        layout = QVBoxLayout(self)

        has_errors = any(m.severity == Severity.ERROR for m in messages)
        summary = QLabel(
            "❌ Validation failed — fix errors before generating VHDL."
            if has_errors else
            "⚠️ Validation passed with warnings."
        )
        summary.setStyleSheet(
            "color: #c62828; font-weight: bold;" if has_errors else
            "color: #e65100; font-weight: bold;"
        )
        layout.addWidget(summary)

        from PyQt6.QtGui import QFont
        report = QTextEdit()
        report.setReadOnly(True)
        report.setFont(QFont("Courier New", 9))
        text_lines = []
        for m in messages:
            icon = {"ERROR": "❌", "WARNING": "⚠️", "INFO": "ℹ️"}.get(
                m.severity.value, "•")
            text_lines.append(f"{icon}  {m}")
        report.setPlainText("\n".join(text_lines))
        layout.addWidget(report)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        buttons.accepted.connect(self.accept)
        layout.addWidget(buttons)
        self._has_errors = has_errors

    def has_errors(self) -> bool:
        return self._has_errors


# ── main widget ───────────────────────────────────────────────────────── #
class SequentialWidget(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        uic.loadUi(UI_PATH, self)

        # ── signal model ──
        self._signal_model = SignalModel(self)

        # ── replace placeholder tableSignals with SignalManagerWidget ──
        self._signal_mgr = SignalManagerWidget(
            self._signal_model, show_bus=False, parent=self)
        right_layout = self.rightPanel.layout()
        for i in range(right_layout.count()):
            item = right_layout.itemAt(i)
            if item and item.widget() is self.tableSignals:
                right_layout.removeWidget(self.tableSignals)
                self.tableSignals.deleteLater()
                right_layout.insertWidget(i, self._signal_mgr)
                break

        # ── wire AsmToolbar → canvas ──
        self.asmToolbar.connect_tool_changed(self._on_tool_selected)
        self.asmToolbar.connect_delete(self._on_delete_selected)

        # ── keep hub output-signal list in sync with signal model ──
        self._signal_model.changed.connect(self._update_hub_outputs)

        # ── VHDL preview buttons ──
        self.btnValidate.clicked.connect(self._on_validate)
        self.btnGenerate.clicked.connect(self._on_generate)
        self.btnCopyVHDL.clicked.connect(self._on_copy_vhdl)
        self.btnSaveVHDL.clicked.connect(self._on_save_vhdl)

        # ── seed signals ──
        self._signal_model.add_signal(Signal("clk", Direction.INPUT))
        self._signal_model.add_signal(Signal("rst", Direction.INPUT))
        self._signal_model.add_signal(Signal("x",   Direction.INPUT))
        self._signal_model.add_signal(Signal("z",   Direction.OUTPUT))
        self._update_hub_outputs()

        # ── simulation panel (collapsible at bottom) ──
        from PyQt6.QtWidgets import QSplitter
        from widgets.simulation_panel import SimulationPanel
        self._sim_panel = SimulationPanel(self)
        self._sim_panel.setVisible(False)

        main_layout = self.layout()
        for i in range(main_layout.count()):
            item = main_layout.itemAt(i)
            if item and item.widget() is self.splitterMain:
                main_layout.removeWidget(self.splitterMain)
                vsplit = QSplitter()
                vsplit.setOrientation(Qt.Orientation.Vertical)
                vsplit.addWidget(self.splitterMain)
                vsplit.addWidget(self._sim_panel)
                vsplit.setSizes([600, 250])
                vsplit.setCollapsible(1, True)
                main_layout.insertWidget(i, vsplit)
                self._vsplitter = vsplit
                break

        # ── wire simulate button from .ui ──
        self.btnSimulate.toggled.connect(self._on_simulate_toggled)

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #
    def retranslate_ui(self):
        self.labelEntityName.setText(tr("tt_entity"))
        self.lineEditEntityName.setPlaceholderText(tr("hint_entity_seq"))
        self.labelArchName.setText(tr("tt_arch"))
        self.lineEditArchName.setPlaceholderText(tr("hint_arch"))
        self.labelSignals.setText(tr("sig_title"))
        self.labelPreview.setText(tr("lbl_vhdl_preview"))
        self.btnValidate.setText("✔ " + tr("vhdl_validate"))
        self.btnGenerate.setText("⚡ " + tr("vhdl_generate"))
        self.btnCopyVHDL.setText("⎘ " + tr("vhdl_copy"))
        self.btnSaveVHDL.setText("💾 " + tr("vhdl_save"))
        self.asmToolbar.retranslate_ui()
        self.asmCanvasWidget.retranslate_ui()
        if hasattr(self, '_signal_mgr'):
            self._signal_mgr.retranslate_ui()
        self.btnSimulate.setText("⚙ " + tr("sim_start"))
        if hasattr(self, '_sim_panel'):
            self._sim_panel.retranslate_ui()

    def _reset(self):
        """Clear signals and canvas for a new project."""
        from widgets.asm_items import BaseAsmItem, ConnectLine
        scene = self.asmCanvasWidget._scene
        for it in list(scene.items()):
            if isinstance(it, (BaseAsmItem, ConnectLine)):
                scene.removeItem(it)
        self._signal_model.clear()
        self.lineEditEntityName.clear()
        self.lineEditArchName.clear()
        self._signal_model.add_signal(Signal("clk", Direction.INPUT))
        self._signal_model.add_signal(Signal("rst", Direction.INPUT))
        self._signal_model.add_signal(Signal("x",   Direction.INPUT))
        self._signal_model.add_signal(Signal("z",   Direction.OUTPUT))
        self.vhdlPreviewWidget.clear()
        self._update_hub_outputs()

    def _on_simulate_toggled(self, checked: bool):
        if checked:
            self._start_simulation()
        else:
            self._stop_simulation()

    def _start_simulation(self):
        from generators.asm_validator import validate, Severity
        from simulation.fsm_engine import FsmEngine
        asm_data = self.asmCanvasWidget.get_asm_data()
        msgs = validate(asm_data, self._signal_model)
        errors = [m for m in msgs if m.severity == Severity.ERROR]
        if errors:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.critical(
                self, tr("sim_error_title"),
                tr("sim_error_body") + "\n\n" +
                "\n".join(f"• {m.message}" for m in errors))
            self._btn_simulate.setChecked(False)
            return
        engine = FsmEngine(asm_data, self._signal_model)
        self._sim_panel.attach_engine(engine, self.asmCanvasWidget)
        self._sim_panel.setVisible(True)
        self._vsplitter.setSizes([500, 280])

    def _stop_simulation(self):
        self._sim_panel.detach()
        self._sim_panel.setVisible(False)

    def _status(self, msg: str):
        win = self.window()
        if hasattr(win, "statusBar"):
            win.statusBar().showMessage(msg)

    def _update_hub_outputs(self):
        """Keep the ASM hub's signal lists in sync with the signal model."""
        hub = self.asmCanvasWidget._hub
        hub._output_signals = [(s.name, s.width)
                                for s in self._signal_model.outputs()]
        non_clk_rst = [s for s in self._signal_model.inputs()
                       if s.name not in ("clk", "rst")]
        hub._input_signals             = [s.name  for s in non_clk_rst]
        hub._input_signals_with_width  = [(s.name, s.width) for s in non_clk_rst]

    def _clk_name(self) -> str:
        for s in self._signal_model.inputs():
            if "clk" in s.name.lower() or "clock" in s.name.lower():
                return s.name
        ins = self._signal_model.inputs()
        return ins[0].name if ins else "clk"

    def _rst_name(self) -> str:
        for s in self._signal_model.inputs():
            if "rst" in s.name.lower() or "reset" in s.name.lower():
                return s.name
        ins = self._signal_model.inputs()
        return ins[1].name if len(ins) > 1 else "rst"

    def _run_validation(self) -> tuple[list, bool]:
        asm_data = self.asmCanvasWidget.get_asm_data()
        msgs = validate(asm_data, self._signal_model)
        has_errors = any(m.severity == Severity.ERROR for m in msgs)
        return msgs, has_errors

    # ------------------------------------------------------------------ #
    # Slots
    # ------------------------------------------------------------------ #
    def _on_tool_selected(self, tool: str):
        self.asmCanvasWidget.set_tool(tool)
        self._status(f"Tool: {tool}")

    def _on_delete_selected(self):
        self.asmCanvasWidget.delete_selected()
        self._status("Selected item(s) deleted.")

    def _on_validate(self):
        msgs, has_errors = self._run_validation()
        if not msgs:
            self._status("✔ ASM is valid — no issues found.")
            QMessageBox.information(self, "Validation",
                                    "✔ ASM is valid — no issues found.")
            return
        dlg = ValidationDialog(msgs, self)
        dlg.exec()
        n_err  = sum(1 for m in msgs if m.severity == Severity.ERROR)
        n_warn = sum(1 for m in msgs if m.severity == Severity.WARNING)
        self._status(f"Validation: {n_err} error(s), {n_warn} warning(s).")

    def _on_generate(self):
        msgs, has_errors = self._run_validation()
        if has_errors:
            dlg = ValidationDialog(msgs, self)
            dlg.exec()
            self._status("Generation blocked — fix validation errors first.")
            return
        entity = self.lineEditEntityName.text().strip() or "fsm"
        arch   = self.lineEditArchName.text().strip()   or "rtl"
        try:
            gen  = SequentialVHDLGenerator()
            code = gen.generate(
                entity_name  = entity,
                arch_name    = arch,
                signal_model = self._signal_model,
                asm_data     = self.asmCanvasWidget.get_asm_data(),
                clk_name     = self._clk_name(),
                rst_name     = self._rst_name(),
            )
            self.vhdlPreviewWidget.set_vhdl(code)
            n_states = len(self.asmCanvasWidget.get_state_names())
            base_msg = f"Generated FSM with {n_states} state(s)."
            if msgs:
                base_msg += f"  ⚠️ {len(msgs)} warning(s) — check validate report."
            self._status(base_msg)
        except Exception as e:
            self._status(f"Generation error: {e}")

    def _on_copy_vhdl(self):
        code = self.vhdlPreviewWidget.get_vhdl()
        if code.strip():
            QApplication.clipboard().setText(code)
            self._status(tr("status_vhdl_copied"))
        else:
            self._status("Nothing to copy — generate first.")

    def _on_save_vhdl(self):
        code = self.vhdlPreviewWidget.get_vhdl()
        if not code.strip():
            self._status("Nothing to save — generate first.")
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Save VHDL file", "", "VHDL Files (*.vhd);;All Files (*)")
        if path:
            with open(path, "w", encoding="utf-8") as f:
                f.write(code)
            self._status(f"Saved: {path}")

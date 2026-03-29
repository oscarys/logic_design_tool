"""
widgets/simulation_panel.py
Collapsible simulation panel for the Sequential tab.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QSlider, QComboBox, QLineEdit, QFrame, QSizePolicy, QFileDialog
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont

from i18n import tr
from widgets.timing_diagram_widget import TimingDiagramWidget

HEADER_FONT = QFont("Arial", 8, QFont.Weight.Bold)


class SimulationPanel(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self._engine        = None
        self._running       = False
        self._timer         = QTimer(self)
        self._timer.timeout.connect(self._do_step)
        self._input_widgets: dict[str, QWidget] = {}
        self._highlighted_state: str | None     = None
        self._canvas_widget = None

        self._build_ui()

    # ── UI construction ───────────────────────────────────────────────── #

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(4, 4, 4, 4)
        root.setSpacing(4)

        # ── controls bar ──
        ctrl = QHBoxLayout()

        self._btn_reset = QPushButton("⏹ " + tr("sim_reset"))
        self._btn_step  = QPushButton("▶| " + tr("sim_step"))
        self._btn_run   = QPushButton("▶ "  + tr("sim_run"))
        self._btn_pause = QPushButton("⏸ "  + tr("sim_pause"))
        self._btn_pause.setEnabled(False)
        for btn in (self._btn_reset, self._btn_step,
                    self._btn_run, self._btn_pause):
            btn.setFixedHeight(26)
            ctrl.addWidget(btn)

        ctrl.addSpacing(12)
        self._lbl_speed = QLabel(tr("sim_speed"))
        ctrl.addWidget(self._lbl_speed)
        self._speed_slider = QSlider(Qt.Orientation.Horizontal)
        self._speed_slider.setRange(1, 20)
        self._speed_slider.setValue(5)
        self._speed_slider.setFixedWidth(100)
        ctrl.addWidget(self._speed_slider)

        ctrl.addSpacing(20)
        self._lbl_state = QLabel(tr("sim_state") + ": —")
        self._lbl_state.setFont(HEADER_FONT)
        ctrl.addWidget(self._lbl_state)
        ctrl.addSpacing(12)
        self._lbl_cycle = QLabel(tr("sim_cycle") + ": 0")
        ctrl.addWidget(self._lbl_cycle)
        ctrl.addStretch()

        self._btn_timing = QPushButton("📊 " + tr("sim_timing"))
        self._btn_timing.setFixedHeight(26)
        self._btn_timing.setEnabled(False)
        ctrl.addWidget(self._btn_timing)

        root.addLayout(ctrl)

        # ── inputs bar ──
        self._inputs_bar       = QHBoxLayout()
        self._inputs_container = QHBoxLayout()
        self._lbl_inputs = QLabel(tr("sim_inputs") + ":")
        self._inputs_bar.addWidget(self._lbl_inputs)
        self._inputs_bar.addLayout(self._inputs_container)
        self._inputs_bar.addStretch()
        root.addLayout(self._inputs_bar)

        # ── separator ──
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        root.addWidget(line)

        # ── live timing diagram ──
        self._diagram = TimingDiagramWidget(self)
        self._diagram.setMinimumHeight(140)
        root.addWidget(self._diagram)

        # ── connect ──
        self._btn_reset.clicked.connect(self._on_reset)
        self._btn_step.clicked.connect(self._do_step)
        self._btn_run.clicked.connect(self._on_run)
        self._btn_pause.clicked.connect(self._on_pause)
        self._btn_timing.clicked.connect(self._on_export_timing)

    # ── public API ────────────────────────────────────────────────────── #

    def attach_engine(self, engine, canvas_widget):
        self._engine        = engine
        self._canvas_widget = canvas_widget
        self._build_input_widgets()
        self._diagram.set_signals(
            [s.name for s in engine.input_signals()],
            [s.name for s in engine.output_signals()])
        self._on_reset()

    def detach(self):
        self._on_pause()
        self._clear_highlight()
        self._engine = None
        self._clear_input_widgets()
        self._diagram.clear()
        self._btn_timing.setEnabled(False)
        self._lbl_state.setText(tr("sim_state") + ": —")
        self._lbl_cycle.setText(tr("sim_cycle") + ": 0")

    def retranslate_ui(self):
        self._btn_reset.setText( "⏹ " + tr("sim_reset"))
        self._btn_step.setText(  "▶| " + tr("sim_step"))
        self._btn_run.setText(   "▶ "  + tr("sim_run"))
        self._btn_pause.setText( "⏸ "  + tr("sim_pause"))
        self._btn_timing.setText("📊 " + tr("sim_timing"))
        self._lbl_speed.setText(tr("sim_speed"))
        self._lbl_inputs.setText(tr("sim_inputs") + ":")
        self._lbl_state.setText(tr("sim_state") + f": {self._engine.current_state() if self._engine else '—'}")
        self._lbl_cycle.setText(tr("sim_cycle") + f": {self._engine.cycle() if self._engine else 0}")

    # ── input widgets ──────────────────────────────────────────────────── #

    def _build_input_widgets(self):
        self._clear_input_widgets()
        if not self._engine:
            return
        for sig in self._engine.input_signals():
            self._inputs_container.addWidget(QLabel(f"{sig.name}="))
            if sig.width == 1:
                combo = QComboBox()
                combo.addItems(["0", "1"])
                combo.setFixedWidth(55)
                self._inputs_container.addWidget(combo)
                self._input_widgets[sig.name] = combo
            else:
                le = QLineEdit("0" * sig.width)
                le.setFixedWidth(max(60, sig.width * 12))
                le.setMaxLength(sig.width)
                self._inputs_container.addWidget(le)
                self._input_widgets[sig.name] = le

    def _clear_input_widgets(self):
        self._input_widgets.clear()
        while self._inputs_container.count():
            item = self._inputs_container.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def _read_inputs(self) -> dict[str, str]:
        result = {}
        for name, w in self._input_widgets.items():
            if isinstance(w, QComboBox):
                result[name] = w.currentText()
            else:
                result[name] = w.text().strip() or "0"
        return result

    # ── simulation control ────────────────────────────────────────────── #

    def _on_reset(self):
        if not self._engine:
            return
        self._on_pause()
        self._engine.reset()
        self._diagram.clear()
        self._btn_timing.setEnabled(False)
        self._clear_highlight()
        outputs = self._engine._evaluate_outputs(self._engine.current_state())
        self._update_display(self._engine.current_state(),
                             self._engine.cycle())
        self._highlight_state(self._engine.current_state())

    def _do_step(self):
        if not self._engine:
            return
        inputs    = self._read_inputs()
        new_state, outputs = self._engine.step(inputs)
        self._update_display(new_state, self._engine.cycle())
        self._highlight_state(new_state)
        self._append_trace(self._engine.cycle(), new_state, inputs, outputs)

    def _on_run(self):
        if not self._engine or self._running:
            return
        self._running = True
        self._btn_run.setEnabled(False)
        self._btn_pause.setEnabled(True)
        self._update_timer_interval()
        self._speed_slider.valueChanged.connect(self._update_timer_interval)
        self._timer.start()

    def _on_pause(self):
        self._running = False
        self._timer.stop()
        self._btn_run.setEnabled(True)
        self._btn_pause.setEnabled(False)
        try:
            self._speed_slider.valueChanged.disconnect(
                self._update_timer_interval)
        except Exception:
            pass

    def _update_timer_interval(self):
        self._timer.setInterval(int(1200 / self._speed_slider.value()))

    # ── display ───────────────────────────────────────────────────────── #

    def _update_display(self, state: str, cycle: int):
        self._lbl_state.setText(tr("sim_state") + f": {state}")
        self._lbl_cycle.setText(tr("sim_cycle") + f": {cycle}")

    def _append_trace(self, cycle: int, state: str,
                       inputs: dict, outputs: dict):
        self._btn_timing.setEnabled(True)
        self._diagram.append_cycle({
            "cycle":   cycle,
            "state":   state,
            "inputs":  inputs,
            "outputs": outputs,
        })

    # ── canvas highlight ──────────────────────────────────────────────── #

    def _highlight_state(self, state_name: str):
        self._clear_highlight()
        if not self._canvas_widget:
            return
        from widgets.asm_items import StateItem
        scene = self._canvas_widget._scene
        for item in scene.items():
            if isinstance(item, StateItem) and item.name() == state_name:
                item.set_sim_highlight(True)
                self._highlighted_state = state_name
                scene.update()
                break

    def _clear_highlight(self):
        if not self._canvas_widget or not self._highlighted_state:
            return
        from widgets.asm_items import StateItem
        scene = self._canvas_widget._scene
        for item in scene.items():
            if isinstance(item, StateItem):
                item.set_sim_highlight(False)
        self._highlighted_state = None
        scene.update()

    # ── timing diagram export ─────────────────────────────────────────── #

    def _on_export_timing(self):
        if self._diagram.row_count() == 0:
            return
        path, _ = QFileDialog.getSaveFileName(
            self, tr("sim_timing"), "timing_diagram.png",
            "PNG Image (*.png)")
        if not path:
            return
        img = self._diagram.render_to_image()
        img.save(path)
        if hasattr(self.window(), "statusBar"):
            self.window().statusBar().showMessage(
                tr("status_vhdl_saved", path))

"""
project/project_manager.py
Serialises and deserialises a complete .vhdlt project (JSON).

Schema v1
---------
{
  "version": 1,
  "combinational": {
    "entity":   str,
    "arch":     str,
    "dc_value": str,          # '-' | '0' | '1'
    "signals":  [ {name, direction, width, bus_group}, ... ],
    "truth_table": [ [str, ...], ... ]   # output columns only, row-major
  },
  "sequential": {
    "entity":  str,
    "arch":    str,
    "signals": [ {name, direction, width}, ... ],
    "states":  [
      {
        "name": str, "x": float, "y": float,
        "outputs": str, "is_initial": bool,
        "condition": null | {
          "type": "unconditional",
          "next_state": str
        } | {
          "type": "diamond",
          "condition": str,
          "yes_state": str,
          "no_state":  str
        } | {
          "type": "hexagon",
          "condition_vars": str,
          "exits": [ {"label": str, "state": str}, ... ]
        }
      }, ...
    ]
  }
}
"""

import json
import pathlib


SCHEMA_VERSION = 1
FILE_EXT       = ".vhdlt"
FILE_FILTER    = f"VHDL Tool Project (*{FILE_EXT});;All Files (*)"


# ── serialise ──────────────────────────────────────────────────────────── #

def save_project(path: str,
                 comb_widget,
                 seq_widget) -> None:
    """Serialise both tabs and write to *path*."""
    data = {
        "version":      SCHEMA_VERSION,
        "combinational": _save_combinational(comb_widget),
        "sequential":    _save_sequential(seq_widget),
    }
    pathlib.Path(path).write_text(
        json.dumps(data, indent=2, ensure_ascii=False),
        encoding="utf-8")


def _save_combinational(w) -> dict:
    sm = w._signal_model
    tt = w._tt_model

    signals = []
    for s in sm.all_signals():
        signals.append({
            "name":      s.name,
            "direction": s.direction.value,
            "width":     s.width,
            "bus_group": s.bus_group,
        })

    # Save only output column values (inputs are deterministic)
    n_in   = tt._n_input_bits
    n_rows = tt.rowCount()
    n_out  = len(tt._output_cols)
    truth_table = []
    for r in range(n_rows):
        row = tt.row_data(r)
        truth_table.append(row[n_in:])   # output values only

    # dc_value from combo index
    dc_map   = {0: "-", 1: "1", 2: "0"}
    dc_value = dc_map.get(w.comboDontCare.currentIndex(), "-")

    return {
        "entity":      w.lineEditEntityName.text().strip(),
        "arch":        w.lineEditArchName.text().strip(),
        "dc_value":    dc_value,
        "signals":     signals,
        "truth_table": truth_table,
    }


def _save_sequential(w) -> dict:
    from widgets.asm_items import StateItem

    sm = w._signal_model
    signals = []
    for s in sm.all_signals():
        signals.append({
            "name":      s.name,
            "direction": s.direction.value,
            "width":     s.width,
        })

    scene  = w.asmCanvasWidget._scene
    states = []
    for it in scene.items():
        if not isinstance(it, StateItem):
            continue
        state_dict = {
            "name":       it.name(),
            "x":          it.x(),
            "y":          it.y(),
            "outputs":    it.outputs(),
            "is_initial": it.is_initial(),
            "condition":  None,
        }
        cb = it.condition_block()
        if cb is not None:
            state_dict["condition"] = cb.to_dict()
            state_dict["condition"].pop("type_key", None)
        states.append(state_dict)

    return {
        "entity":  w.lineEditEntityName.text().strip(),
        "arch":    w.lineEditArchName.text().strip(),
        "signals": signals,
        "states":  states,
    }


# ── deserialise ────────────────────────────────────────────────────────── #

def load_project(path: str,
                 comb_widget,
                 seq_widget) -> None:
    """Read *path* and restore both tabs."""
    raw  = pathlib.Path(path).read_text(encoding="utf-8")
    data = json.loads(raw)

    if data.get("version", 0) != SCHEMA_VERSION:
        raise ValueError(
            f"Unsupported project version: {data.get('version')}. "
            f"Expected {SCHEMA_VERSION}.")

    _load_combinational(data.get("combinational", {}), comb_widget)
    _load_sequential(   data.get("sequential",    {}), seq_widget)


def _load_combinational(d: dict, w) -> None:
    from models.signal_model import Signal, Direction
    from models.truth_table_model import TruthTableModel

    # Entity / arch names
    w.lineEditEntityName.setText(d.get("entity", ""))
    w.lineEditArchName.setText(  d.get("arch",   ""))

    # dc_value combo
    dc_idx = {"-": 0, "1": 1, "0": 2}.get(d.get("dc_value", "-"), 0)
    w.comboDontCare.setCurrentIndex(dc_idx)

    # Signals
    sm = w._signal_model
    sm.clear()
    for s in d.get("signals", []):
        sm.add_signal(Signal(
            name      = s["name"],
            direction = Direction(s["direction"]),
            width     = s.get("width", 1),
            bus_group = s.get("bus_group"),
        ))

    # Truth table — rebuild then restore output values
    tt = TruthTableModel(w)
    tt.rebuild(sm)
    saved_rows = d.get("truth_table", [])
    n_in = tt._n_input_bits
    for r, out_vals in enumerate(saved_rows):
        if r >= tt.rowCount():
            break
        for c, val in enumerate(out_vals):
            col = n_in + c
            if col < tt.columnCount():
                tt.setData(tt.index(r, col), val)

    w._tt_model = tt
    w.truthTableWidget.set_model(tt)


def _load_sequential(d: dict, w) -> None:
    from models.signal_model import Signal, Direction
    from widgets.asm_items import (StateItem, DiamondItem, HexagonItem,
                                   UnconditionalItem)

    # Entity / arch names
    w.lineEditEntityName.setText(d.get("entity", ""))
    w.lineEditArchName.setText(  d.get("arch",   ""))

    # Signals
    sm = w._signal_model
    sm.clear()
    for s in d.get("signals", []):
        sm.add_signal(Signal(
            name      = s["name"],
            direction = Direction(s["direction"]),
            width     = s.get("width", 1),
        ))
    w._update_hub_outputs()

    # Clear canvas
    scene = w.asmCanvasWidget._scene
    from widgets.asm_items import BaseAsmItem, ConnectLine
    for it in list(scene.items()):
        if isinstance(it, (BaseAsmItem, ConnectLine)):
            scene.removeItem(it)

    hub = w.asmCanvasWidget._hub

    # Place states
    for sd in d.get("states", []):
        state = StateItem(hub,
                          name       = sd["name"],
                          outputs    = sd.get("outputs", ""),
                          is_initial = sd.get("is_initial", False))
        state.setPos(sd.get("x", 0), sd.get("y", 0))
        state._refresh_name_display()
        scene.addItem(state)

        # Restore condition block
        cond = sd.get("condition")
        if cond:
            ctype = cond.get("type")
            if ctype == "unconditional":
                block = UnconditionalItem(hub, cond.get("next_state", ""))
            elif ctype == "diamond":
                block = DiamondItem(hub,
                                    condition = cond.get("condition", ""),
                                    yes_state = cond.get("yes_state", ""),
                                    no_state  = cond.get("no_state",  ""))
            elif ctype == "hexagon":
                block = HexagonItem(hub,
                                    condition_vars = cond.get("condition_vars", ""),
                                    exits          = cond.get("exits", []))
            else:
                block = None

            if block:
                state._attach_condition(block)

    # Broadcast state list so dropdowns populate
    names = [it.name() for it in scene.items()
             if isinstance(it, StateItem)]
    hub.state_list_changed.emit(names)

"""
simulation/fsm_engine.py
Pure-Python Moore FSM simulator.

Takes asm_data (from AsmScene.get_asm_data()) and a signal model,
evaluates transitions each clock cycle.
"""

import re


class FsmEngine:
    """
    Stateful Moore FSM simulator.

    Usage
    -----
        engine = FsmEngine(asm_data, signal_model)
        engine.reset()
        state, outputs = engine.step({"x": "1"})
    """

    def __init__(self, asm_data: dict, signal_model):
        self._asm_data     = asm_data
        self._signal_model = signal_model
        self._states       = {s["name"]: s for s in asm_data.get("states", [])}
        self._initial      = self._find_initial()
        self._current      = self._initial
        self._cycle        = 0

    # ── lifecycle ─────────────────────────────────────────────────────── #

    def reset(self):
        self._current = self._initial
        self._cycle   = 0

    def step(self, inputs: dict[str, str]) -> tuple[str, dict[str, str]]:
        """
        Advance one clock cycle.

        Parameters
        ----------
        inputs : {signal_name: "0"/"1" or bit-string for buses}

        Returns
        -------
        (new_state_name, {output_name: value_string})
        """
        next_state = self._evaluate_transition(self._current, inputs)
        self._current = next_state
        self._cycle  += 1
        outputs = self._evaluate_outputs(self._current)
        return self._current, outputs

    # ── accessors ─────────────────────────────────────────────────────── #

    def current_state(self) -> str:
        return self._current

    def cycle(self) -> int:
        return self._cycle

    def initial_state(self) -> str:
        return self._initial

    def state_names(self) -> list[str]:
        return list(self._states.keys())

    def input_signals(self) -> list:
        """Return list of non-clk/rst input Signal objects."""
        return [s for s in self._signal_model.inputs()
                if s.name not in ("clk", "rst")]

    def output_signals(self) -> list:
        return list(self._signal_model.outputs())

    # ── transition evaluation ─────────────────────────────────────────── #

    def _find_initial(self) -> str:
        for s in self._asm_data.get("states", []):
            if s.get("is_initial"):
                return s["name"]
        states = self._asm_data.get("states", [])
        return states[0]["name"] if states else ""

    def _evaluate_transition(self, state_name: str,
                              inputs: dict[str, str]) -> str:
        state = self._states.get(state_name)
        if not state:
            return state_name

        cond = state.get("condition")
        if not cond:
            return state_name   # no transition defined → stay

        ctype = cond.get("type")

        if ctype == "unconditional":
            ns = cond.get("next_state", "")
            return ns if ns in self._states else state_name

        elif ctype == "diamond":
            sig  = cond.get("condition", "").strip()
            yes  = cond.get("yes_state", "")
            no   = cond.get("no_state",  "")
            val  = inputs.get(sig, "0")
            result = yes if _is_true(val) else no
            return result if result in self._states else state_name

        elif ctype == "hexagon":
            vars_str  = cond.get("condition_vars", "")
            var_list  = [v.strip() for v in vars_str.split(",") if v.strip()]
            exits     = cond.get("exits", [])

            # Build the composite label from current input values
            current_label = " ".join(
                inputs.get(v, "0") for v in var_list)

            for ex in exits:
                label = ex.get("label", "")
                ns    = ex.get("state",  "")
                if not ns or ns not in self._states:
                    continue
                if _label_matches(label, current_label):
                    return ns

            return state_name  # no match → stay

        return state_name

    def _evaluate_outputs(self, state_name: str) -> dict[str, str]:
        state   = self._states.get(state_name, {})
        outputs = {}
        text    = state.get("outputs", "").strip()

        bus_re  = re.compile(r'(\w+)\s*(?:<=|=)\s*["\']([01XxZz\-]+)["\']')
        explicit: dict[str, str] = {}
        for m in bus_re.finditer(text):
            explicit[m.group(1).strip()] = m.group(2).strip()

        clean  = bus_re.sub(" ", text)
        tokens = set(re.split(r'[\s,;]+', clean)) - {""}

        for sig in self._signal_model.outputs():
            if sig.name in explicit:
                outputs[sig.name] = explicit[sig.name]
            elif sig.name in tokens:
                outputs[sig.name] = "1" if sig.width == 1 else "1" * sig.width
            else:
                outputs[sig.name] = "0" if sig.width == 1 else "0" * sig.width

        return outputs


# ── helpers ────────────────────────────────────────────────────────────── #

def _is_true(val: str) -> bool:
    return val.strip() not in ("0", "", "false", "False")


def _label_matches(label: str, current: str) -> bool:
    """
    Match a hexagon exit label against the current input combination.
    Labels may contain 'X' as don't-care, and are space- or no-separator.
    current is a space-separated string of bit values.
    """
    label_bits   = label.replace(" ", "")
    current_bits = current.replace(" ", "")

    if len(label_bits) != len(current_bits):
        return False

    for lb, cb in zip(label_bits, current_bits):
        if lb.upper() == "X":
            continue
        if lb != cb:
            return False
    return True

"""
generators/asm_validator.py
Validates an ASM chart data dict before VHDL generation.

Returns a list of ValidationMessage objects (severity + text).
The generator refuses to run if any ERROR-level messages exist.
"""

from dataclasses import dataclass
from enum import Enum


class Severity(Enum):
    ERROR   = "ERROR"
    WARNING = "WARNING"
    INFO    = "INFO"


@dataclass
class ValidationMessage:
    severity: Severity
    message:  str

    def __str__(self):
        return f"[{self.severity.value}] {self.message}"


def validate(asm_data: dict, signal_model) -> list[ValidationMessage]:
    """
    asm_data  – dict from AsmScene.get_asm_data()
                keys: states, decisions, hexagons
    signal_model – SignalModel (for input/output signal names)
    """
    msgs: list[ValidationMessage] = []

    states    = asm_data.get("states",    [])
    decisions = asm_data.get("decisions", [])
    hexagons  = asm_data.get("hexagons",  [])

    def err(msg):  msgs.append(ValidationMessage(Severity.ERROR,   msg))
    def warn(msg): msgs.append(ValidationMessage(Severity.WARNING, msg))
    def info(msg): msgs.append(ValidationMessage(Severity.INFO,    msg))

    # ── 1. at least one state ──────────────────────────────────────────
    if not states:
        err("No state blocks defined — add at least one state to the canvas.")
        return msgs   # nothing else to check

    # ── 2. initial state marked ────────────────────────────────────────
    initial_states = [s for s in states if s.get("is_initial")]
    if not initial_states:
        err("No initial state marked — right-click a state and select "
            "'Set as Initial State'.")
    elif len(initial_states) > 1:
        names = ", ".join(s["name"] for s in initial_states)
        err(f"Multiple initial states marked: {names}. Only one is allowed.")

    # ── 3. unique state names ──────────────────────────────────────────
    state_names = [s["name"] for s in states]
    seen, dupes = set(), set()
    for n in state_names:
        (dupes if n in seen else seen).add(n)
    for d in dupes:
        err(f"Duplicate state name: '{d}'. All state names must be unique.")

    all_names = set(state_names)

    # ── 4. collect all transition targets ─────────────────────────────
    reachable: set[str] = set()

    for s in states:
        # Check owned condition block
        cond = s.get("condition")
        if cond:
            ctype = cond.get("type")
            sname = s["name"]
            if ctype == "unconditional":
                ns = cond.get("next_state", "")
                if not ns:
                    warn(f"State '{sname}': unconditional transition "
                         f"has no target state.")
                else:
                    reachable.add(ns)
                    if ns not in all_names:
                        err(f"State '{sname}': unconditional transition "
                            f"→ unknown state '{ns}'.")
            elif ctype == "diamond":
                for key, label in [("yes_state","Y"), ("no_state","N")]:
                    ns = cond.get(key, "")
                    if not ns:
                        warn(f"State '{sname}' diamond: "
                             f"exit '{label}' has no target state.")
                    else:
                        reachable.add(ns)
                        if ns not in all_names:
                            err(f"State '{sname}' diamond: "
                                f"exit '{label}' → unknown state '{ns}'.")
            elif ctype == "hexagon":
                for ex in cond.get("exits", []):
                    ns  = ex.get("state", "")
                    lbl = ex.get("label", "?")
                    if not ns:
                        warn(f"State '{sname}' hexagon: "
                             f"exit '{lbl}' has no target state.")
                    else:
                        reachable.add(ns)
                        if ns not in all_names:
                            err(f"State '{sname}' hexagon: "
                                f"exit '{lbl}' → unknown state '{ns}'.")

    for d in decisions:
        for key, label in [("yes_state", "Y"), ("no_state", "N")]:
            ns = d.get(key, "")
            if not ns:
                warn(f"Decision '{d.get('condition','?')}': "
                     f"exit '{label}' has no target state (dropdown = —).")
            else:
                reachable.add(ns)
                if ns not in all_names:
                    err(f"Decision '{d.get('condition','?')}': "
                        f"exit '{label}' points to non-existent state '{ns}'.")

    for h in hexagons:
        for ex in h.get("exits", []):
            ns = ex.get("state", "")
            lbl = ex.get("label", "?")
            if not ns:
                warn(f"Hexagon '{h.get('condition_vars','?')}': "
                     f"exit '{lbl}' has no target state (dropdown = —).")
            else:
                reachable.add(ns)
                if ns not in all_names:
                    err(f"Hexagon '{h.get('condition_vars','?')}': "
                        f"exit '{lbl}' points to non-existent state '{ns}'.")

    # ── 5. dead-end states ────────────────────────────────────────────
    for s in states:
        if not s.get("condition"):
            warn(f"State '{s['name']}' has no transition defined. "
                 f"Use '+ condition' on the state block to add one.")

    # ── 6. unreachable states ─────────────────────────────────────────
    # The initial state is reachable by definition; all others must appear
    # in at least one transition target
    init_name = initial_states[0]["name"] if initial_states else None
    for s in states:
        if s["name"] == init_name:
            continue
        if s["name"] not in reachable:
            warn(f"State '{s['name']}' is unreachable — "
                 f"no transition points to it.")

    # ── 7. output signals sanity ──────────────────────────────────────
    if signal_model:
        import re
        out_names = {s.name for s in signal_model.outputs()}
        # Tokens that are valid in output expressions but not signal names
        _ignore = {"", "others", "std_logic", "std_logic_vector"}
        _bit_re = re.compile(r'^[01XxZz\-]+$')   # pure bit-strings
        for s in states:
            text = s.get("outputs", "").strip()
            if not text or text in ("(outputs)", "list outputs\ne.g.: z, y"):
                continue
            tokens = set(re.split(r'[\s,;=<>\'\"()]+', text))
            unknown = {
                t for t in tokens
                if t
                and t not in out_names
                and t not in _ignore
                and not _bit_re.match(t)   # skip pure bit-strings like "11","0X"
                and not t.isdigit()        # skip plain numbers
            }
            if unknown and out_names:
                warn(f"State '{s['name']}': output box contains unrecognised "
                     f"token(s): {', '.join(sorted(unknown))}. "
                     f"Known outputs: {', '.join(sorted(out_names))}.")

    return msgs

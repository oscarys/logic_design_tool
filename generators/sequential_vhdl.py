"""
generators/sequential_vhdl.py
Generates VHDL-2008 for a Moore FSM from an ASM chart.

Architecture — three concurrent when-else statements, NO processes:

  -- 1. next-state logic (combinational — failsafe holds current state)
  next_state <=
      S1 when current_state = S0 and x = '1' else
      S0 when current_state = S0 else
      ...
      current_state;   -- hold state if no transition matches

  -- 2. output logic (Moore — depends only on current_state)
  z <= '1' when current_state = S2 else '0';

  -- 3. state register (clean — async reset + clock, no extra failsafe)
  current_state <=
      S0         when rst = '1' else
      next_state when rising_edge(clk);
"""

from models.signal_model import SignalModel, Direction


# ── helpers ────────────────────────────────────────────────────────────── #

def _vhdl_type(sig) -> str:
    if sig.width == 1:
        return "std_logic"
    return f"std_logic_vector({sig.width - 1} downto 0)"


def _port_lines(signal_model: SignalModel,
                clk_name: str, rst_name: str) -> list[str]:
    lines = []
    sigs  = signal_model.all_signals()
    for i, sig in enumerate(sigs):
        sep = ";" if i < len(sigs) - 1 else ""
        lines.append(
            f"        {sig.name:<16}: {sig.direction.value:<4} "
            f"{_vhdl_type(sig)}{sep}"
        )
    return lines


def _parse_outputs(output_text: str) -> list[str]:
    """
    Split a state's output text into individual assignment strings.
    Accepts newline or semicolon separated entries.
    Returns cleaned strings like ["z <= '1'", "y <= '0'"].
    """
    raw = output_text.replace(";", "\n")
    parts = [p.strip().rstrip(";") for p in raw.splitlines()]
    return [p for p in parts
            if p and p not in ("(outputs)", "(output assignments)")]


def _collect_output_signals(states: list[dict],
                             signal_model: SignalModel) -> dict[str, list]:
    """
    For each output signal, collect (state_name, vhdl_value) pairs.

    Convention — in a state's output box the user lists:
      • Signal names to ASSERT (set to '1'), one per line or comma/space separated
          e.g.  "z"  or  "z, y"  or  "z\\ny"
      • For bus outputs, optionally an explicit value:
          e.g.  "addr = \\"101\\""  or  "addr=\\"101\\""

    Any output signal NOT listed in a state's box is implicitly '0' / (others=>'0')
    and does NOT generate a when branch (the final else handles it).
    """
    import re
    out_sigs = {s.name: s for s in signal_model.outputs()}
    # result[sig_name] = list of (state_name, vhdl_value)
    result: dict[str, list] = {name: [] for name in out_sigs}

    # Regex for explicit bus assignment:  name = "101"  or  name <= "101"
    bus_assign_re = re.compile(
        r'(\w+)\s*(?:<=|=)\s*["\']([01XxZz\-]+)["\']'
    )

    for state in states:
        sname = state["name"]
        text  = state.get("outputs", "").strip()

        if not text or text in ("(outputs)", "(output assignments)"):
            continue

        # Collect explicit bus assignments first
        explicit: dict[str, str] = {}
        for m in bus_assign_re.finditer(text):
            sig_name = m.group(1).strip()
            value    = m.group(2).strip()
            if sig_name in out_sigs:
                sig = out_sigs[sig_name]
                if sig.width == 1:
                    explicit[sig_name] = f"'{value}'"
                else:
                    explicit[sig_name] = f'"{value}"'

        # Tokenise remaining words — any output signal name present = asserted
        # Strip out the explicit assignment tokens so they don't double-count
        clean = bus_assign_re.sub(" ", text)
        tokens = re.split(r'[\s,;]+', clean)
        tokens = [t.strip() for t in tokens if t.strip()]

        for sig_name, sig in out_sigs.items():
            if sig_name in explicit:
                result[sig_name].append((sname, explicit[sig_name]))
            elif sig_name in tokens:
                # Scalar: assert to '1'
                if sig.width == 1:
                    result[sig_name].append((sname, "'1'"))
                else:
                    # Bus listed without value — warn-worthy but emit all-ones
                    result[sig_name].append(
                        (sname, f'(others => \'1\')'))

    return result


def _default_value(sig) -> str:
    if sig.width == 1:
        return "'0'"
    return "(others => '0')"


# ── transition table builder ───────────────────────────────────────────── #

def _build_transitions(asm_data: dict) -> list[tuple[str, str, str]]:
    """
    Build (current_state_guard, condition_expr, next_state) tuples.
    Each state owns its condition block — transitions are per-state.
    Conditional branches come first, unconditional fallback last.
    """
    states = asm_data.get("states", [])
    conditional:   list[tuple[str, str, str]] = []
    unconditional: list[tuple[str, str, str]] = []

    for s in states:
        sname = s["name"]
        cond  = s.get("condition")

        if cond:
            ctype = cond.get("type")
            if ctype == "unconditional":
                ns = cond.get("next_state", "")
                if ns:
                    unconditional.append(
                        (sname, f"current_state = {sname}", ns))
                continue   # skip the fallback below for this state
            elif ctype == "diamond":
                c  = cond.get("condition", "cond").strip()
                ys = cond.get("yes_state", "")
                ns = cond.get("no_state",  "")
                if ys:
                    conditional.append(
                        (sname,
                         f"current_state = {sname} and {c} = '1'",
                         ys))
                if ns:
                    conditional.append(
                        (sname,
                         f"current_state = {sname} and {c} = '0'",
                         ns))
            elif ctype == "hexagon":
                vars_    = cond.get("condition_vars", "").strip()
                var_list = [v.strip() for v in vars_.split(",") if v.strip()]
                for ex in cond.get("exits", []):
                    label = ex.get("label", "")
                    ns    = ex.get("state", "")
                    if not ns:
                        continue
                    terms = [f"current_state = {sname}"]
                    for i, bit in enumerate(label):
                        if i < len(var_list) and bit != "X":
                            terms.append(f"{var_list[i]} = '{bit}'")
                    conditional.append((sname, " and ".join(terms), ns))

        ns = s.get("next_state", "")
        if ns:
            unconditional.append(
                (sname, f"current_state = {sname}", ns))

    return conditional + unconditional


# ── main generator ─────────────────────────────────────────────────────── #

class SequentialVHDLGenerator:

    def generate(self, entity_name: str,
                 arch_name:   str,
                 signal_model: SignalModel,
                 asm_data:    dict,
                 clk_name:    str = "clk",
                 rst_name:    str = "rst") -> str:

        if not entity_name.strip():
            entity_name = "fsm"
        if not arch_name.strip():
            arch_name = "rtl"

        states = asm_data.get("states", [])
        initial = next(
            (s["name"] for s in states if s.get("is_initial")), 
            states[0]["name"] if states else "S0"
        )

        state_names = [s["name"] for s in states]
        transitions = _build_transitions(asm_data)
        out_assignments = _collect_output_signals(states, signal_model)

        lines = []

        # ── header ──
        lines += [
            "-- Auto-generated by VHDL Design Tool",
            "-- VHDL-2008  |  Sequential design (Moore FSM)",
            "-- Architecture: three concurrent when-else, no processes",
            "",
            "library ieee;",
            "use ieee.std_logic_1164.all;",
            "",
        ]

        # ── entity ──
        port_lines = _port_lines(signal_model, clk_name, rst_name)
        lines += [
            f"entity {entity_name} is",
            "    port (",
        ]
        lines += port_lines
        lines += [
            "    );",
            f"end entity {entity_name};",
            "",
        ]

        # ── architecture ──
        # State type declaration
        state_type = ", ".join(state_names)
        lines += [
            f"architecture {arch_name} of {entity_name} is",
            "",
            f"    type t_state is ({state_type});",
            "    signal current_state : t_state;",
            "    signal next_state    : t_state;",
            "",
            "begin",
            "",
        ]

        # ── 1. next-state concurrent when-else ──
        lines += [
            "    -- Next-state logic (combinational)",
            "    next_state <=",
        ]

        for _owner, cond_expr, nxt in transitions:
            lines.append(f"        {nxt} when {cond_expr} else")

        # Failsafe: hold current state if no transition matches
        lines.append(f"        current_state;")
        lines.append("")

        # ── 2. output logic (Moore) ──
        lines.append("    -- Output logic (Moore: depends only on current_state)")
        out_sigs = list(signal_model.outputs())
        if not out_sigs:
            lines.append("    -- (no output signals defined)")
        else:
            for sig in out_sigs:
                assignments = out_assignments.get(sig.name, [])
                if sig.width == 1:
                    lhs = sig.name
                    if not assignments:
                        lines.append(
                            f"    {lhs} <= {_default_value(sig)};")
                    else:
                        lines.append(f"    {lhs} <=")
                        for sname, val in assignments:
                            lines.append(
                                f"        {val} when current_state = {sname} else")
                        lines.append(f"        {_default_value(sig)};")
                else:
                    # bus output — generate per-state assignments
                    lhs = sig.name
                    if not assignments:
                        lines.append(
                            f"    {lhs} <= {_default_value(sig)};")
                    else:
                        lines.append(f"    {lhs} <=")
                        for sname, val in assignments:
                            lines.append(
                                f"        {val} when current_state = {sname} else")
                        lines.append(f"        {_default_value(sig)};")
                lines.append("")

        # ── 3. state register — async reset, clocked when-else ──
        lines += [
            "    -- State register (asynchronous reset)",
            f"    current_state <=",
            f"        {initial}  when {rst_name} = '1' else",
            f"        next_state when rising_edge({clk_name});",
            "",
            f"end architecture {arch_name};",
        ]

        return "\n".join(lines)

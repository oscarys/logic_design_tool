"""i18n/en.py — English strings"""

STRINGS = {
    # ── Window / app ──────────────────────────────────────────────────── #
    "app_title":            "VHDL Design Tool",
    "untitled":             "Untitled",

    # ── Menu: File ────────────────────────────────────────────────────── #
    "menu_file":            "&File",
    "menu_new":             "&New Project",
    "menu_open":            "&Open Project…",
    "menu_save":            "&Save Project",
    "menu_save_as":         "Save Project &As…",
    "menu_quit":            "&Quit",

    # ── Menu: Edit ────────────────────────────────────────────────────── #
    "menu_edit":            "&Edit",
    "menu_undo":            "&Undo",
    "menu_redo":            "&Redo",

    # ── Menu: Settings ────────────────────────────────────────────────── #
    "menu_settings":        "&Settings",
    "menu_language":        "&Language",

    # ── Menu: Help ────────────────────────────────────────────────────── #
    "menu_help":            "&Help",
    "menu_about":           "&About…",

    # ── Tabs ──────────────────────────────────────────────────────────── #
    "tab_combinational":    "Combinational Design",
    "tab_sequential":       "Sequential Design (Moore ASM)",

    # ── Signal manager ────────────────────────────────────────────────── #
    "sig_title":            "Signals",
    "sig_col_name":         "Name",
    "sig_col_direction":    "Direction",
    "sig_col_width":        "Width",
    "sig_add":              "+ Add",
    "sig_remove":           "− Remove",
    "sig_input":            "Input",
    "sig_output":           "Output",

    # ── Truth table toolbar ───────────────────────────────────────────── #
    "tt_group":             "Group",
    "tt_ungroup":           "Ungroup",
    "tt_dc_label":          "Don't-care:",
    "tt_dc_dash":           "— (dash)",
    "tt_dc_one":            "1",
    "tt_dc_zero":           "0",
    "tt_entity":            "Entity:",
    "tt_arch":              "Architecture:",

    # ── ASM toolbar ───────────────────────────────────────────────────── #
    "asm_tool_select":      "Select / Move",
    "asm_tool_state":       "Place State",
    "asm_tool_delete":      "Delete Selected\n(or press Del)",

    # ── VHDL preview ──────────────────────────────────────────────────── #
    "vhdl_generate":        "Generate VHDL",
    "vhdl_copy":            "Copy",
    "vhdl_save":            "Save VHDL…",
    "vhdl_validate":        "Validate",

    # ── Dialogs: general ──────────────────────────────────────────────── #
    "dlg_ok":               "OK",
    "dlg_cancel":           "Cancel",
    "dlg_save":             "Save",
    "dlg_discard":          "Discard",

    # ── Dialogs: unsaved changes ──────────────────────────────────────── #
    "dlg_unsaved_title":    "Unsaved Changes",
    "dlg_unsaved_msg":      "You have unsaved changes. Save before continuing?",

    # ── Dialogs: about ────────────────────────────────────────────────── #
    "dlg_about_title":      "About VHDL Design Tool",
    "dlg_about_body":       (
        "<b>VHDL Design Tool</b><br>"
        "Combinational and Moore FSM digital design tool.<br>"
        "Generates VHDL-2008 from truth tables and ASM charts.<br><br>"
        "<b>Authors:</b><br>"
        "Oscar Yáñez Suárez<br>"
        "Omar Piña Ramírez<br>"
        "Universidad Autónoma Metropolitana, Unidad Iztapalapa<br>"
        "Erik René Bojorges Valdés<br>"
        "Universidad Iberoamericana, Campus CDMX<br><br>"
        "Project files use the <tt>.vhdlt</tt> format (JSON).<br>"
        "Licensed under the GNU General Public License v3.0."
    ),

    # ── Dialogs: add transition ───────────────────────────────────────── #
    "dlg_add_transition":       "Add Transition",
    "dlg_transition_type":      "Choose transition type:",
    "dlg_uncond":               "Unconditional → (go directly to next state)",
    "dlg_single_input":         "Single input condition (Diamond)",
    "dlg_multi_input":          "Multiple input condition (Hexagon)",

    # ── Dialogs: condition ────────────────────────────────────────────── #
    "dlg_edit_condition":       "Edit Decision Condition",
    "dlg_test_signal":          "Test signal / condition:",
    "dlg_if_true":              "If TRUE  (Y →):",
    "dlg_if_false":             "If FALSE (N →):",
    "dlg_edit_hex_condition":   "Edit Multi-Decision Condition",
    "dlg_condition_vars":       "Condition variables:",
    "dlg_exit_targets":         "Exit targets",

    # ── Dialogs: unconditional ────────────────────────────────────────── #
    "dlg_uncond_title":         "Unconditional Transition",
    "dlg_uncond_always":        "This state always transitions to:",
    "dlg_next_state":           "Next state:",

    # ── Dialogs: outputs ──────────────────────────────────────────────── #
    "dlg_outputs_title":        "Outputs for state:",
    "dlg_outputs_hint":         (
        "Tick scalars to assert them ('1') in this state.\n"
        "Enter bit patterns for bus signals (e.g. 101).\n"
        "Unticked / empty = default '0'."
    ),
    "dlg_no_outputs":           (
        "No output signals defined.\n"
        "Add output signals in the Signals panel first."
    ),

    # ── Dialogs: hexagon config ───────────────────────────────────────── #
    "dlg_hex_config":           "Configure Decision Hexagon",
    "dlg_hex_vars":             "Input variables:",
    "dlg_hex_mode":             "Exit mode:",
    "dlg_hex_minterms":         "One exit per minterm (2^n exits)",
    "dlg_hex_custom":           "User-defined exits with labels",
    "dlg_hex_custom_labels":    "Custom exit labels:",

    # ── State block canvas text ───────────────────────────────────────── #
    "state_click_outputs":      "click to set outputs",
    "state_add_condition":      "＋ condition",
    "state_edit_condition":     "⚙ condition",
    "state_set_initial":        "☆ Set as Initial State",
    "state_unset_initial":      "★ Initial state (click to unmark)",
    "state_edit_cond_menu":     "✏ Edit condition",
    "state_remove_cond_menu":   "🗑 Remove condition",

    # ── Condition block canvas text ───────────────────────────────────── #
    "cond_click_to_edit":       "click owner\nto edit",

    # ── Status bar ────────────────────────────────────────────────────── #
    "status_ready":             "Ready.",
    "status_saved":             "Saved: {}",
    "status_opened":            "Opened: {}",
    "status_new":               "New project.",
    "status_undo_na":           "Undo — not yet implemented.",
    "status_redo_na":           "Redo — not yet implemented.",
    "status_vhdl_copied":       "VHDL copied to clipboard.",
    "status_vhdl_saved":        "VHDL saved: {}",
    "status_validated_ok":      "Validation passed.",
    "status_validated_warn":    "{} warning(s).",
    "status_validated_err":     "{} error(s).",

    # ── Section labels ───────────────────────────────────────────────── #
    "lbl_truth_table":          "Truth Table",
    "lbl_vhdl_preview":         "VHDL Preview",
    "lbl_show_connections":     "Show connections",
    "lbl_tool_prefix":          "Tool:",

    # ── Hints / tips ─────────────────────────────────────────────────── #
    "hint_signal_mgr":          (
        "Tip: set Width > 1 for a bus signal, or select multiple "
        "inputs and click ⊞ Group → Bus to merge them."
    ),
    "hint_multiselect":         "Tip: hold Ctrl or Shift and click rows to multi-select.",
    "hint_bus_pattern":         "{}-bit pattern e.g. {}",
    "hint_vars_placeholder":    "e.g. a, b",
    "hint_custom_labels":       "e.g.  0X, 1X, X0, X1  (comma-separated)",
    "hint_entity_comb":         "my_combinational",
    "hint_entity_seq":          "my_fsm",
    "hint_arch":                "rtl",
    "menu_theme":           "Theme",
    "menu_theme_light":     "Light",
    "menu_theme_dark":      "Dark",
    # ── Simulation ───────────────────────────────────────────────────── #
    "sim_start":            "Simulate",
    "sim_stop":             "Stop Simulation",
    "sim_reset":            "Reset",
    "sim_step":             "Step",
    "sim_run":              "Run",
    "sim_pause":            "Pause",
    "sim_speed":            "Speed:",
    "sim_state":            "State",
    "sim_cycle":            "Cycle",
    "sim_inputs":           "Inputs",
    "sim_col_cycle":        "Cycle",
    "sim_col_state":        "State",
    "sim_col_inputs":       "Inputs",
    "sim_col_outputs":      "Outputs",
    "sim_error_title":      "Cannot Start Simulation",
    "sim_error_body":       "Fix the following errors in the ASM chart first:",
    "sim_timing": "Export Timing Diagram",
}

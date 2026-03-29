"""i18n/es.py — Spanish strings"""

STRINGS = {
    # ── Window / app ──────────────────────────────────────────────────── #
    "app_title":            "Herramienta de Diseño VHDL",
    "untitled":             "Sin título",

    # ── Menu: File ────────────────────────────────────────────────────── #
    "menu_file":            "&Archivo",
    "menu_new":             "&Nuevo proyecto",
    "menu_open":            "&Abrir proyecto…",
    "menu_save":            "&Guardar proyecto",
    "menu_save_as":         "Guardar proyecto &como…",
    "menu_quit":            "&Salir",

    # ── Menu: Edit ────────────────────────────────────────────────────── #
    "menu_edit":            "&Editar",
    "menu_undo":            "&Deshacer",
    "menu_redo":            "&Rehacer",

    # ── Menu: Settings ────────────────────────────────────────────────── #
    "menu_settings":        "&Configuración",
    "menu_language":        "&Idioma",

    # ── Menu: Help ────────────────────────────────────────────────────── #
    "menu_help":            "A&yuda",
    "menu_about":           "&Acerca de…",

    # ── Tabs ──────────────────────────────────────────────────────────── #
    "tab_combinational":    "Diseño Combinacional",
    "tab_sequential":       "Diseño Secuencial (Moore ASM)",

    # ── Signal manager ────────────────────────────────────────────────── #
    "sig_title":            "Señales",
    "sig_col_name":         "Nombre",
    "sig_col_direction":    "Dirección",
    "sig_col_width":        "Ancho",
    "sig_add":              "+ Agregar",
    "sig_remove":           "− Eliminar",
    "sig_input":            "Entrada",
    "sig_output":           "Salida",

    # ── Truth table toolbar ───────────────────────────────────────────── #
    "tt_group":             "Agrupar",
    "tt_ungroup":           "Desagrupar",
    "tt_dc_label":          "No importa:",
    "tt_dc_dash":           "— (guión)",
    "tt_dc_one":            "1",
    "tt_dc_zero":           "0",
    "tt_entity":            "Entidad:",
    "tt_arch":              "Arquitectura:",

    # ── ASM toolbar ───────────────────────────────────────────────────── #
    "asm_tool_select":      "Seleccionar / Mover",
    "asm_tool_state":       "Colocar Estado",
    "asm_tool_delete":      "Eliminar seleccionado\n(o presione Supr)",

    # ── VHDL preview ──────────────────────────────────────────────────── #
    "vhdl_generate":        "Generar VHDL",
    "vhdl_copy":            "Copiar",
    "vhdl_save":            "Guardar VHDL…",
    "vhdl_validate":        "Validar",

    # ── Dialogs: general ──────────────────────────────────────────────── #
    "dlg_ok":               "Aceptar",
    "dlg_cancel":           "Cancelar",
    "dlg_save":             "Guardar",
    "dlg_discard":          "Descartar",

    # ── Dialogs: unsaved changes ──────────────────────────────────────── #
    "dlg_unsaved_title":    "Cambios sin guardar",
    "dlg_unsaved_msg":      "Tiene cambios sin guardar. ¿Guardar antes de continuar?",

    # ── Dialogs: about ────────────────────────────────────────────────── #
    "dlg_about_title":      "Acerca de la Herramienta de Diseño VHDL",
    "dlg_about_body":       (
        "<b>Herramienta de Diseño VHDL</b><br>"
        "Herramienta de diseño digital combinacional y FSM de Moore.<br>"
        "Genera VHDL-2008 desde tablas de verdad y diagramas ASM.<br><br>"
        "Los archivos de proyecto usan el formato <tt>.vhdlt</tt> (JSON)."
    ),

    # ── Dialogs: add transition ───────────────────────────────────────── #
    "dlg_add_transition":       "Agregar transición",
    "dlg_transition_type":      "Seleccione el tipo de transición:",
    "dlg_uncond":               "Incondicional → (ir directamente al siguiente estado)",
    "dlg_single_input":         "Condición de una entrada (Diamante)",
    "dlg_multi_input":          "Condición de múltiples entradas (Hexágono)",

    # ── Dialogs: condition ────────────────────────────────────────────── #
    "dlg_edit_condition":       "Editar condición de decisión",
    "dlg_test_signal":          "Señal / condición a probar:",
    "dlg_if_true":              "Si VERDADERO  (Y →):",
    "dlg_if_false":             "Si FALSO (N →):",
    "dlg_edit_hex_condition":   "Editar condición multi-decisión",
    "dlg_condition_vars":       "Variables de condición:",
    "dlg_exit_targets":         "Destinos de salida",

    # ── Dialogs: unconditional ────────────────────────────────────────── #
    "dlg_uncond_title":         "Transición incondicional",
    "dlg_uncond_always":        "Este estado siempre transiciona a:",
    "dlg_next_state":           "Siguiente estado:",

    # ── Dialogs: outputs ──────────────────────────────────────────────── #
    "dlg_outputs_title":        "Salidas del estado:",
    "dlg_outputs_hint":         (
        "Marque escalares para activarlos ('1') en este estado.\n"
        "Ingrese patrones de bits para buses (ej. 101).\n"
        "Sin marcar / vacío = '0' por defecto."
    ),
    "dlg_no_outputs":           (
        "No hay señales de salida definidas.\n"
        "Agregue señales de salida en el panel de Señales primero."
    ),

    # ── Dialogs: hexagon config ───────────────────────────────────────── #
    "dlg_hex_config":           "Configurar hexágono de decisión",
    "dlg_hex_vars":             "Variables de entrada:",
    "dlg_hex_mode":             "Modo de salidas:",
    "dlg_hex_minterms":         "Una salida por mintérmino (2^n salidas)",
    "dlg_hex_custom":           "Salidas definidas por el usuario con etiquetas",
    "dlg_hex_custom_labels":    "Etiquetas de salida personalizadas:",

    # ── State block canvas text ───────────────────────────────────────── #
    "state_click_outputs":      "clic para definir salidas",
    "state_add_condition":      "＋ condición",
    "state_edit_condition":     "⚙ condición",
    "state_set_initial":        "☆ Marcar como estado inicial",
    "state_unset_initial":      "★ Estado inicial (clic para desmarcar)",
    "state_edit_cond_menu":     "✏ Editar condición",
    "state_remove_cond_menu":   "🗑 Eliminar condición",

    # ── Condition block canvas text ───────────────────────────────────── #
    "cond_click_to_edit":       "clic al estado\npropietario",

    # ── Status bar ────────────────────────────────────────────────────── #
    "status_ready":             "Listo.",
    "status_saved":             "Guardado: {}",
    "status_opened":            "Abierto: {}",
    "status_new":               "Nuevo proyecto.",
    "status_undo_na":           "Deshacer — aún no implementado.",
    "status_redo_na":           "Rehacer — aún no implementado.",
    "status_vhdl_copied":       "VHDL copiado al portapapeles.",
    "status_vhdl_saved":        "VHDL guardado: {}",
    "status_validated_ok":      "Validación exitosa.",
    "status_validated_warn":    "{} advertencia(s).",
    "status_validated_err":     "{} error(es).",

    # ── Section labels ───────────────────────────────────────────────── #
    "lbl_truth_table":          "Tabla de verdad",
    "lbl_vhdl_preview":         "Vista VHDL",
    "lbl_show_connections":     "Mostrar conexiones",
    "lbl_tool_prefix":          "Herramienta:",

    # ── Hints / tips ─────────────────────────────────────────────────── #
    "hint_signal_mgr":          (
        "Tip: establezca Ancho > 1 para un bus, o seleccione múltiples "
        "entradas y haga clic en ⊞ Agrupar → Bus para combinarlas."
    ),
    "hint_multiselect":         "Tip: mantenga Ctrl o Shift y haga clic en filas para selección múltiple.",
    "hint_bus_pattern":         "patrón de {} bits ej. {}",
    "hint_vars_placeholder":    "ej. a, b",
    "hint_custom_labels":       "ej.  0X, 1X, X0, X1  (separados por coma)",
    "hint_entity_comb":         "mi_combinacional",
    "hint_entity_seq":          "mi_fsm",
    "hint_arch":                "rtl",
    "menu_theme":           "Tema",
    "menu_theme_light":     "Claro",
    "menu_theme_dark":      "Oscuro",
    # ── Simulation ───────────────────────────────────────────────────── #
    "sim_start":            "Simular",
    "sim_stop":             "Detener simulación",
    "sim_reset":            "Reiniciar",
    "sim_step":             "Paso",
    "sim_run":              "Ejecutar",
    "sim_pause":            "Pausar",
    "sim_speed":            "Velocidad:",
    "sim_state":            "Estado",
    "sim_cycle":            "Ciclo",
    "sim_inputs":           "Entradas",
    "sim_col_cycle":        "Ciclo",
    "sim_col_state":        "Estado",
    "sim_col_inputs":       "Entradas",
    "sim_col_outputs":      "Salidas",
    "sim_error_title":      "No se puede iniciar la simulación",
    "sim_error_body":       "Corrija los siguientes errores en el diagrama ASM primero:",
    "sim_timing": "Exportar diagrama de tiempo",
}

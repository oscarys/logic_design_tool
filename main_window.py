"""
main_window.py
MainWindow — project save/load, dirty tracking, i18n, window title.
"""

import os
from PyQt6.QtWidgets import QMainWindow, QMessageBox, QFileDialog
from PyQt6.QtGui import QActionGroup
from PyQt6 import uic

from widgets.combinational_widget import CombinationalWidget   # noqa: F401
from widgets.sequential_widget    import SequentialWidget      # noqa: F401
from project.dirty_tracker   import DirtyTracker
from project.project_manager import (save_project, load_project,
                                     FILE_EXT, FILE_FILTER)
from i18n import (tr, set_language, current_language, language_changed,
                  set_theme, current_theme, theme_changed, theme_qss)

UI_PATH = os.path.join(os.path.dirname(__file__), "ui", "main_window.ui")


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        uic.loadUi(UI_PATH, self)

        self._tracker = DirtyTracker(self)
        self._tracker.dirty_changed.connect(self._update_title)

        # Language actions are mutually exclusive
        self._lang_group = QActionGroup(self)
        self._lang_group.setExclusive(True)
        self._lang_group.addAction(self.actionLangEnglish)
        self._lang_group.addAction(self.actionLangSpanish)

        self._theme_group = QActionGroup(self)
        self._theme_group.setExclusive(True)
        self._theme_group.addAction(self.actionThemeLight)
        self._theme_group.addAction(self.actionThemeDark)

        self._connect_actions()
        self._connect_dirty_signals()
        language_changed.connect(self._on_language_changed)
        theme_changed.connect(self._on_theme_changed)

        self.retranslate_ui()
        self._update_lang_checkmarks()
        self._apply_theme()
        self._update_theme_checkmarks()
        self._tracker.mark_clean(None)

    # ------------------------------------------------------------------ #
    # Menu wiring
    # ------------------------------------------------------------------ #
    def _connect_actions(self):
        self.actionNewProject.triggered.connect(self._on_new)
        self.actionOpenProject.triggered.connect(self._on_open)
        self.actionSaveProject.triggered.connect(self._on_save)
        self.actionSaveAs.triggered.connect(self._on_save_as)
        self.actionQuit.triggered.connect(self.close)
        self.actionUndo.triggered.connect(
            lambda: self.statusBar().showMessage(tr("status_undo_na")))
        self.actionRedo.triggered.connect(
            lambda: self.statusBar().showMessage(tr("status_redo_na")))
        self.actionAbout.triggered.connect(self._on_about)
        self.actionLangEnglish.triggered.connect(lambda: set_language("en"))
        self.actionLangSpanish.triggered.connect(lambda: set_language("es"))
        self.actionThemeLight.triggered.connect(lambda: set_theme("light"))
        self.actionThemeDark.triggered.connect(lambda: set_theme("dark"))

    def _connect_dirty_signals(self):
        t  = self._tracker
        cw = self.combinationalWidget
        sw = self.sequentialWidget

        cw._signal_model.changed.connect(t.mark_dirty)
        sw._signal_model.changed.connect(t.mark_dirty)
        cw._tt_model.dataChanged.connect(lambda *_: t.mark_dirty())
        cw._signal_model.changed.connect(self._reconnect_tt_dirty)
        sw.asmCanvasWidget._hub._dirty_tracker = t

        for le in (cw.lineEditEntityName, cw.lineEditArchName,
                   sw.lineEditEntityName, sw.lineEditArchName):
            le.textChanged.connect(lambda _: t.mark_dirty())
        cw.comboDontCare.currentIndexChanged.connect(
            lambda _: t.mark_dirty())

    def _reconnect_tt_dirty(self):
        self.combinationalWidget._tt_model.dataChanged.connect(
            lambda *_: self._tracker.mark_dirty())

    # ------------------------------------------------------------------ #
    # i18n
    # ------------------------------------------------------------------ #
    def _update_lang_checkmarks(self):
        lang = current_language()
        self.actionLangEnglish.setChecked(lang == "en")
        self.actionLangSpanish.setChecked(lang == "es")

    def _on_language_changed(self, lang: str):
        self._update_lang_checkmarks()
        self.retranslate_ui()

    def retranslate_ui(self):
        self._update_title(self._tracker.is_dirty())
        # Menus
        self.menuFile.setTitle(tr("menu_file"))
        self.menuEdit.setTitle(tr("menu_edit"))
        self.menuSettings.setTitle(tr("menu_settings"))
        self.menuLanguage.setTitle(tr("menu_language"))
        self.menuTheme.setTitle(tr("menu_theme"))
        self.actionThemeLight.setText(tr("menu_theme_light"))
        self.actionThemeDark.setText(tr("menu_theme_dark"))
        self.menuHelp.setTitle(tr("menu_help"))
        # Actions
        self.actionNewProject.setText(tr("menu_new"))
        self.actionOpenProject.setText(tr("menu_open"))
        self.actionSaveProject.setText(tr("menu_save"))
        self.actionSaveAs.setText(tr("menu_save_as"))
        self.actionQuit.setText(tr("menu_quit"))
        self.actionUndo.setText(tr("menu_undo"))
        self.actionRedo.setText(tr("menu_redo"))
        self.actionAbout.setText(tr("menu_about"))
        # Tab names
        self.tabWidget.setTabText(0, tr("tab_combinational"))
        self.tabWidget.setTabText(1, tr("tab_sequential"))
        # Status bar
        self.statusBar().showMessage(tr("status_ready"))
        # Child widgets — always retranslate together
        self.combinationalWidget.retranslate_ui()
        self.sequentialWidget.retranslate_ui()

    # ------------------------------------------------------------------ #
    # Theme
    # ------------------------------------------------------------------ #
    def _apply_theme(self):
        from PyQt6.QtWidgets import QApplication
        QApplication.instance().setStyleSheet(theme_qss())
        # Refresh canvas grid (redraws with new bg colour)
        sw = self.sequentialWidget
        sw.asmCanvasWidget._draw_grid()
        sw.asmCanvasWidget._scene.update()

    def _on_theme_changed(self, _name: str):
        self._apply_theme()
        self._update_theme_checkmarks()
        self.retranslate_ui()

    def _update_theme_checkmarks(self):
        t = current_theme()
        self.actionThemeLight.setChecked(t == "light")
        self.actionThemeDark.setChecked(t == "dark")

    # ------------------------------------------------------------------ #
    # Title bar
    # ------------------------------------------------------------------ #
    def _update_title(self, dirty: bool):
        path   = self._tracker.current_path()
        name   = os.path.basename(path) if path else tr("untitled")
        prefix = "* " if dirty else ""
        self.setWindowTitle(f"{prefix}{name} — {tr('app_title')}")

    # ------------------------------------------------------------------ #
    # Dirty-check guard
    # ------------------------------------------------------------------ #
    def _confirm_discard(self) -> bool:
        if not self._tracker.is_dirty():
            return True
        reply = QMessageBox.question(
            self, tr("dlg_unsaved_title"), tr("dlg_unsaved_msg"),
            QMessageBox.StandardButton.Save    |
            QMessageBox.StandardButton.Discard |
            QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Save)
        if reply == QMessageBox.StandardButton.Save:
            return self._on_save()
        if reply == QMessageBox.StandardButton.Discard:
            return True
        return False

    # ------------------------------------------------------------------ #
    # File actions
    # ------------------------------------------------------------------ #
    def _on_new(self):
        if not self._confirm_discard():
            return
        self.combinationalWidget._reset()
        self.sequentialWidget._reset()
        self._tracker.mark_clean(None)
        self.statusBar().showMessage(tr("status_new"))

    def _on_open(self):
        if not self._confirm_discard():
            return
        path, _ = QFileDialog.getOpenFileName(
            self, tr("menu_open"), "", FILE_FILTER)
        if not path:
            return
        try:
            load_project(path,
                         self.combinationalWidget,
                         self.sequentialWidget)
            self.combinationalWidget._tt_model.dataChanged.connect(
                lambda *_: self._tracker.mark_dirty())
            self._tracker.mark_clean(path)
            self.statusBar().showMessage(tr("status_opened", path))
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def _on_save(self) -> bool:
        path = self._tracker.current_path()
        if not path:
            return self._on_save_as()
        self._do_save(path)
        return True

    def _on_save_as(self) -> bool:
        path, _ = QFileDialog.getSaveFileName(
            self, tr("menu_save_as"), "", FILE_FILTER)
        if not path:
            return False
        if not path.endswith(FILE_EXT):
            path += FILE_EXT
        self._do_save(path)
        return True

    def _do_save(self, path: str):
        try:
            save_project(path,
                         self.combinationalWidget,
                         self.sequentialWidget)
            self._tracker.mark_clean(path)
            self.statusBar().showMessage(tr("status_saved", path))
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def _on_about(self):
        QMessageBox.about(self, tr("dlg_about_title"), tr("dlg_about_body"))

    # ------------------------------------------------------------------ #
    # Close event
    # ------------------------------------------------------------------ #
    def closeEvent(self, event):
        if self._confirm_discard():
            event.accept()
        else:
            event.ignore()

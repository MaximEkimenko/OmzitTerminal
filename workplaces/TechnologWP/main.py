import os

import sys

from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QIcon, QAction
from PyQt6.QtWidgets import QApplication, QMainWindow, QStatusBar, QToolBar

from apps.process.widgets import ProcessWidget


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__(parent=None)
        self.setWindowTitle("Рабочее место технолога")
        self.setMinimumSize(1200, 600)
        self.setWindowIcon(QIcon("static/img/icon.svg"))

        self._create_actions()
        self._create_menu()
        self._create_toolbar()
        self._connect_actions()
        self._create_statusbar()
        self._open_main_window()

    def _create_menu(self):
        menu_bar = self.menuBar()

        file_menu = menu_bar.addMenu("&Файл")
        edit_menu = menu_bar.addMenu("&Правка")
        help_menu = menu_bar.addMenu("&Справка")

        file_menu.addAction(self.open_action)
        file_menu.addSeparator()
        file_menu.addAction(QIcon("static/img/close.svg"), "&Выход", self.close)

        edit_menu.addAction(self.undo_action)
        edit_menu.addAction(self.redo_action)

        help_menu.addAction("&О программе")

    def _create_toolbar(self):
        tools = QToolBar("Навигация")
        tools.setIconSize(QSize(35, 35))
        tools.addAction(self.open_main_window_action)
        tools.addAction(self.open_plasma_window_action)
        tools.addSeparator()
        tools.addAction(self.close_app_action)
        self.addToolBar(Qt.ToolBarArea.LeftToolBarArea, tools)

    def _create_statusbar(self):
        status = QStatusBar()
        self.setStatusBar(status)

    def _create_actions(self):
        self.open_main_window_action = QAction(QIcon("static/img/process.svg"), "Технологический процесс", self)
        self.open_plasma_window_action = QAction(QIcon("static/img/plasma.png"), "Плазма", self)
        self.close_app_action = QAction(QIcon("static/img/exit.svg"), "Выход", self)
        self.open_action = QAction(QIcon("static/img/open.svg"), "&Открыть", self)
        self.undo_action = QAction(QIcon("static/img/undo.svg"), "&Отменить", self)
        self.redo_action = QAction(QIcon("static/img/redo.svg"), "&Повторить", self)

    def _remove_previous_widget_toolbar(self):
        if hasattr(self, 'widget_tools'):
            self.removeToolBar(self.widget_tools)

    def _open_main_window(self):
        if hasattr(self, 'central_widget') and isinstance(self.central_widget, ProcessWidget):
            return
        self._remove_previous_widget_toolbar()
        self.central_widget = ProcessWidget(self)
        self.setCentralWidget(self.central_widget)

    def _connect_actions(self):
        self.open_main_window_action.triggered.connect(self._open_main_window)
        self.close_app_action.triggered.connect(self.close)


def create_folders():
    if not os.path.exists('data'):
        os.mkdir('data')
    if not os.path.exists('data/temp'):
        os.mkdir('data/temp')
    if not os.path.exists('data/process'):
        os.mkdir('data/process')


def set_style(application, style_name):
    with open(f'static/css/{style_name}.css', 'r') as style_file:
        theme = style_file.read()
    application.setStyleSheet(theme)


if __name__ == "__main__":
    app = QApplication([])
    create_folders()
    set_style(application=app, style_name='light')
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

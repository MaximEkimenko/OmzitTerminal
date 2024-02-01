import logging
import os

import pandas as pd
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import (
    QGridLayout, QTableView, QFileDialog, QDialog, QPushButton, QLineEdit, QCheckBox, QLabel, QComboBox,
)

from apps.process.models import PandasModel
from apps.process.settings import COLUMNS
from apps.process.utils.parse_operations import get_all_operations


class OperationChoiceWindow(QDialog):
    def __init__(self, parent=None):
        super(OperationChoiceWindow, self).__init__(parent)
        self.setWindowTitle('Выбор операции')
        layout = QGridLayout()
        layout.setSpacing(10)
        self.operations = []
        self.data = None

        self.table_operations = QTableView()
        self.table_operations.setGeometry(0, 0, 800, 600)

        if os.path.exists('data/temp/operations.xlsx'):
            data = pd.read_excel(r'operations.xlsx', index_col=0)
        else:
            data = pd.DataFrame(columns=COLUMNS[:15])
        model = PandasModel(data, 0)

        self.table_operations.setModel(model)

        self.setMinimumWidth(self.table_operations.width() * 2)
        self.setMinimumHeight(self.table_operations.height())

        self.searchbar = QLineEdit()
        self.searchbar.textChanged.connect(self.search)

        from_file_button = QPushButton(text="Загрузить операции из файла", parent=self)
        from_file_button.clicked.connect(self.open_from_file)

        self.setLayout(layout)

        ok_button = QPushButton(text="OK", parent=self)
        ok_button.clicked.connect(self.on_confirm_operation_select)

        layout.addWidget(self.searchbar, 0, 0, 1, 2)
        layout.addWidget(from_file_button, 0, 2, 1, 1)
        layout.addWidget(self.table_operations, 1, 0, 1, 20)
        layout.addWidget(ok_button, 2, 0, 1, 2)

    def set_table_data(self, table, data):
        try:
            model = PandasModel(data, 0)
            table.setModel(model)
        except Exception as ex:
            logging.exception(ex)

    def open_from_file(self):
        xlsx_file_names = QFileDialog.getOpenFileNames(
            self,
            caption="Выберите файл",
            directory=r"D:\\",
            filter="Excel Files (*.xlsx);;",
        )[0]
        if xlsx_file_names:
            get_all_operations(xlsx_file_names)
            data = pd.read_excel(r'operations.xlsx', index_col=0)
            self.set_table_data(self.table_operations, data)

    def search(self):
        try:
            if self.data is None:
                self.data = self.table_operations.model().df
            data = self.data
            data = data[
                data.apply(
                    lambda x: x.astype(str).str.contains(self.searchbar.text(), case=False, regex=False)).any(
                    axis=1)]
            self.set_table_data(self.table_operations, data)
        except Exception as ex:
            logging.exception(ex)

    def on_confirm_operation_select(self):
        indexes = set(map(lambda x: x.row(), self.table_operations.selectedIndexes()))
        data = self.table_operations.model().df
        for index in indexes:
            self.operations.append(data.iloc[index])
        self.close()


class SelectColumnsWindow(QDialog):
    def __init__(self, parent=None):
        super(SelectColumnsWindow, self).__init__(parent)
        self.setWindowTitle('Выбор отображаемых столбцов')
        layout = QGridLayout()
        layout.setSpacing(5)
        self.selected_columns = parent.displayed_columns

        self.setLayout(layout)

        self.checkboxes = []
        for column in COLUMNS:
            checkbox = QCheckBox(column)
            checkbox.setChecked(column in self.selected_columns)
            self.checkboxes.append(checkbox)

        ok_button = QPushButton(text="OK", parent=self)
        ok_button.clicked.connect(self.on_confirm_columns_select)

        select_all_button = QPushButton(text="", parent=self)
        select_all_button.setIcon(QIcon("static/img/select-all.svg"))
        select_all_button.clicked.connect(self.select_all)

        select_none_button = QPushButton(text="", parent=self)
        select_none_button.setIcon(QIcon("static/img/select-none.svg"))
        select_none_button.clicked.connect(self.select_none)

        layout.addWidget(select_all_button, 0, 0, 1, 1, Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(select_none_button, 0, 1, 1, 1, Qt.AlignmentFlag.AlignLeft)

        last = 0

        for i, checkbox in enumerate(self.checkboxes):
            layout.addWidget(checkbox, 1 + i, 0, 1, 11)
            last = 1 + i

        layout.addWidget(ok_button, last + 1, 2, 1, 6)

    def on_confirm_columns_select(self):
        self.selected_columns = [checkbox.text() for checkbox in self.checkboxes if checkbox.isChecked()]
        self.close()

    def select_all(self):
        for checkbox in self.checkboxes:
            checkbox.setChecked(True)

    def select_none(self):
        for checkbox in self.checkboxes:
            checkbox.setChecked(False)


class SelectNextPrevOperationWindow(OperationChoiceWindow):
    def __init__(self, parent=None, data=None, current_ids=None):
        super(OperationChoiceWindow, self).__init__(parent)
        self.setWindowTitle('Выбор операции')
        layout = QGridLayout()
        layout.setSpacing(10)
        self.operations_ids = current_ids
        self.data = data

        self.table_operations = QTableView()
        self.table_operations.setGeometry(0, 0, 800, 600)

        model = PandasModel(data, 0)

        self.table_operations.setModel(model)

        self.setMinimumWidth(self.table_operations.width() * 2)
        self.setMinimumHeight(self.table_operations.height())

        self.searchbar = QLineEdit()
        self.searchbar.textChanged.connect(self.search)

        self.setLayout(layout)

        ok_button = QPushButton(text="OK", parent=self)
        ok_button.clicked.connect(self.on_confirm_operation_select)

        layout.addWidget(self.searchbar, 0, 0, 1, 2)
        layout.addWidget(self.table_operations, 1, 0, 1, 20)
        layout.addWidget(ok_button, 2, 0, 1, 2)

    def on_confirm_operation_select(self):
        indexes = set(map(lambda x: x.row(), self.table_operations.selectedIndexes()))
        data = self.table_operations.model().df
        self.operations_ids = []
        for index in indexes:
            self.operations_ids.append(data.iloc[index, 20])
        self.close()


class SelectXlsxSheetWindow(QDialog):

    def __init__(self, parent=None, sheets=None):
        super(SelectXlsxSheetWindow, self).__init__(parent)
        self.sheets = sheets
        self.selected_sheet = ''
        layout = QGridLayout()
        layout.setSpacing(10)

        self.setLayout(layout)

        ok_button = QPushButton(text="OK", parent=self)
        ok_button.clicked.connect(self.on_confirm_sheet_select)

        label = QLabel()
        label.setText('Выберите модель:')
        self.sheet_select = QComboBox()
        self.sheet_select.addItem("Не выбрано")
        self.sheet_select.addItems(self.sheets)
        self.sheet_select.setMinimumWidth(200)

        layout.addWidget(label, 0, 0, 1, 1, Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(self.sheet_select, 0, 1, 1, 1, Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(ok_button, 1, 0, 1, 2, Qt.AlignmentFlag.AlignHCenter)

    def on_confirm_sheet_select(self):
        index = self.sheet_select.currentIndex()
        if index > 0:
            self.selected_sheet = self.sheet_select.itemText(index)
        else:
            self.selected_sheet = ''
        self.close()

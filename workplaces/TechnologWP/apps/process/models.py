import logging

from PyQt6.QtCore import Qt, QAbstractTableModel
from PyQt6.QtGui import QColor


class PandasModel(QAbstractTableModel):
    def __init__(self, data, last_id, planned=False, immutables=()):
        super().__init__()
        self.df = data
        self.last_id = last_id
        self.planned = planned
        self.colors = dict()
        self.immutables = immutables

    def rowCount(self, index):
        return self.df.shape[0]

    def columnCount(self, parent=None):
        return self.df.shape[1]

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        try:
            if index.isValid():
                if role == Qt.ItemDataRole.BackgroundRole:
                    color = self.colors.get((index.row(), index.column()))
                    if color is not None:
                        return color
                if role == Qt.ItemDataRole.DisplayRole or role == Qt.ItemDataRole.EditRole:
                    value = self.df.iloc[index.row(), index.column()]
                    if str(value) == 'nan' or str(value) == 'None':
                        value = f''
                    elif isinstance(value, float):
                        value = f'{value:.2f}'
                    else:
                        value = f'{value}'
                    return value
        except Exception as ex:
            logging.exception(ex)

    def setData(self, index, value, role):
        try:
            def val(i):
                return float(self.df.iloc[index.row(), i])

            if role == Qt.ItemDataRole.EditRole:
                if index.column() not in [20, 21, 22] + list(range(6, 15)):
                    if value.strip() == '':
                        value = None
                    self.change_color(index.row(), index.column(), QColor("white"))
                    self.df.iloc[index.row(), index.column()] = value
                elif index.column() == 6:
                    if float(value) == 0:
                        logging.error('Деление на 0')
                        return False
                    self.df.iloc[index.row(), 6] = float(value)
                    self.df.iloc[index.row(), 9] = val(7) * val(8) / val(6)
                    self.df.iloc[index.row(), 11] = val(9) * val(10)
                    self.df.iloc[index.row(), 12] = val(11) * val(13)
                    self.df.iloc[index.row(), 14] = val(9) * val(10) / val(8)
                elif index.column() == 7:
                    self.df.iloc[index.row(), 7] = float(value)
                    self.df.iloc[index.row(), 6] = val(8) * val(7) / val(9)
                elif index.column() == 8:
                    if float(value) == 0:
                        logging.error('Деление на 0')
                        return False
                    self.df.iloc[index.row(), 8] = float(value)
                    self.df.iloc[index.row(), 6] = val(8) * val(7) / val(9)
                    self.df.iloc[index.row(), 14] = val(9) * val(10) / val(8)
                elif index.column() == 9:
                    if float(value) == 0:
                        logging.error('Деление на 0')
                        return False
                    self.df.iloc[index.row(), 9] = float(value)
                    self.df.iloc[index.row(), 6] = val(8) * val(7) / val(9)
                    self.df.iloc[index.row(), 11] = val(9) * val(10)
                    self.df.iloc[index.row(), 12] = val(11) * val(13)
                    self.df.iloc[index.row(), 14] = val(9) * val(10) / val(8)
                elif index.column() == 10:
                    self.df.iloc[index.row(), 10] = float(value)
                    self.df.iloc[index.row(), 11] = val(9) * val(10)
                    self.df.iloc[index.row(), 12] = val(11) * val(13)
                    self.df.iloc[index.row(), 14] = val(9) * val(10) / val(8)
                elif index.column() == 13:
                    self.df.iloc[index.row(), 13] = float(value)
                    self.df.iloc[index.row(), 12] = val(11) * val(13)
                    self.df.iloc[index.row(), 14] = val(9) * val(10) / val(8)
                return True
        except Exception as ex:
            logging.exception(ex)
        finally:
            return False

    def headerData(self, section, orientation, role):
        if role == Qt.ItemDataRole.DisplayRole:
            if orientation == Qt.Orientation.Horizontal:
                return str(self.df.columns[section])

            if orientation == Qt.Orientation.Vertical:
                return str(self.df.index[section] + 1)

    def flags(self, index):
        try:
            if self.df.shape[1] > 19 and self.df.iloc[index.row(), 20] in self.immutables and index.column() not in [19,
                                                                                                                     21,
                                                                                                                     22]:
                return Qt.ItemFlag.ItemIsSelectable
            elif self.planned and index.column() in [200] or index.column() in [11, 12, 14]:
                return Qt.ItemFlag.ItemIsSelectable
            else:
                return Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsEditable
        except Exception as ex:
            logging.exception(ex)

    def change_color(self, row, column, color):
        ix = self.index(row, column)
        self.colors[(row, column)] = color
        self.dataChanged.emit(ix, ix, (Qt.ItemDataRole.BackgroundRole,))

import os
import datetime
import time
from calendar import monthrange
from openpyxl.styles import Font, Alignment, Border, Side, PatternFill
"""
Модуль с разными вспомогательными функциями
'ver 23.08.2023'
"""


def fresh_file(path=os.getcwd() + '\\', keyword='', ext=''):
    """
    Функция возвращает имя файла модифицированного последним в директории path в имени которого есть,
    ключевое слово keyword
    return: latest_file - - полная директория файла с именем
    """
    max_time = 0  # переменная максимального времени корректировки файла
    latest_file = ''  #
    for root, dirs, files in os.walk(path):
        for file in files:
            if keyword in file and '~' not in file and ext in file:
                current_file = os.path.join(root, file)
                file_change_time = os.path.getmtime(current_file)
                if file_change_time > max_time:
                    max_time = file_change_time
                    latest_file = current_file
    return latest_file


def d_m_y_today():
    """
    Функция возвращает сегодняшний день, месяц, год. День и месяц в формате '01-31', '01-12'

    """
    return (datetime.datetime.now().strftime('%d'), datetime.datetime.now().strftime('%m'),
            datetime.datetime.now().year)


def last_month_day(month, year, weekday=False):
    """
    Возвращает количество дней в месяце.
    Если передан параметр weekday = True,
    то возвращается кортеж = день недели первого дня месяца (номер от 0 до 6), последний день месяца
    """
    if weekday:
        return monthrange(int(year), int(month))
    else:
        return monthrange(int(year), int(month))[1]


def restart_decor(**dkwargs):  # параметры декоратора
    """
    Функция для использования в качестве декоратора для перезапуска декорируемой функции attempts раз через
    time_after_attempt секунд
    """

    def outer(func):  # декорируемая функция
        def inner(*args, **kwargs):  # *args, **kwargs вход параметры функции
            attempts = dkwargs['attempts']
            time_after_attempt = dkwargs['time_after_attempt']
            total_attempts = attempts
            while attempts > 0:
                try:
                    return func(*args, **kwargs)
                except Exception as err:
                    print(f"Ошибка {err} на попытке {total_attempts - (attempts - 1)}. Время попытки: "
                          f"{datetime.datetime.now().time().strftime('%H:%M:%S')}. Попыток осталось {attempts - 1}.")
                    attempts -= 1
                    time.sleep(time_after_attempt)
        return inner
    return outer


def find_file(search_dir, filename):
    """"
    Функция находить файл filename в директории search_dir включая вложенные папки
    возвращает
    """
    for root, dirs, files in os.walk(search_dir):
        for file in files:
            if file in filename:
                return fr'{root}\{file}'


def create_list(dir_path: str, result_type: str, extension: str = '') -> list:
    """
    Функция возвращает список файлов с расширением extension при result_type=files и папок в директории dir_path
    при result_type=dirs не включая вложенные папки
    при result_type=all_files в список добавляются все файлы включая под паки dir_path
    """
    file_list = []
    dirs_list = []
    for root, path_dirs, path_files in os.walk(dir_path):
        if result_type == 'all_files':
            for file in path_files:
                if extension in file and '~' not in file:
                    file_list.append(fr'{root}\{file}')
            return file_list
        if result_type == 'files':
            for file in path_files:
                if extension in file and '~' not in file:
                    if dir_path == root:
                        file_list.append(fr'{root}\{file}')
            return file_list
        if result_type == 'dirs':
            for path_dir in path_dirs:
                if dir_path == root:
                    dirs_list.append(fr'{root}\{path_dir}')
            return dirs_list


def cell_width(sh_obj, letters_list: tuple):
    """"
    Функция форматирует ширину колонок по кортежу ('Литера колонки', 'Ширина колонки')
    """
    for letter, value in letters_list:
        sh_obj.column_dimensions[letter].width = value


def cell_formating(cell_obj, sheet_obj=None, col_num=None, borders=None, border_color='000000', row_height=None,
                   fill_color=None, font_size=None, font_name=None, font_bold=None, font_color='000000',
                   hor_align=None, vert_align=None, wrap_text=None, number_format=None):
    """
    Программа форматирует выбранную ячейку
    cell_obj передается в виде  cell_obj = sheet_obj [f'A{str(i)}'] - ячейка
    sheet_obj объект листа openpyxl
    feel_color = "FF6505"
    col_num - int номера колонки
    return: None
    """
    if borders:
        borders_thin = Side(border_style="thin", color=border_color)  # стиль границы
        cell_obj.border = Border(top=borders_thin, bottom=borders_thin, left=borders_thin, right=borders_thin)
    if row_height and col_num:
        sheet_obj.row_dimensions[col_num].height = row_height
    if fill_color:
        cell_obj.fill = PatternFill('solid', fgColor=fill_color)
    if font_size and font_name:
        cell_obj.font = Font(size=font_size, name=font_name, bold=font_bold, color=font_color)
    if hor_align and vert_align:
        cell_obj.alignment = Alignment(horizontal=hor_align, vertical=vert_align, wrapText=wrap_text)
    if number_format:
        cell_obj.number_format = number_format


if __name__ == '__main__':
    find_file(search_dir=r'O:\Расчет эффективности\Рапорты', filename='report_16.05.23.pdf')

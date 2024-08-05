import datetime
import openpyxl
from omzit_terminal.settings import BASE_DIR  # noqa
from m_logger_settings import logger  # noqa
from openpyxl.utils.cell import get_column_interval


def db_fields_to_excel(db_verbose_names: tuple, report_name: str, DBmodel) -> str:
    """
    Функция формирует файл excel с колонками verbose_name из модели DBmodel
    и возвращает путь к файлу отчёт
    :param DBmodel:
    :param report_name:
    :param db_verbose_names:
    :return:
    """
    # Имя нового файла
    report_filename = f"{datetime.datetime.now().strftime('%Y-%m-%d')} {report_name}.xlsx"
    # Формируем путь к новому файлу
    exel_file_path = BASE_DIR / "xlsx" / report_filename
    # список колонок для шапки
    verbose_names = dict()
    for field in DBmodel._meta.get_fields():
        if field.verbose_name in db_verbose_names:
            if hasattr(field, "verbose_name"):
                verbose_names[field.name] = field.verbose_name
            else:
                verbose_names[field.name] = field.name
    # сортировка по db_verbose_names
    reverse_values_dict = {value: key for key, value in verbose_names.items()}
    verbose_names = {reverse_values_dict[value]: value for value in db_verbose_names}
    # данные
    data = DBmodel.objects.all().values(*verbose_names.keys())
    # файл excel
    excel_workbook = openpyxl.Workbook()
    excel_sheet = excel_workbook.active
    # шапка
    headers = list(verbose_names.values())
    headers.insert(0, '№')  # TODO найти другое решение добавления номера строки
    excel_sheet.append(headers)
    # запись данных
    for index, row in enumerate(data):
        row_data = list(row.values())
        # форматирование даты
        for element_index, element in enumerate(row_data):
            if isinstance(element, datetime.date):
                row_data[element_index] = element.strftime('%d.%m.%Y')
        row_data.insert(0, index + 1)  # TODO найти другое решение добавления номера строки
        excel_sheet.append(row_data)
    # форматирование TODO вынести во внешние параметры
    cols = get_column_interval(1, excel_sheet.max_column)  # литеры колонок листа
    skip_format_columns = ('A', 'B', 'H')
    for col in cols:
        if col not in skip_format_columns:
            excel_sheet.column_dimensions[col].width = 30
        else:
            excel_sheet.column_dimensions[col].width = 10
    # сохранение excel
    try:
        excel_workbook.save(exel_file_path)
        excel_workbook.close()
        return exel_file_path
    except Exception as e:
        logger.error(f'Ошибка сохранения файла Excel при запросу отчёта {exel_file_path}')
        logger.exception(e)

import datetime
import io
import os
import re
import shutil

import openpyxl
from transliterate import translit

from omzit_terminal.settings import BASE_DIR

STEELS = {
    "С235": "SP",
    "С245": "SP",
    "С255": "SP",
    "С275": "SP",
    "С285": "SP",
    "С345": "GS",
    "С345Д": "GS",
    "С345К": "SS",
    "С375": "",
    "С375Д": "",
    "С390": "",
    "С390Д": "",
    "С390К": "",
    "С440": "",
    "С440Д": "",
    "С590": "",
    "С590К": "",
    "Ст3кп2": "SP",
    "Ст3пс5": "SP",
    "Ст3сп5": "SP",
    "Ст3Гпс": "SP",
    "Ст3Гсп": "SP",
    "Ст3пс": "SP",
    "Ст3сп": "SP",
    "12Г2С": "GS",
    "09Г2С": "GS",
    "09Г2СД": "GS",
    "12Г2СД": "GS",
    "10ХНДП": "SS",
    "14Г2АФ": "",
    "14Г2АФД": "",
    "14Г2АФДпс": "",
    "16Г2АФ": "",
    "16Г2АФД": "",
    "12Г2СМФ": "",
    "12Г2СМФФАЮ": "",
}


def create_layout_xlsx(queryset):
    """
    Создает excel-файл по выбранным заготовкам для выполнения раскладки
    :param queryset: выбранные заготовки
    :return:
    """
    fields = (
        'id',  # Номер СЗ
        'model_order_query',  # Заказ-модель
        'fio_tehnolog',  # ФИО Технолога
        'plasma_layout',  # Раскладка
        'datetime_done',  # Дата потребности
        'ws_number',  # Цех плазмы
        'draw',  # Чертеж
        'name',  # Наименование
        'count',  # Количество
        'material',  # Материал
        'layout_name',  # Имя детали на раскладке
    )

    exel_file_src = BASE_DIR / "LayoutPlasmaTemplate.xlsx"
    new_file_name = f"{datetime.datetime.now().strftime('%Y.%m.%d %H-%M-%S')} layout.xlsx"
    # Создаем папку для хранения отчетов
    if not os.path.exists(BASE_DIR / "xlsx"):
        os.mkdir(BASE_DIR / "xlsx")
    # Формируем путь к новому файлу
    exel_file_dst = BASE_DIR / "xlsx" / new_file_name
    # Копируем шаблон в новый файл отчета
    shutil.copy(exel_file_src, exel_file_dst)

    ex_wb = openpyxl.load_workbook(exel_file_src, data_only=True)
    ex_sh = ex_wb["Раскладка"]
    # Данные
    for i, row in enumerate(queryset):
        row.update(row.pop('workpiece'))
        j = 0
        for field in row:
            if field in fields:
                cell = ex_sh.cell(row=i + 2, column=j + 1)
                cell.value = str(row[field])
                j += 1
    ex_wb.save(exel_file_dst)
    return exel_file_dst


def read_plasma_layout(layout_file):
    file = layout_file.read().decode('Windows-1251')
    reader = io.StringIO(file)
    parts_layouts = {}

    if layout_file.name.lower().endswith(".csv"):
        layout_duplicates = None  # количество листов с одинаковой раскладкой
        layout_name = None  # имя раскладки
        layout_date = ''  # дата раскладки
        for row in reader:

            if not layout_date:
                date_pattern = (r'[,]+(\d{1,2})\/(\d{1,2})\/(\d{4})\s(\d{1,2}):(\d{1,2}):(\d{1,2})[,]+')
                date_match = re.match(date_pattern, row)
                if date_match:
                    layout_date = '-'.join(date_match.group(1, 2, 3)) + ' ' + '.'.join(date_match.group(4, 5, 6))

            if not layout_name:
                layout_name_pattern = (r'.*Имя\sпрограммы\s:\s([^,]+)')
                layout_name_match = re.match(layout_name_pattern, row)
                if layout_name_match:
                    layout_name = ''.join(layout_name_match.group(1)) + ' ' * len(layout_date) + layout_date

            if not layout_duplicates:
                duplicates_match = re.match(r"^.*Кол-во листов с одинаковой раскладкой[,]+([\d])+.*", row)
                if duplicates_match:
                    layout_duplicates = int(duplicates_match.group(1))

            dxf = re.match(r"^.*[,]+(.*(SS |SP |GS )[^,]*)[\s,]+([\d]+).*(\d{2}:\d{2}:\d{2})", row)
            if dxf:
                if not layout_name:
                    layout_name = layout_file.name
                if not layout_duplicates:
                    layout_duplicates = 1
                part = dxf.group(1).strip()
                parts_layouts[part] = {
                    layout_name: [int(dxf.group(3)) * layout_duplicates],
                    'time': dxf.group(4)
                }

    elif layout_file.name.lower().endswith(".cnc"):
        for row in reader:
            dxf = re.match(r"^\"PART (.*)\s([\d]+)\s[\d]+\s[\d.]+\s[\d.]+", row)
            if dxf and "$REST_CUT" not in dxf.group(1):
                part = dxf.group(1).strip()
                parts_layouts[part] = parts_layouts.get(part, {layout_file.name: set()})
                parts_layouts[part][layout_file.name].add(dxf.group(2))
        for part, part_value in parts_layouts.items():
            for key, value in part_value.items():
                part_value[key] = [len(value)]

    elif layout_file.name.lower().endswith(".odt"):
        pass
    # Пример структуры parts_layouts {
    # "№order1 3SP B-30 Balka №30 3": {  наименование детали
    #             '12ГС-43.csv': [1],  раскладка: количество
    #             '10ГС-40.csv': [3, 3, 3, 3], количество листов с одинаковой раскладкой - 4 - исключили случай
    #             '10ГС-40.csv': [12], количество листов с одинаковой раскладкой - 4
    #       },
    # "№order1 3SP B-31 Balka №31 1": {
    #             '10ГС-С отхода 2280х480 к 21-1.csv': [15],
    #       }
    # }
    return parts_layouts


def read_plasma_layout_db(dxf):
    pass


def create_part_name(shift_task_values):
    workshop = shift_task_values['ws_number']
    name = shift_task_values['workpiece']['name']
    material = shift_task_values['workpiece']['material']
    count = shift_task_values['workpiece']['count']
    order_model = shift_task_values['model_order_query']

    order, model = order_model.split("_")

    # Толщина
    match = re.match(r"^.*?([\d]+).*", material)
    if match:
        thickness = match.group(1)
    else:
        thickness = ""

    # Наименование
    match = re.match(r"(^.+?)\s\d+х\d+.*", name)
    if match:
        name = match.group(1)

    # Сталь
    steel = ""
    for key, value in STEELS.items():
        if key in material:
            steel = value

    if workshop == '102':
        part_name = f"{thickness}{steel} №{order} {name.strip()} {count}"
    else:
        part_name = f"№{order} {thickness}{steel} {name.strip()} {count}"

    part_name = translit(part_name, language_code='ru', reversed=True)
    return part_name

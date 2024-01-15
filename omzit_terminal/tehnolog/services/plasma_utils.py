import datetime
import io
import operator
import os
import re
import shutil

from functools import reduce

import openpyxl
from django.db.models import Q, F, Subquery, Sum, Max, OuterRef
from transliterate import translit

from omzit_terminal.settings import BASE_DIR, DATABASES

from tehnolog.models import Pip, Program

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

THICKNESS_SPEED = {  # mm (толщина): mm/s (скорость)
    '0.5': 5355 / 60,
    '1.5': 2210 / 60,
    '1': 3615 / 60,
    '2': 9810 / 60,
    '3': 6145 / 60,
    '4': 5550 / 60,
    '5': 4297.5 / 60,
    '6': 3045 / 60,
    '8': 2862.5 / 60,
    '10': 2680 / 60,
    '12': 2200 / 60,
    '14': 1843.3 / 60,
    '16': 2938 / 60,
    '18': 2554 / 60,
    '20': 2170 / 60,
    '22': 1930 / 60,
    '24': 1766.7 / 60,
    '25': 1685 / 60,
    '30': 1290 / 60,
    '36': 975 / 60,
    '40': 790 / 60,
    '50': 405 / 60,
    '60': 258.3 / 60,
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
                hours, minutes, seconds = map(int, dxf.group(4).split(':'))
                norm_tech = hours + ((minutes + seconds / 60) / 60)
                parts_layouts[part] = {
                    layout_name: {
                        'count': [int(dxf.group(3)) * layout_duplicates],
                        'time': norm_tech,
                    },
                }

    elif layout_file.name.lower().endswith(".cnc"):
        parts_thickness = dict()
        parts_length = dict()
        for row in reader:
            dxf = re.match(r"^\"PART ((\d{1,2}|[^\s]+\s).*)\s([\d]+)\s([\d]+)\s[\d.]+\s[\d.]+", row)
            if dxf and "$REST_CUT" not in dxf.group(1):
                thickness = dxf.group(2)
                part, number, area = dxf.group(1, 3, 4)
                if thickness in THICKNESS_SPEED:
                    parts_thickness[part] = thickness
                else:
                    parts_thickness[part] = '1'
                part = part.strip()
                parts_length[part] = (int(area) ** 0.5) * 4

                parts_layouts[part] = parts_layouts.get(part, {layout_file.name: set()})
                parts_layouts[part][layout_file.name].add(number)

        for part, part_layouts in parts_layouts.items():
            for layout, numbers in part_layouts.items():
                part_layouts[layout] = {
                    'count': [len(numbers)],
                    'time': (parts_length[part] / THICKNESS_SPEED[parts_thickness[part]]) / 3600
                }
    elif layout_file.name.lower().endswith(".odt"):
        pass
    # Пример структуры parts_layouts {
    # "№order1 3SP B-30 Balka №30 3": {  наименование детали
    #             '12ГС-43.csv': {
    #                   'count': [3],
    #                   'time': 2.67631 в часах
    #             }
    #       },
    return parts_layouts


def read_plasma_layout_db(dxf):
    condition = reduce(
        operator.or_,
        (Q(wo_number=order, part_name=part) for order, part in dxf)
    )

    total_cutting_length = Pip.objects.using('sigma').values('program_name').annotate(
        total_cutting_length=Sum(F('cutting_length') * F('qty_in_process'))
    ).values('total_cutting_length')

    max_repeat_id = Program.objects.using('sigma').values('program_name').annotate(
        max_repeat_id=Max('repeat_id')
    ).values('max_repeat_id', 'cutting_time')

    pip_queryset = Pip.objects.using('sigma').annotate(
        qty=Subquery(
            max_repeat_id.filter(program_name=OuterRef('program_name')).values('max_repeat_id')[:1]
        ) * F('qty_in_process')
    ).annotate(
        cut_time=Subquery(
            max_repeat_id.filter(program_name=OuterRef('program_name')).values('cutting_time')[:1]
        ) * F('cutting_length') / Subquery(
            total_cutting_length.filter(program_name=OuterRef('program_name')).values('total_cutting_length')[:1]
        )
    ).filter(condition).values_list('wo_number', 'part_name', 'program_name', 'qty', 'cut_time')

    parts_layouts = dict()
    for part, values in map(part_handler, pip_queryset):
        layouts = parts_layouts.get(part, {})
        layouts.update(values)
        parts_layouts[part] = layouts
    # Пример структуры parts_layouts {
    # "№order1 3SP B-30 Balka №30 3": {  наименование детали
    #             '12ГС-43.csv': {
    #                   'count': [3],
    #                   'time': 2.67631 в часах
    #             }
    #       },

    return parts_layouts


def part_handler(row):
    order, part, layout, count, cutting_time = row
    norm_tech = float(cutting_time) / 3600  # переводим в часы
    order_part = f'№{order} {part}'
    layouts = {layout: {
        'count': [count],
        'time': norm_tech,
    }, }
    return order_part, layouts


def create_part_name(shift_task_values):
    workshop = shift_task_values['ws_number']
    name = shift_task_values['workpiece']['name']
    material = shift_task_values['workpiece']['material']
    count = shift_task_values['workpiece']['count']
    order_model = shift_task_values['model_order_query']

    order, model = order_model.split("_")

    # Толщина
    match = re.match(r"^.*?([\d]+),\d.*|^.*?([\d]+)\sГОСТ.*", material)
    if match:
        thickness = match.group(1)
        if not thickness:
            thickness = match.group(2)
    else:
        thickness = ""

    # Наименование
    match = re.match(r"(^.+?)\s\d+х\d+.*", name)
    if match:
        name = match.group(1)

    # Сталь
    steel = ""
    for key, value in STEELS.items():
        material = material.replace("C", "С")  # замена англ на рус
        if key in material:
            steel = value

    if workshop == '102':
        part_name = f"{thickness}{steel} №{order} {name.strip()} {count}"
    else:
        part_name = f"№{order} {thickness}{steel} {name.strip()} {count}"

    part_name = translit(part_name, language_code='ru', reversed=True).replace("'", "")
    return part_name

# Сырой запрос в БД SIGMA
#
# import time
# import pyodbc
#
# def read_plasma_layout_db_raw(dxf):
#     condition = []
#     for order, part in dxf:
#         condition.append(f"WoNumber = '{order}' AND PartName = '{part}'")
#     text_condition = " OR ".join(condition)
#     query = f"""
#         WITH TotalCuttingLength AS (
#             SELECT
#                 ProgramName,
#                 SUM(CuttingLength * QtyInProcess) AS TotalCuttingLength
#             FROM SNDBase.dbo.PIP
#             GROUP BY ProgramName
#         ),
#         MaxRepeatID AS (
#             SELECT
#                 ProgramName,
#                 MAX(RepeatID) AS MaxRepeatId,
#                 CuttingTime
#             FROM SNDBase.dbo.Program
#             GROUP BY ProgramName, CuttingTime
#         )
#         SELECT
#             pip.WONumber,
#             pip.PartName,
#             pip.ProgramName,
#             pip.QtyInProcess * mri.MaxRepeatId AS Qty,
#             pip.CuttingLength * mri.CuttingTime / tcl.TotalCuttingLength AS CuttingTime
#         FROM SNDBase.dbo.PIP as pip
#         JOIN TotalCuttingLength as tcl ON tcl.ProgramName = pip.ProgramName
#         JOIN MaxRepeatID as mri ON mri.ProgramName = pip.ProgramName
#         WHERE ({text_condition})
#     """
#
#     parts_layouts = dict()
#     for part, values in execute_raw_query(query, part_handler):
#         layouts = parts_layouts.get(part, {})
#         layouts.update(values)
#         parts_layouts[part] = layouts
#     return parts_layouts
#
#
# def execute_raw_query(query, handler):
#     start = time.time()
#     try:
#         cnxn = pyodbc.connect(
#             f'DRIVER=SQL Server;'
#             f'SERVER={DATABASES["sigma"]["HOST"]};'
#             f'DATABASE={DATABASES["sigma"]["NAME"]};'
#             f'UID={DATABASES["sigma"]["USER"]};'
#             f'PWD={DATABASES["sigma"]["PASSWORD"]}',
#         )
#         cursor = cnxn.cursor()
#         cursor.execute(query)
#         row = cursor.fetchone()
#         while row:
#             result = handler(row)
#             row = cursor.fetchone()
#             yield result
#         print(f"Завершение запроса в БД. Время выполнения {time.time() - start}")
#     except Exception as ex:
#         print(f"Исключение при работе с БД: {ex}")
#     finally:
#         cnxn.close()

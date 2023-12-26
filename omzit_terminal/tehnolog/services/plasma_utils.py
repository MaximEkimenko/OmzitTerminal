import datetime
import io
import os
import re
import shutil
import time

import pyodbc

import openpyxl
from transliterate import translit

from omzit_terminal.settings import BASE_DIR

BD_SERVER = 'APM-0230\SIGMANEST'
BD_USERNAME = 'SNUser'
BD_PASSWORD = 'BestNest1445'
BD_DATABASE = 'SNDBase'

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

THICKNESS_SPEED = {  # mm: mm/s
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
    condition = []
    for order, part in dxf:
        condition.append(f"WoNumber = '{order}' AND PartName = '{part}'")
    text_condition = " OR ".join(condition)
    query = f"""
        SELECT WoNumber, PartName, ProgramName, QtyProgram, CuttingTime
        FROM (SELECT 
                WoNumber,
                PartName, 
                ProgramName,
                QtyProgram,
                CuttingLength * (
                            SELECT d.CuttingTime
                            FROM SNDBase.dbo.ProgArchive AS d
                            WHERE d.AutoID = (
                                SELECT MAX(c.AutoID)
                                FROM SNDBase.dbo.ProgArchive AS c
                                WHERE c.ProgramName = a.ProgramName
                                GROUP BY c.ProgramName
                        )
                ) / (
                        SELECT SUM(CuttingLength * QtyProgram)
                        FROM SNDBase.dbo.PartArchive as b
                        WHERE b.ProgramName = a.ProgramName
                ) AS CuttingTime
        FROM SNDBase.dbo.PartArchive AS a
        WHERE (
                SELECT SUM(CuttingLength * QtyProgram)
                FROM SNDBase.dbo.PartArchive as b
                WHERE b.ProgramName = a.ProgramName
              ) <> 0
        UNION
        SELECT 
            e.WONumber AS WoNumber,
            e.PartName, 
            e.ProgramName,
            e.QtyInProcess * MAX(e.RepeatID) AS QtyProgram,
            e.CuttingLength * (
                    SELECT j.CuttingTime
                    FROM SNDBase.dbo.ProgArchive AS j
                    WHERE j.AutoID = (
                        SELECT MAX(i.AutoID)
                        FROM SNDBase.dbo.ProgArchive AS i
                        WHERE i.ProgramName = e.ProgramName
                        GROUP BY i.ProgramName
                    )
            ) /     (
                        SELECT SUM(x.CuttingLength * x.QtyInProcess)
                        FROM SNDBase.dbo.PIPArchive AS x
                        WHERE x.ArcDateTime = MAX(e.ArcDateTime) and x.ProgramName = e.ProgramName and x.RepeatID = (
                            SELECT MAX(f.RepeatID)
                            FROM SNDBase.dbo.PIPArchive as f
                            WHERE f.ProgramName = e.ProgramName
                            GROUP BY f.ProgramName
                    )
            ) AS CuttingTime
        FROM SNDBase.dbo.PIPArchive AS e  
        GROUP BY e.PartName, e.WONumber, e.ProgramName, e.QtyInProcess, e.CuttingLength
        HAVING (
                        SELECT SUM(x.CuttingLength * x.QtyInProcess)
                        FROM SNDBase.dbo.PIPArchive AS x
                        WHERE x.ArcDateTime = MAX(e.ArcDateTime) and x.ProgramName = e.ProgramName and x.RepeatID = (
                            SELECT MAX(f.RepeatID)
                            FROM SNDBase.dbo.PIPArchive as f
                            WHERE f.ProgramName = e.ProgramName
                            GROUP BY f.ProgramName
                    )
        ) <> 0   
        ) AS t1
        WHERE ({text_condition})
    """

    parts_layouts = dict()
    for part, values in execute_query(query, part_handler):
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


def execute_query(query, handler):
    start = time.time()
    try:
        cnxn = pyodbc.connect(
            f'DRIVER=SQL Server;'
            f'SERVER={BD_SERVER};'
            f'DATABASE={BD_DATABASE};'
            f'UID={BD_USERNAME};'
            f'PWD={BD_PASSWORD}',
        )
        cursor = cnxn.cursor()
        cursor.execute(query)
        row = cursor.fetchone()
        while row:
            result = handler(row)
            row = cursor.fetchone()
            yield result
        print(f"Завершение запроса в БД. Время выполнения {time.time() - start}")
    except Exception as ex:
        print(f"Исключение при работе с БД: {ex}")
    finally:
        cnxn.close()


def create_part_name(shift_task_values):
    workshop = shift_task_values['ws_number']
    name = shift_task_values['workpiece']['name']
    material = shift_task_values['workpiece']['material']
    count = shift_task_values['workpiece']['count']
    order_model = shift_task_values['model_order_query']
    shift_task = shift_task_values['id']

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

    part_name = translit(part_name, language_code='ru', reversed=True).replace("'", "")
    return part_name

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
    #             '12ГС-43.csv': {
    #                   'count': [3],
    #                   'time': 2.67631 в часах
    #             }
    #       },
    return parts_layouts


def read_plasma_layout_db(dxf):
    parts = [
        '10SP TM-1_D3 Plastina 42',
        '10SP TM-1_D4 Rebro 168',
        '10SP TM-2_D1 Plastina 2',
        '10SP TM-2_D3 Plastina 2',
        '10SP TM-3_D1 Plastina 1',
        '10SP TM-3_D3 Plastina 1',
        '10SP OB47-1  PL3a 2',
        '10SP OB48-1  PL3a 2',
        '10SP B24-2 Pl1 11',
        '10SP OB24-2 Kc8 6',
        '10SP OB28-2 Pb1 27',
    ]
    orders = ['Z572(2023)'] * 6 + ['Z579(2023)'] * 5
    dxf = zip(orders, parts)
    condition = []
    for order, part in dxf:
        condition.append(f"WoNumber = '{order}' and PartName = '{part}'")
    text_condition = " or ".join(condition)
    query = f"""
        SELECT *
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
            )          
        FROM SNDBase.dbo.PartArchive AS a
        UNION
        SELECT 
            e.WONumber,
            e.PartName, 
            e.ProgramName,
            e.QtyInProcess * MAX(e.RepeatID),
            e.CuttingLength * (
                    SELECT j.CuttingTime
                    FROM SNDBase.dbo.ProgArchive AS j
                    WHERE j.AutoID = (
                        SELECT MAX(i.AutoID)
                        FROM SNDBase.dbo.ProgArchive AS i
                        WHERE i.ProgramName = e.ProgramName
                        GROUP BY i.ProgramName
                    )
            ) / (       SELECT SUM(x.CuttingLength * x.QtyInProcess)
                    FROM SNDBase.dbo.PIPArchive AS x
                    WHERE x.ArcDateTime = MAX(e.ArcDateTime) and x.ProgramName = e.ProgramName and x.RepeatID = (
                        SELECT MAX(f.RepeatID)
                        FROM SNDBase.dbo.PIPArchive as f
                        WHERE f.ArcDateTime = MAX(e.ArcDateTime) and f.ProgramName = e.ProgramName
                        GROUP BY f.PartName, f.WONumber, f.ProgramName, f.QtyInProcess, f.CuttingLength
                    )
            )
        FROM SNDBase.dbo.PIPArchive AS e        
        GROUP BY e.PartName, e.WONumber, e.ProgramName, e.QtyInProcess, e.CuttingLength
        ) AS t1
        WHERE {text_condition}
    """

    for row in execute_query(query, lambda x: x):
        print(row)

    parts_layouts = dict()
    for key, values in execute_query(query, part_handler):
        layouts = parts_layouts.get(key, {})
        layouts.update(values)
        parts_layouts[key] = layouts
    # Пример структуры parts_layouts {
    # "№order1 3SP B-30 Balka №30 3": {  наименование детали
    #             '12ГС-43.csv': {
    #                   'count': [3],
    #                   'time': 2.67631 в часах
    #             }
    #       },
    layout_total_time = dict()
    for part, layouts in parts_layouts.items():
        for name, data in layouts.items():
            current_total = layout_total_time.get(name, 0)
            current_total += data['time'] * data['count'][0]
            layout_total_time[name] = current_total
    print(layout_total_time)
    return parts_layouts


def part_handler(row):
    norm_tech = float(row[4])
    key = f'№{row[0]} {row[1]}'
    layouts = {f'{row[2]}': {
        'count': [row[3]],
        'time': norm_tech,
    }, }
    return key, layouts


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

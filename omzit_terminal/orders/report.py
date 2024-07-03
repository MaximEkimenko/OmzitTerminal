import openpyxl
import pandas as pd
from pathlib import Path
from datetime import datetime

from django.forms import model_to_dict
from django.utils.timezone import make_naive
from openpyxl import Workbook

from m_logger_settings import logger
from omzit_terminal.settings import BASE_DIR
from orders.models import Orders
from openpyxl.styles import Font

from orders.utils.utils import orders_to_dict


# def create_order_report(queryset):
#     x = datetime.now()
#     filename = f"report_{x.hour}_{x.minute}_{x.second}.xlsx"
#     mypath = Path(r"D:\temp")
#     fullpath = mypath.joinpath(filename)
#     df = pd.DataFrame.from_records(queryset)
#     print(df)
#     print(fullpath)
#     df.to_csv(filename, index=False, sep="\t", quoting=1)


def create_order_report():

    # font = Font(name="Arial", size=12)
    wb = Workbook()
    ws = wb.active
    ws.title = "Заявки на ремонт"

    verbose_names = dict()
    for field in Orders._meta.get_fields():
        if hasattr(field, "verbose_name"):
            verbose_names[field.name] = field.verbose_name
        else:
            verbose_names[field.name] = field.name
    qs = Orders.objects.values(*verbose_names)
    specific_fields = [
        "id",
        "equipment",
        "status",
        "priority",
        "breakdown_date",
        "breakdown_description",
    ]

    qs = list(Orders.objects.all().values(*specific_fields))
    # print(qs)
    # qs = model_to_dict(qs, specific_fields)
    qs = list(Orders.objects.all())
    qs = orders_to_dict(qs)

    for i, key in enumerate(verbose_names):
        ws.cell(row=1, column=i + 1).value = verbose_names[key]

    for i, row in enumerate(qs):
        for j, key in enumerate(row):
            cell = ws.cell(row=i + 2, column=j + 1)
            try:
                row[key] = make_naive(row[key])
            except Exception as e:
                # logger.exception(e)
                pass
            try:
                cell.value = row[key]
            except ValueError as e:
                logger.error(f"Ошибка при конвертации значения {row[key]} по ключу {key}")
                logger.exception(e)
                cell.value = "error"

    x = datetime.now()
    filename = f"Заявки на ремонт {x.day:02d}_{x.month:02d}_{x.year:04d} {x.hour:02d}_{x.minute:02d}_{x.second:02d}.xlsx"
    exel_file_dst = Path(BASE_DIR).joinpath("xlsx")
    abspath = exel_file_dst.joinpath(filename)
    wb.save(abspath)
    return abspath

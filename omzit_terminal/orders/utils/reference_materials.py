from pathlib import Path
from django.db.models import Count
from openpyxl import load_workbook, Workbook
from orders.utils.xlsx_converter import get_workbook, xlsx_to_html
from orders.models import ReferenceMaterials

def add_reference_materials(file) -> bool:
    """

    @param file: объект файла выбранный через форму (обрабатываемый эксель-локумент)
    @return:
    """
    try:
        wb = load_workbook(file)
    except Exception as e:
        return e

    converted = xlsx_to_html(wb)
    name_count = (ReferenceMaterials.objects.values("original_name")
                  .annotate(name_count=Count("original_name"))
                  .values("original_name", "name_count").all()
                  )
    count_dict = {item["original_name"]: item["name_count"] for item in  name_count}
    print(list(converted.keys()))
    for sheet in converted:
        print(sheet)
        count = count_dict.get(sheet, 0)
        sheetname = sheet if count == 0 else f"{sheet}({count+1})"
        print(dir(file))
        obj = {
            "filename": Path(file.name).stem,  # имя файла без расширения
            "original_name": sheet,
            "sheetname": sheetname,
            "content": converted[sheet]
        }
        ReferenceMaterials.objects.create(**obj)
    return None

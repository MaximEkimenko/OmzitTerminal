from pathlib import Path
from openpyxl import load_workbook, Workbook
from orders.utils.xlsx_converter import get_workbook, xlsx_to_html
from orders.models import ReferenceMaterials
def add_reference_materials(file) -> None:
    #wb = get_workbook(file)
    wb = load_workbook(file)
    converted = xlsx_to_html(wb)
    print(converted[next(iter(converted))])
    for sheet in converted:
        obj = {
            "filename": file.name,
            "sheetname": sheet,
            "content": converted[sheet]
        }
        ReferenceMaterials.objects.create(**obj)
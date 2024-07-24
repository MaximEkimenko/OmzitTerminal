from openpyxl import load_workbook, Workbook
from openpyxl.cell import Cell
from openpyxl.utils import rows_from_range
from pathlib import Path


def get_cell_border(cell: Cell) -> str:
    """
    Проходит по всем сторонам ячейки, и смотрит, есть ли видимые границы. Если есть,
    то формирует строку стиля с указанием имебщихся границ
    """
    border_style = ""
    for direction in ["right", "left", "top", "bottom"]:
        b_s = getattr(cell.border, direction)
        # гранича есть и ее стиль отличается о дефолтного (то есть граница установлена пользователем)
        if b_s and b_s.style is not None:
            border_style += f"border-{direction}: solid 1px;"
        else:
            border_style += f"border-{direction}: none; "
    return border_style


def xlsx_to_html(wb: Workbook,
                worksheets: list[str] = None,
                classes: dict[str, str] = None,
                header: bool = False
                 ) -> dict[str, str]:
    """
    Конвертирования xlsx_file в html с подключением css_file
    :param wb: экселевский документ, из которого происходит экспорт
    :param worksheets: Список листов документа, которые нужно сконвертировать в HTML.
    Если он не указан, то вонвертируются все листы документа
    :param classes: словарь, содержащий классы, для применения к тегам. Если отсутствует, то каждая ячейка
    форматируется индивидуально
    :param header: Если True, то первая строка превращается в заголовок таблицы
    :return: словарь, в качестве ключа название листа документа, в качестве значения: сконвертированный в HTML лист
    """
    if not worksheets:
        worksheets = wb.sheetnames
    # print(worksheets)
    converted_worksheets = {}
    for sheet_name in worksheets:
        ws = wb[sheet_name]
        # Ячейки, исключенные из построения таблицы. Это слитые ячейки, не несущие информации.
        # За исключением первой ячейки в диапазоне
        excluded_cells = set()
        for i in ws.merged_cells.ranges:
            for j in rows_from_range(i.coord):  # по рядам диапазона
                for mc in j:  # по ячейкам в ряду диапазона
                    excluded_cells.add(ws[mc])

        # словарь содержащий размеры объединенных ячеек
        first_merged_cells = {}
        for i in ws.merged_cells.ranges:
            ml = list(ws[i.coord])
            first_cell = ml[0][0]
            cols = len(ml[0])
            rows = len(ml)
            first_merged_cells[first_cell] = (cols, rows)

        # удаляем первые ячейки слитых диапазонов из множества исключенных ячеек
        for i in first_merged_cells:
            excluded_cells.remove(i)
        # построение HTML-документа
        html_row = "<table>"
        html_rows = [html_row]
        html_row = "<thead></htead>"
        html_rows.append(html_row)
        for row in ws.iter_rows():
            html_row = """<tr>"""
            for cell in row:

                if cell.fill.patternType is not None:
                    # bgcolor = f"background-color: #{cell.fill.fgColor.rgb[2:]};"
                    bgcolor = f"background-color: rgba(100, 100, 100, 0.4);"
                else:
                    bgcolor = f"background-color: none;"

                border_style = get_cell_border(cell)
                rowspan_attr = ""
                colspan_attr = ""
                sz = f"font-size: {int(cell.font.sz * 1.7)}px;" if cell.font.sz else ""
                bold = "font-weight: bold;" if cell.font.b else ""
                italic = "font-style: italic;" if cell.font.i else ""
                value = cell.value if cell.value is not None else ""
                if cell in first_merged_cells:
                    merge_cols = first_merged_cells[cell][0]
                    merge_rows = first_merged_cells[cell][1]
                    rowspan_attr = f' rowspan="{merge_rows}"'
                    colspan_attr = f' colspan="{merge_cols}"'
                elif cell in excluded_cells:
                    continue
                html_row += f'<td{rowspan_attr}{colspan_attr} class="td_cell"  style="{sz} {bold} {italic} {bgcolor} {border_style}">{value} </td>'
            html_row += "</tr>"
            html_rows.append(html_row)
        converted_worksheets[sheet_name] = "\n".join(html_rows)
    return converted_worksheets



def html_save(directory, converted_sheets: dict, style_file=None ):
        html_template = """
        <!DOCTYPE html>
        <html>
        <head>
            {0}
            <style>
            </style>
        </head>
        <body>
          {1}
        </body>
        </html>
        """
        ctyle = ""
        if style_file:
            ctyle = '< linkrel = "stylesheet"type = "text/css" href = "{css_file}" >'


        for sheet in converted_sheets:
            # сохранение в файл
            html_table = html_template.format(ctyle, converted_sheets[sheet])
            output_file = Path.joinpath(directory, f"{sheet}.html")
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(html_table)

def prepare_output_directory(source_directory: str, output_dirmane: str) -> Path:
    """
    Создает и возвращает директорию для выгрузки созданных HTML-файлов.
    Если у директории уже есть файлы, они удаляются
    """
    source_directory = Path(source_directory)
    output_dir: Path = source_directory.joinpath(output_dirmane)
    if not output_dir.exists():
        output_dir.mkdir()
    else:
        for i in output_dir.glob("*"):
            i.unlink()
    return output_dir


def get_workbook(xlsx_file: str) -> Workbook:
    xlsx_file = Path(xlsx_file)
    wb = load_workbook(xlsx_file)
    return wb


if __name__ == '__main__':
    xlsx_file_tst = r'D:\python_temp\convert_from_excel\График ППР 2024 ЦЕХ №2.xlsx'
    css_file = r'..\scheduler.css'

    output_direcory = prepare_output_directory(Path(xlsx_file_tst).parent, "результат")
    workbook = get_workbook(xlsx_file_tst)
    convered_sheets = xlsx_to_html(workbook, )

    html_save(output_direcory, convered_sheets, css_file)

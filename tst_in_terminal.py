import openpyxl
from madmodule import create_list

exel_file_dir = r'O:\ПТО\котлы\Трудоемкость котлов\Трудоемкость котлов'
exclusion_list = ('Интерполяция М', 'гофрирование', 'Интерполяция R')
dir_list = create_list(exel_file_dir, result_type='dirs', extension='.xlsx')
file_list = create_list(exel_file_dir, result_type='files', extension='.xlsx')

file = r'D:\АСУП\Python\Projects\OmzitTerminal\Трудоёмкость серия I.xlsx'
ex_wb = openpyxl.load_workbook(file,  data_only=True)
sheets = []
for name in ex_wb.sheetnames:
    if name not in exclusion_list:
        sheets.append(name)


print(sheets)




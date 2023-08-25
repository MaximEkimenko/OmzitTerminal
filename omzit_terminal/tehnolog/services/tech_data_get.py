import openpyxl
import re
from ..models import TechData, ProductCategory, ProductModel


def tech_data_get(exel_file: str, model_list: list = None, category: str = 'Котлы',
                  exclusion_list: tuple = ('Интерполяция М', 'гофрирование', 'Интерполяция R')) -> None:
    """
    Функция получает технологические данные из файла exel_file по списку моделей изделия model_list,
    который равен списку имен листов файла исключая имена листов в списке exclusion_list и сохраняет в модели
    django ProductModel, TechData
    :param category: категория изделия Котлы или АБМК
    :param exel_file: имя файла excel
    :param model_list: список моделей изделия для получения данных - список листов книги excel
    :param exclusion_list: список листов книги excel файла для исключения из чтения
    :return: None
    """
    # TODO вместо cat_id сделать нормальный запрос ORM к ProductCategory!
    if str(category).strip() == 'Котлы':
        cat_id = 1
    elif str(category).strip() == 'АБМК':
        cat_id = 2
    # exclusion_list = ('Интерполяция М', 'гофрирование', 'Интерполяция R')
    ex_wb = openpyxl.load_workbook(exel_file, data_only=True)
    # получение списка моделей изделия, если не указана модель
    # Если список моделей не указан явно, то забираем имена моделей из листов
    if model_list is None:
        model_list = []
        for sheet_name in ex_wb.sheetnames:
            if sheet_name not in exclusion_list:
                model_list.append(sheet_name)
    for model_name in model_list:
        model_name = model_name.strip()
        # добавление модели изделия если такой ещё не было в модель ProductModel
        if not ProductModel.objects.filter(model_name=model_name).exists():
            ProductModel.objects.create(model_name=model_name)
        ex_sh = ex_wb[model_name.strip()]
        op_number_template = r'\d\d.\d\d*'  # шаблон номера операции
        # Если по модели TechData была запись, то удаляются все записи модели
        if TechData.objects.filter(model_name=model_name).exists():
            TechData.objects.filter(model_name=model_name).delete()
            print('Удалено!')
        # определение максимальной строки для чтения
        max_read_row = 1
        for row in ex_sh.iter_rows(min_row=2, min_col=1, max_row=ex_sh.max_row,
                                   max_col=2, values_only=True):
            max_read_row += 1
            if 'итого' in str(row[1]).lower():
                break
        # добавление в модель TechData технологических данных
        for row in ex_sh.iter_rows(min_row=1, min_col=1, max_row=max_read_row,
                                   max_col=12, values_only=True):
            if re.fullmatch(op_number_template, str(row[0])):
                # TODO сделать отдельной функцией
                TechData.objects.create(model_name=model_name,
                                        op_number=row[0],
                                        op_name=row[1],
                                        ws_name=row[2],
                                        op_name_full=row[1] + '-' + row[2],
                                        ws_number=str(row[3]),
                                        norm_tech=row[11],
                                        product_category=ProductCategory(id=cat_id)  # TODO сделать нормальный запрос
                                        )
                # TODO передать сообщение
                print('Добавлено!')
                previous_op_number = str(row[0])  # обработка объединенных ячеек имени операции
                previous_op_name = row[1]
                # print(row[0], '---', row[1], row[2], row[11], )
            elif row[0] is None and row[2] is not None:  # если объединённая ячейка
                # добавление в модель технологических данных
                TechData.objects.create(model_name=model_name,
                                        op_number=previous_op_number,
                                        op_name=previous_op_name,
                                        ws_name=row[2],
                                        op_name_full=previous_op_name + '-' + row[2],
                                        ws_number=str(row[3]),
                                        norm_tech=row[11],
                                        product_category=ProductCategory(id=cat_id)
                                        )


if __name__ == '__main__':
    ex_file_dir_tst = r'D:\АСУП\Python\Projects\OmzitTerminal\Трудоёмкость серия I.xlsx'
    model_list_tst = ['7000М+', '800М+']
    exclusion_list_tst = ('Интерполяция М', 'гофрирование', 'Интерполяция R')
    tech_data_get(exel_file=ex_file_dir_tst)

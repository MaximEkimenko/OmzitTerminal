import logging

import pandas as pd

from rapidfuzz import fuzz

# НЕ МЕНЯТЬ ПОРЯДОК И НЕ УДАЛЯТЬ! ТОЛЬКО ДОБАВЛЯТЬ В КОНЕЦ! НАЗВАНИЯ МОЖНО МЕНЯТЬ, А СУТЬ - НЕТ!
# ЕСЛИ ИЗМЕНИТЬ, ТО ПРИДЕТСЯ МЕНЯТЬ ВСЕ ИНДЕКСЫ ПО КОДУ
COLUMNS = [
    'п/п',  # 0
    'Наименование работ',  # 1
    'Рабочий центр',  # 2
    '№ рабочего центра',  # 3
    'ГОСТ и тип сварочного шва',  # 4
    'ед.изм.',  # 5
    'Объём работ (максимальный в смену)',  # 6
    'Трудоёмкость в смену, час',  # 7
    'Численность, чел.',  # 8
    'Трудоёмкость на 1 ед./заготовку, чел/час',  # 9
    'Кол-во ед./ заготовок на 1 котел',  # 10
    'Трудоёмкость на 1 котел, чел/час',  # 11
    'Расценка за объем работ, руб.',  # 12
    'Стоимость часа, руб',  # 13
    'Загрузка оборудования на 1 котел, часов',  # 14
    'Наименование',  # 15
    'Материал',  # 16
    'Количество',  # 17
    'Длина',  # 18
    'Чертеж',  # 19
    'id',  # 20
    'Следующая операция',  # 21
    'Предыдущая операция'  # 22
]


def get_all_category(xlsx_file):
    sheet_names = xlsx_file.sheet_names
    categories = dict()
    for sheet in sheet_names:
        all_data = xlsx_file.parse(sheet)
        for category in all_data[
                            all_data.iloc[:, 1].str.contains(r'^\d+\.[^\d]{1}.*', na=False)
                        ].iloc[:, 1].to_list():
            categories[category.split('.')[0]] = category
    return categories


def sheet_handler(data):
    try:
        filtered_data = data[data.iloc[:, 2].notna()]
        new_columns = dict()
        filtered_data.columns = filtered_data.iloc[0].tolist()
        for title in filtered_data.columns:
            for column in COLUMNS:
                score = fuzz.ratio(str(title), column) / 100
                if score > 0.85:
                    new_columns[title] = column
        filtered_data = filtered_data.rename(columns=new_columns)
        filtered_data = filtered_data.iloc[1:]
        filtered_data = filtered_data.filter(items=list(new_columns.values()))
        filtered_data = filtered_data[filtered_data[COLUMNS[13]].astype(str).str.isdigit()]
        filtered_data.iloc[:, 0:2] = filtered_data.iloc[:, 0:2].ffill()
        return filtered_data
    except Exception as ex:
        logging.exception(ex)


def get_all_operations(xlsx_file_names):
    operations = pd.DataFrame(columns=COLUMNS[:15])
    for xlsx_file_name in xlsx_file_names:
        xlsx_file = pd.ExcelFile(xlsx_file_name)
        sheet_names = xlsx_file.sheet_names
        for sheet in sheet_names:
            try:
                all_data = xlsx_file.parse(sheet)
                filtered_data = sheet_handler(all_data)
                operations = pd.concat([operations, filtered_data])
                operations = operations.drop_duplicates()
                operations.index = range(0, len(operations))
            except Exception as ex:
                logging.warning(f'При чтении данных с листа {sheet} возникло исключение:')
                logging.exception(ex)
    operations.index = range(0, len(operations))
    operations.to_excel('operations.xlsx')


if __name__ == "__main__":
    get_all_operations([r'D:\Projects\TechnologWS\Трудоёмкость серия SV.xlsx'])

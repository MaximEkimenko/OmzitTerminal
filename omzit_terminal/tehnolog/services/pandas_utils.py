import pandas as pd
from rapidfuzz import fuzz

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
    'Ссылка на чертежи',  # 15
]


def sheet_handler(data):
    end_index = data.index[data.iloc[:, 1].str.contains('ИТОГО', na=False)].tolist()[0]
    filtered_data = data.head(end_index)
    filtered_data = filtered_data[data.iloc[:, 2].notna()]
    new_columns = dict()
    filtered_data.columns = filtered_data.iloc[0].tolist()
    for title in filtered_data.columns:
        for column in COLUMNS:
            score = fuzz.ratio(str(title), column) / 100
            if score > 0.87:
                new_columns[title] = column
                break
    no_columns = []
    for column in COLUMNS:
        if column not in new_columns.values():
            no_columns.append(column)
    if len(no_columns) > 0:
        raise KeyError(f"Не найдены столбцы: {', '.join(no_columns)}")
    filtered_data = filtered_data.rename(columns=new_columns)
    filtered_data = filtered_data.iloc[1:]
    filtered_data = filtered_data.filter(items=list(new_columns.values()))
    filtered_data = filtered_data[filtered_data[COLUMNS[13]].astype(str).str.isdigit()]
    filtered_data.iloc[:, 0:2] = filtered_data.iloc[:, 0:2].ffill()
    return filtered_data


def df_handler(df, start_id=0):
    filtered_data = sheet_handler(df)
    if filtered_data is None:
        filtered_data = pd.DataFrame()
    filtered_data = filtered_data.reindex(columns=COLUMNS)
    filtered_data['id'] = range(start_id + 1, len(filtered_data) + start_id + 1)
    return filtered_data

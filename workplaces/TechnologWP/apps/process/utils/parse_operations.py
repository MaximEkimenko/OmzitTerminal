import logging
import re

import pandas as pd

from rapidfuzz import fuzz

from apps.process.settings import COLUMNS


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


def df_handler(df, start_id=0):
    filtered_data = sheet_handler(df)
    if filtered_data is None:
        filtered_data = pd.DataFrame()
    filtered_data = filtered_data.reindex(columns=COLUMNS)
    filtered_data['id'] = range(start_id + 1, len(filtered_data) + start_id + 1)

    def next_prev_handler(x):
        if str(x) not in ['nan', '']:
            values = re.split(r',|\.', str(x).strip('[]'))
            return list(map(lambda y: int(y.strip()), values))
        else:
            return []

    filtered_data[COLUMNS[21]] = filtered_data[COLUMNS[21]].apply(next_prev_handler)
    filtered_data[COLUMNS[22]] = filtered_data[COLUMNS[22]].apply(next_prev_handler)
    return filtered_data


if __name__ == "__main__":
    get_all_operations([r'D:\Projects\TechnologWS\Трудоёмкость серия SV.xlsx'])

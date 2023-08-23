# import sqlite3
import psycopg2
import datetime
from tech_data_get import tech_data_get
from db_config import host, dbname, user, password


def db_handle(ex_file: str, models_list: list = None,
              exclusion_list: tuple = ('Интерполяция М', 'гофрирование', 'Интерполяция R')):
    # получение списка данных операций по моделям
    model_list, tech_data_list = (
        tech_data_get(exel_file=ex_file, model_list=models_list, exclusion_list=exclusion_list))
    # print(tech_data_list)
    # print(models_list)
    try:
        con = psycopg2.connect(dbname=dbname, user=user, password=password, host=host)
        con.autocommit = True
        for model in models_list:
            time_now = datetime.datetime.now()  # время сейчас
            # проверка существования таблицы
            try:
                with con.cursor() as cur:
                    cur.execute(f"""select count(*) from "{model}" LIMIT 1 """)
                print(f'Таблица {model} существует.')
                # TODO добавить алерт о существовании и согласии на обновление
                table_exists = True
            except Exception as e:
                print(e, f'Таблица {model} создана.')
                table_exists = False
            # table_exists = False
            # создание таблицы с именем модели
            create_query = f"""CREATE TABLE IF NOT EXISTS "{model}"
                                        (id serial PRIMARY KEY,
                                        model_name  varchar(32),
                                        op_number  varchar(10),
                                        op_name varchar(200),
                                        ws_name varchar(100),
                                        op_name_full varchar(300),
                                        ws_number varchar(50),
                                        norm_tech real,
                                        datetime_update timestamp);"""
            try:
                with con.cursor() as cur:
                    cur.execute(create_query)
            except Exception as e:
                print(e, 'ошибка при создании')
            # если таблица существует, то удаляем её содержимое
            if table_exists:
                delete_table_query = f"""DELETE FROM "{model}" """
                try:
                    with con.cursor() as cur:
                        cur.execute(delete_table_query)
                    print(f'Таблица {model} очищена')
                except Exception as e:
                    print(e)
            # добавляем данные в таблицу
            for row in tech_data_list:
                if row[0] == model:
                    insert_query = f"""INSERT INTO "{model}"
                                    (model_name, op_number, op_name, ws_name, op_name_full,
                                                    ws_number, norm_tech, datetime_update)
                                    VALUES ('{row[0]}', '{row[1]}', '{row[2]}', '{row[3]}',
                                            '{row[4]}', '{row[5]}', '{row[6]}', '{str(time_now)}')"""
                    try:
                        with con.cursor() as cur:
                            cur.execute(insert_query)
                        table_updated = True
                    except Exception as e:
                        print(e)
                        table_updated = False
            if table_updated and table_exists:
                print(f'Таблица {model} обновлена.')
            elif table_updated:
                print(f'Таблица {model} заполнена.')
    except Exception as e:
        print('Ошибка соединения с БД', e)
    finally:
        con.close()


if __name__ == '__main__':
    ex_file_tst = r'D:\АСУП\Python\Projects\OmzitTerminal\Трудоёмкость серия I.xlsx'
    model_list_tst = ['4500I+', '3000I+']
    exclusion_list_tst = ('Интерполяция М', 'гофрирование', 'Интерполяция R')
    db_handle(ex_file=ex_file_tst, models_list=model_list_tst)

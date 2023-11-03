import threading
import time

import psycopg2
from .db_config import host, dbname, user, password  # TODO перенести в env весь файл db_config


def continue_work(st_number):
    print(f'Через 10 минут статус СЗ {st_number} измениться на "в работе"')
    time.sleep(600)
    try:
        con = psycopg2.connect(dbname=dbname, user=user, password=password, host=host)
        con.autocommit = True
        update_query = f"""
        UPDATE shift_task 
        SET st_status='в работе' 
        WHERE id = '{st_number}' AND st_status = 'ожидание мастера';
        """
        try:
            with con.cursor() as cur:
                cur.execute(update_query)
                con.commit()
        except Exception as e:
            print(e, 'ошибка обновления')
    except Exception as e:
        print('Ошибка подключения к базе', e)
    finally:
        con.close()


def select_master_call(ws_number: str, st_number) -> list or None:
    """
    Функция делает выборку из базы по РЦ и master_called = не было и формирует список сообщений из результатов запроса.
    Меняет master_called на вызван
    :param st_number: номер сменного задания (id)
    :param ws_number: номер рабочего центра
    :return: список сообщений для мастера
    """
    messages_to_master = []  # список сообщений для мастера
    try:
        # подключение к БД
        con = psycopg2.connect(dbname=dbname, user=user, password=password, host=host)
        con.autocommit = True
        # запрос на все статусы ожидания мастера
        select_query = f"""SELECT id, model_name, "order", op_number, op_name_full, fio_doer
                        FROM shift_task
                        WHERE st_status='в работе' AND
                        id = '{st_number}'               
                        """
        try:
            with con.cursor() as cur:
                cur.execute(select_query)
                con.commit()
                shift_tasks = cur.fetchall()
                for task in shift_tasks:
                    # print(task)
                    message_to_master = (f"Мастера ожидают на Т{ws_number}. Номер СЗ: {task[0]}. Заказ: {task[1]}. "
                                         f"Изделие: {task[2]}. Операция: {task[3]} {task[4]}. "
                                         f"Исполнители: {task[5]}")
                    messages_to_master.append(message_to_master)
        except Exception as e:
            print(e, 'ошибка выборке')
        if not messages_to_master:  # выход при отсутствии записей
            return None
        else:  # обновление переменной факта вызова мастера
            print('Обновление статуса')
            update_query = f"""
                        UPDATE shift_task 
                        SET master_called = 'вызван', st_status='ожидание мастера', master_calls=master_calls+1
                        WHERE id = '{st_number}';
                        """
            try:
                with con.cursor() as cur:
                    cur.execute(update_query)
                    con.commit()
                    thread = threading.Thread(target=continue_work, args=(st_number,))
                    thread.start()
            except Exception as e:
                print(e, 'ошибка обновления')
    except Exception as e:
        print('Ошибка подключения к базе', e)
    finally:
        con.close()
    # print(messages_to_master)
    return messages_to_master


def select_dispatcher_call(ws_number: str, st_number) -> list or None:
    messages_to_dispatcher = []  # список сообщений для мастера
    try:
        print(ws_number, st_number)
        # подключение к БД
        con = psycopg2.connect(dbname=dbname, user=user, password=password, host=host)
        con.autocommit = True
        # запрос на все статусы ожидания мастера
        select_query = f"""SELECT id, model_name, "order", op_number, op_name_full, fio_doer
                            FROM shift_task
                            WHERE 
                            id = '{st_number}'
                        """
        try:
            with con.cursor() as cur:
                cur.execute(select_query)
                con.commit()
                shift_tasks = cur.fetchall()
                for task in shift_tasks:
                    # print(task)
                    message_to_dispatcher = (f"Диспетчера ожидают на РЦ {ws_number}. Номер СЗ: {task[0]}. Заказ: {task[1]}. "
                                             f"Изделие: {task[2]}. Операция: {task[3]} {task[4]}. "
                                             f"Исполнители: {task[5]}")
                    messages_to_dispatcher.append(message_to_dispatcher)
        except Exception as e:
            print(e, 'ошибка выборке')
        if not messages_to_dispatcher:  # выход при отсутствии записей
            return None
    except Exception as e:
        print('Ошибка подключения к базе', e)
    finally:
        con.close()
    return messages_to_dispatcher


if __name__ == '__main__':
    pass

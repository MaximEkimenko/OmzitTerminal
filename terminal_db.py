import psycopg2
from db_config import host, dbname, user, password


def select_master_call(ws_number: str) -> list or None:
    """
    Функция делает выборку из базы по РЦ и master_called = не было и формирует список сообщений из результатов запроса.
    Меняет master_called на вызван
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
                        WHERE st_status='ожидание мастера' AND 
                        ws_number = '{ws_number}' AND
                        master_called = 'не было'                
                        """
        try:
            with con.cursor() as cur:
                cur.execute(select_query)
                con.commit()
                shift_tasks = cur.fetchall()
                for task in shift_tasks:
                    print(task)
                    message_to_master = (f"Вас ожидают на РЦ {ws_number}. Номер СЗ: {task[0]}. Заказ: {task[1]}. "
                                         f"Изделие: {task[2]}. Операция: {task[3]} {task[4]}. "
                                         f"Исполнители: {task[5]}")
                    messages_to_master.append(message_to_master)
        except Exception as e:
            print(e, 'ошибка выборке')
        if not messages_to_master:
            return None
        else:  # обновление переменной факта вызова мастера
            print('Обновление статуса')
            update_query = f"""UPDATE shift_task SET master_called = 'вызван'
                                        WHERE st_status='ожидание мастера' AND 
                                        ws_number = '{ws_number}' AND
                                        master_called = 'не было'; 
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
    print(messages_to_master)
    return messages_to_master



if __name__ == '__main__':
    select_master_call("109")

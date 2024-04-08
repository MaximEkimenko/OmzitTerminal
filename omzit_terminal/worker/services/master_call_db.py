import threading
import time
from m_logger_settings import logger

import psycopg2
from .db_config import host, dbname, user, password


def continue_work(st_number):
    """
    TODO в текущей логике процесса не используется
    Функция автоматического возобновления работы по СЗ через time.sleep(n) секунд (смена статус с 'ожидание мастера'
    на 'в работе')
    :param st_number: Номер сменного задания
    :return:
    """
    n_seconds = 600
    logger.info(f'Через {int(n_seconds/60)} минут статус СЗ {st_number} изменится на "в работе"')
    time.sleep(n_seconds)
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
            logger.error(f'ошибка обновления {st_number} в функции continue_work')
            logger.exception(e)
    except Exception as e:
        logger.error(f'Ошибка подключения к базе {dbname} в функции continue_work.')
        logger.exception(e)
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
                        WHERE st_status in ('в работе', 'пауза')  AND
                        id = '{st_number}'               
                        """
        try:
            with con.cursor() as cur:
                cur.execute(select_query)
                con.commit()
                shift_tasks = cur.fetchall()
                for task in shift_tasks:
                    message_to_master = (f"Мастера ожидают на Т{ws_number}. Номер СЗ: {task[0]}. Заказ: {task[1]}. "
                                         f"Изделие: {task[2]}. Операция: {task[3]} {task[4]}. "
                                         f"Исполнители: {task[5]}")
                    messages_to_master.append(message_to_master)
        except Exception as e:
            logger.error(f'ошибка выборки  Т{ws_number} СЗ{st_number} из {dbname} при вызове мастера')
            logger.exception(e)
        if not messages_to_master:  # выход при отсутствии записей
            return None
        else:  # обновление переменной факта вызова мастера
            logger.info(f'Обновление статуса СЗ{st_number} после вызова мастера')
            update_query = f"""
                        UPDATE shift_task 
                        SET master_called = 'вызван', st_status='ожидание мастера', master_calls=master_calls+1
                        WHERE id = '{st_number}';
                        """
            try:
                with con.cursor() as cur:
                    cur.execute(update_query)
                    con.commit()
                    # не используемый функционал в текущей ревизии процесса: функция continue_work
                    # thread = threading.Thread(target=continue_work, args=(st_number,))
                    # thread.start()
            except Exception as e:
                logger.error(f'ошибка обновления {st_number} в функции select_master_call')
                logger.exception(e)
    except Exception as e:
        logger.error(f'Ошибка подключения к базе {dbname} в функции select_master_call')
        logger.exception(e)
    finally:
        con.close()
    return messages_to_master


def select_dispatcher_call(ws_number: str, st_number) -> list or None:
    messages_to_dispatcher = []  # список сообщений для мастера
    try:
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
                    message_to_dispatcher = (f"Диспетчера ожидают на РЦ {ws_number}. Номер СЗ: {task[0]}. Заказ: {task[1]}. "
                                             f"Изделие: {task[2]}. Операция: {task[3]} {task[4]}. "
                                             f"Исполнители: {task[5]}")
                    messages_to_dispatcher.append(message_to_dispatcher)
        except Exception as e:
            logger.error(f'ошибка выборки  Т{ws_number} СЗ{st_number} из {dbname} при вызове диспетчера')
            logger.exception(e)
        if not messages_to_dispatcher:  # выход при отсутствии записей
            return None
    except Exception as e:
        logger.error(f'Ошибка подключения к базе {dbname} в функции select_dispatcher_call')
        logger.exception(e)
    finally:
        con.close()
    return messages_to_dispatcher


if __name__ == '__main__':
    pass

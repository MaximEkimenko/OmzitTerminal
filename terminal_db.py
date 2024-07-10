from omzit_terminal.m_logger_settings import logger
import datetime


import psycopg2
from omzit_terminal.worker.services.db_config import host, dbname, user, password


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
                    message_to_master = (f"Вас ожидают на Т{ws_number}. Номер СЗ: {task[0]}. Заказ: {task[1]}. "
                                         f"Изделие: {task[2]}. Операция: {task[3]} {task[4]}. "
                                         f"Исполнители: {task[5]}")
                    messages_to_master.append(message_to_master)
        except Exception as e:
            logger.error(f'Ошибка в выборке select_master_call {ws_number}')
            logger.exception(e)
        if not messages_to_master:
            return None
        else:  # обновление переменной факта вызова мастера
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
                logger.error(f'Ошибка обновления переменной количества вызовов мастера {ws_number}')
                logger.exception(e)
    except Exception as e:
        logger.error(f'Ошибка подключения к базе при select_master_call {ws_number}')
        logger.exception(e)
    finally:
        con.close()
    return messages_to_master


def ws_list_get(status: str) -> tuple:
    """
    Получение tuple уникальных РЦ запросом из базы со статусом status
    :param status: строка статуса
    :return: tuple РЦ
    """
    ws_list = set()  # список сообщений для мастера
    try:
        # подключение к БД
        con = psycopg2.connect(dbname=dbname, user=user, password=password, host=host)
        con.autocommit = True
        # запрос на все статусы ожидания мастера получение списка контролёров
        select_query = f"""SELECT ws_number
                            FROM shift_task
                            WHERE st_status='{status}';"""
        try:
            with con.cursor() as cur:
                cur.execute(select_query)
                con.commit()
                for shift_task in cur.fetchall():
                    ws_list.add(shift_task[0])
        except Exception as e:
            logger.error(f'Ошибка в выборке списка РЦ ws_list_get {status}')
            logger.exception(e)
    except Exception as e:
        logger.error(f'Ошибка подключения к базе при получении списка РЦ ws_list_get {status}')
        logger.exception(e)
    finally:
        con.close()
    ws_list = tuple(sorted(ws_list))
    # print(ws_list)
    return ws_list


def st_list_get(ws_number: str) -> tuple:
    """
    Получение tuple СЗ с РЦ запросом из базы со статусом status
    :return: tuple РЦ
    """
    st_set = set()  # список сообщений для мастера
    try:
        # подключение к БД
        con = psycopg2.connect(dbname=dbname, user=user, password=password, host=host)
        con.autocommit = True
        # запрос на РЦ со статусом ожидание контролёра
        select_query = f"""SELECT id, ws_number, op_name_full
                            FROM shift_task
                            WHERE st_status='ожидание контролёра' AND
                            ws_number = '{ws_number}';
                            """
        try:
            with con.cursor() as cur:
                cur.execute(select_query)
                all_tasks = list(cur.fetchall())
        except Exception as e:
            logger.error(f'Ошибка в выборке списка СЗ st_list_get {ws_number}')
            logger.exception(e)
        for shift_task in all_tasks:
            st = f"№ {shift_task[0]} | T{shift_task[1]} | {shift_task[2]}"  # форматирование строки
            st_set.add(st)
    except Exception as e:
        logger.error(f'Ошибка подключения к базе при получении списка СЗ st_list_get {ws_number}')
        logger.exception(e)
    finally:
        con.close()
    st_set = tuple(sorted(st_set))
    return st_set


def master_id_get(ws_number: str = None, st_id: str = None) -> tuple:
    """
    Получает id мастера и ws_number по РЦ ws_number или id записи
    :param st_id: id записи в БД
    :param ws_number: номер РЦ
    :return: id мастера
    """
    if ws_number:
        query_field = 'ws_number'
        query_var = ws_number
    elif st_id:
        query_field = 'id'
        query_var = st_id
    else:
        query_field = ''
        query_var = ''
        logger.error(f'Неверно заполненные параметры при вызове master_id_get {ws_number=}, {st_id=}')
    try:
        # подключение к БД
        con = psycopg2.connect(dbname=dbname, user=user, password=password, host=host)
        con.autocommit = True
        # запрос на РЦ со статусом ожидание контролёра
        select_query = f"""SELECT master_finish_wp, ws_number
                                FROM shift_task
                                WHERE st_status = 'ожидание контролёра' AND
                                {query_field} = '{query_var}';"""
        try:
            with con.cursor() as cur:
                cur.execute(select_query)
                con.commit()
                master_id, ws_result_number = cur.fetchone()
        # Обработка повторных запросов
        except TypeError:
            check_query = f"""SELECT st_status FROM shift_task WHERE {query_field} = '{query_var}';"""
            with con.cursor() as cur:
                cur.execute(check_query)
                con.commit()
                st_status = cur.fetchone()
            logger.warning(f'Вероятно повторная попытка обратится к сменному заданию со статусом '
                           f'"{st_status[0]}" {ws_number=}, {st_id=}')
            return st_status[0], None
    except Exception as e:
        logger.error(f'Ошибка подключения к базе при получении id мастера master_id_get. {ws_number=}, {st_id=}')
        logger.exception(e)
    finally:
        con.close()
    return master_id, ws_result_number


def control_man_id_get(ws_number: str = None) -> tuple:
    try:
        # подключение к БД
        con = psycopg2.connect(dbname=dbname, user=user, password=password, host=host)
        con.autocommit = True
        # запрос на РЦ со статусом ожидание контролёра
        select_query = f"""SELECT otk_answer
                                FROM shift_task
                                WHERE st_status='ожидание контролёра' AND
                                ws_number = '{ws_number}';"""
        try:
            with con.cursor() as cur:
                cur.execute(select_query)
                con.commit()
                control_man_id = cur.fetchone()

        except Exception as e:
            logger.error(f'Ошибка в выборке id контролёра в control_man_id_get. {ws_number=}')
            logger.exception(e)
    except Exception as e:
        logger.error(f'Ошибка подключения к базе при получении id контролёра в control_man_id_get. {ws_number=}')
        logger.exception(e)
    finally:
        con.close()
    return control_man_id


def status_change_to_otk(ws_number: str, initiator_id: str) -> None:
    """
    Изменение данных СЗ при вызове контролёра
    :param ws_number: номер РЦ
    :param initiator_id: telegram_id мастера
    :return: None
    """
    try:
        # подключение к БД
        con = psycopg2.connect(dbname=dbname, user=user, password=password, host=host)
        con.autocommit = True
        # запрос на корректировку БД
        update_query = f"""UPDATE shift_task SET st_status = 'ожидание контролёра',
                                        master_finish_wp = '{initiator_id}', 
                                        datetime_otk_call = '{datetime.datetime.now()}'
                                        WHERE st_status='ожидание мастера' AND 
                                        ws_number = '{ws_number}'"""
        try:
            with con.cursor() as cur:
                cur.execute(update_query)
                con.commit()
        except Exception as e:
            logger.error(f'Ошибка в выборке при смене статуса ОТК в status_change_to_otk. '
                         f'{ws_number=}, {initiator_id=}')
            logger.exception(e)
    except Exception as e:
        logger.error(f'Ошибка подключения к базе при смене статуса ОТК в status_change_to_otk. '
                     f'{ws_number=} {initiator_id=}')
        logger.exception(e)
    finally:
        con.close()


def lines_count(ws_number: str) -> tuple:
    """
    Количество записей по ws_number и проверяет факт наличия УЗК или рентгена
    :param ws_number:
    :return: tuple (количество СЗ для приёмки, строка операций УЗК)
    """
    try:
        # подключение к БД
        con = psycopg2.connect(dbname=dbname, user=user, password=password, host=host)
        con.autocommit = True
        # запрос количества СЗ
        count_query = f"""SELECT COUNT(id) from shift_task where ws_number='{ws_number}' AND
                           st_status='ожидание контролёра'"""
        # запрос на проверку УЗК
        ultra_sound_query = f"""SELECT op_name from shift_task 
                            WHERE ws_number='{ws_number}' AND
                            st_status='ожидание контролёра' AND
                            op_name like '% УЗК %' OR
                            st_status='ожидание контролёра' AND
                            op_name like '%Рентген %'
                            """
        # Количество СЗ
        try:
            with con.cursor() as cur:
                cur.execute(count_query)
                con.commit()
                ws_count = cur.fetchall()
        except Exception as e:
            logger.error(f'Ошибка в выборке количества сменных заданий в lines_count. {ws_number=}')
            logger.exception(e)
        # проверка УЗК
        try:
            with con.cursor() as cur:
                cur.execute(ultra_sound_query)
                con.commit()
                ultra_sounds = cur.fetchall()
                if ultra_sounds:
                    ultra_sound_string = ', '.join([line for line in ultra_sounds[0]])
                else:
                    ultra_sound_string = ''
        except Exception as e:
            logger.error(f'Ошибка в выборке сменных заданий с УЗК и РК. {ws_number=}')
            logger.exception(e)
    except Exception as e:
        logger.error(f'Ошибка подключения к базе при lines_count. {ws_number=}')
        logger.exception(e)
    finally:
        con.close()
    return ws_count[0][0], ultra_sound_string


def control_man_id_set(ws_number, controlman_id):
    """
    Запись id контролёра при ответе на вызов
    :param ws_number:
    :param controlman_id:
    :return:
    """
    try:
        # подключение к БД
        con = psycopg2.connect(dbname=dbname, user=user, password=password, host=host)
        con.autocommit = True
        # запрос на корректировку БД
        update_query = f"""UPDATE shift_task SET otk_answer = '{controlman_id}', 
                                        datetime_otk_answer = '{datetime.datetime.now()}'
                                        WHERE st_status='ожидание контролёра' AND 
                                        ws_number = '{ws_number}'"""
        try:
            with con.cursor() as cur:
                cur.execute(update_query)
                con.commit()
        except Exception as e:
            logger.error(f'Ошибка в обновлении id контролёра при ответе на вызов в control_man_id_set. '
                         f'{ws_number=} {controlman_id=}')
            logger.exception(e)
    except Exception as e:
        logger.error(f'Ошибка подключения к базе при обновлении id контролёра при ответе на вызов '
                     f'в control_man_id_set. {ws_number=} {controlman_id=}')
        logger.exception(e)
    finally:
        con.close()


def decision_data_set(st_id, controlman_id, decision):
    """
    Обновление данных в БД при решении контролёра
    :param st_id:
    :param controlman_id:
    :param decision:
    :return:
    """
    try:
        # подключение к БД
        con = psycopg2.connect(dbname=dbname, user=user, password=password, host=host)
        con.autocommit = True
        # запрос на корректировку БД
        if decision == 'брак':
            update_query = f"""UPDATE shift_task SET otk_decision = '{controlman_id}',
                        st_status = '{decision}',
                        decision_time = '{datetime.datetime.now()}',
                        is_fail = 'True',
                        datetime_fail = '{datetime.datetime.now()}',
                        fio_failer = 
                        (SELECT fio_doer FROM shift_task WHERE id='{st_id}'),
                        job_duration = job_duration + ('{datetime.datetime.now()}' - datetime_job_resume)                                                      
                        WHERE id='{st_id}'"""
        else:
            update_query = f"""UPDATE shift_task SET otk_decision = '{controlman_id}',
                            st_status = '{decision}',
                            decision_time = '{datetime.datetime.now()}',
                            job_duration = job_duration + ('{datetime.datetime.now()}' - datetime_job_resume)
                            WHERE id='{st_id}'"""
        try:
            with con.cursor() as cur:
                cur.execute(update_query)
                con.commit()
        except Exception as e:
            logger.error(f'Ошибка при обновлении данных БД при решении контролёра decision_data_set '
                         f'{controlman_id=}, {decision=}, {st_id=}')
            logger.exception(e)
    except Exception as e:
        logger.error(f'Ошибка подключения к БД при обновлении данных БД при решении контролёра decision_data_set '
                     f'{controlman_id=}, {decision=}, {st_id=}')
        logger.exception(e)
    finally:
        con.close()


def indexes_calculation(st_id):
    """
    НЕ ИСПОЛЬЗУЕТСЯ для будущей имплементации
    Получение данных из БД и расчёт необходимых показателей
    :param st_id: если = *, то выборка будет по всем записям
    :return:
    """
    results = dict()
    try:
        # подключение к БД
        con = psycopg2.connect(dbname=dbname, user=user, password=password, host=host)
        con.autocommit = True
        if st_id == '*':
            select_query = f"""SELECT * FROM shift_task"""  # получение всех данных
        else:
            select_query = f"""SELECT * FROM shift_task WHERE id='{st_id}'"""  # получение данных по id записи
        try:
            with con.cursor() as cur:
                cur.execute(select_query)
                con.commit()
                # print(cur.fetchall())
                # назначение переменных
                for line in cur.fetchall():
                    results['id'] = line[0]
                    results['workshop'] = line[1]
                    results['model_name'] = line[2]
                    results['datetime_done'] = line[3]
                    results['op_number'] = line[4]
                    results['op_name_full'] = line[7]
                    results['ws_number'] = line[8]
                    results['norm_tech'] = line[9]
                    results['order'] = line[12]
                    results['datetime_job_start'] = line[16]
                    results['decision_time'] = line[23]
        except Exception as e:
            logger.error(f'Ошибка выборке при получении данных из БД для расчёта показателей indexes_calculation '
                         f'{st_id}')
            logger.exception(e)
    except Exception as e:
        logger.error(f'Ошибка подключение к БД при получении данных из БД для расчёта показателей indexes_calculation '
                     f'{st_id}')
        logger.exception(e)
    finally:
        con.close()


def all_active_st_get(status: str = 'ожидание контролёра') -> str:
    """
    Получение списка всех активных СЗ со статусом status
    :return:
    """
    try:
        # подключение к БД
        con = psycopg2.connect(dbname=dbname, user=user, password=password, host=host)
        con.autocommit = True
        # запрос на корректировку БД
        select_query = f"""SELECT * FROM shift_task WHERE st_status='{status}'"""
        try:
            with con.cursor() as cur:
                cur.execute(select_query)
                con.commit()
                st_list = cur.fetchall()
        except Exception as e:
            logger.error(f'Ошибка в выборке СЗ со статусом {status} all_active_st_get.')
            logger.exception(e)
    except Exception as e:
        logger.error(f'Ошибка подключения к БД при выборке СЗ со статусом {status} all_active_st_get.')
        logger.exception(e)
    finally:
        con.close()
    result_string = 'Сменные задания ожидающие приёмки:\n'
    for st in st_list:
        result_string += f'СЗ: №{st[0]}, ТЕРМИНАЛ: {st[10]}, Изделие: {st[5]}, Операция: {st[6]} {st[7]}\n'
    return result_string

# TODO ЗАКОНСЕРВИРОВАНО Функционал простоев
# def confirm_downtime(shift_task_number, master_fio, description) -> None:
#     """
#     Подтверждение простоя
#     """
#     try:
#         # подключение к БД
#         con = psycopg2.connect(dbname=dbname, user=user, password=password, host=host)
#         con.autocommit = True
#         update_query = f""" UPDATE shift_task
#                             SET st_status = 'простой',
#                                 job_duration = job_duration + ('{datetime.datetime.now()}' - datetime_job_resume)
#                             WHERE id='{shift_task_number}';
#
#                             UPDATE downtime
#                             SET status = 'подтверждено',
#                                 description = '{description}',
#                                 datetime_start = '{datetime.datetime.now()}',
#                                 datetime_decision = '{datetime.datetime.now()}',
#                                 master_decision_fio = '{master_fio}'
#                             WHERE shift_task_id = '{shift_task_number}'
#                         """
#         try:
#             with con.cursor() as cur:
#                 cur.execute(update_query)
#                 con.commit()
#         except Exception as e:
#             print(e, 'ошибка выборке')
#     except Exception as e:
#         print('Ошибка подключения к базе', e)
#     finally:
#         con.close()
#
#
# def reject_downtime(shift_task_number, master_fio, description) -> None:
#     """
#     Отклонение простоя
#     """
#     try:
#         # подключение к БД
#         con = psycopg2.connect(dbname=dbname, user=user, password=password, host=host)
#         con.autocommit = True
#         update_query = f""" UPDATE downtime
#                             SET status = 'отклонено',
#                                 description = '{description}',
#                                 datetime_decision = '{datetime.datetime.now()}',
#                                 master_decision_fio = '{master_fio}'
#                             WHERE shift_task_id = '{shift_task_number}'
#                         """
#         try:
#             with con.cursor() as cur:
#                 cur.execute(update_query)
#                 con.commit()
#         except Exception as e:
#             print(e, 'ошибка выборке')
#     except Exception as e:
#         print('Ошибка подключения к базе', e)
#     finally:
#         con.close()


if __name__ == '__main__':
    # select_master_call("13")
    # ws_list_get('')
    # status_change_to_otk('109', 123)
    # st_list_get('109')
    # print(st_list_get('109')[0][2:5], len(st_list_get('109')[0][2:5]))
    # master_id_get(st_id='275')
    # master_id_get(ws_number='109')
    # decision_data_set('264', '123', '!!!!!')
    # indexes_calculation('274')
    # fio_file = r'D:\АСУП\Python\Projects\ARC\GUI\Табель\База ФИО.xlsx'
    # status_change_to_otk('13', '1238658905')
    # doers_update(fio_file)
    master_id_get(ws_number=None, st_id='14912')
    # master_id_get(ws_number='11', st_id=None)

    # print(all_active_st_get())
    pass

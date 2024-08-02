"""
Функции получения контекстов
"""
import datetime
import json
import time
from decimal import Decimal, ROUND_CEILING, ROUND_HALF_EVEN, ROUND_FLOOR
from operator import itemgetter
from pathlib import Path
from pprint import pprint

from scheduler.models import WorkshopSchedule, ShiftTask, Doers, ModelParameters  # noqa
from m_logger_settings import logger  # noqa
from scheduler.services.initial_data_set import series_parameters_set, clean_model_names, models_data_db_set  # noqa
from django.db.models import Q
from .schedule_handlers import get_done_rate_with_td, get_done_rate


# def get_strat_plan_context():
#     """
#     Получение контекста для strat_plan ПЕРВАЯ ВЕРСИЯ
#     :return:
#     """
#     # Первоначальные заполнения данных
#     # series_parameters_set()  # заполнение первоначальных данных для моделей параметров серии
#     # json_file_to_save_tst = r'D:\АСУП\Python\Projects\OmzitTerminal\misc\all_weights.json'
#     # with open(json_file_to_save_tst, 'r') as file:
#     #     model_data = json.load(file)
#     # existing_models = clean_model_names(model_data)
#     # # первоначальное заполнение данных серий и моделей
#     # models_data_db_set(existing_models)
#
#     # TODO!
#     #  сохранить данные графика производства для контекста
#     #  передать первоначальный контекст
#     #  расчёты по смещение по оси времени, скорректировать контекст
#     #  вернуть контекст, перезаписать
#     #  рабочее место технолога
#     # исходный контекст
#     context = {
#         "tasks": [],
#         "canAdd": True,
#         "canWrite": True,
#         "canWriteOnParent": True,
#         "zoom": "1Q",
#         "selectedRow": 1,
#         "deletedTaskIds": [],
#         "resources": [
#             {
#                 "id": "tmp_1",
#                 "name": "Resource 1"
#             },
#             {
#                 "id": "tmp_2",
#                 "name": "Resource 2"
#             },
#             {
#                 "id": "tmp_3",
#                 "name": "Resource 3"
#             },
#             {
#                 "id": "tmp_4",
#                 "name": "Resource 4"
#             }
#         ],
#         "roles": [
#             {
#                 "id": "tmp_1",
#                 "name": "Project Manager"
#             },
#             {
#                 "id": "tmp_2",
#                 "name": "Worker"
#             },
#             {
#                 "id": "tmp_3",
#                 "name": "Stakeholder"
#             },
#             {
#                 "id": "tmp_4",
#                 "name": "Customer"
#             }
#         ],
#     }
#     planned_models = []
#     # запрос на получение запланированных моделей
#     plan = (WorkshopSchedule.objects.filter(
#         Q(order_status='запланировано')
#         | Q(order_status='в работе')
#     ).distinct()
#             .exclude(model_order_query__contains='TRUBOPROVOD')
#             .exclude(datetime_done=None)
#             ).values()
#     today = datetime.datetime.now()
#     # заполнение параметров моделей
#     dates = []
#
#     for model in plan:
#         model_parameters = ModelParameters.objects.filter(model_name=model['model_name']).values()
#         # заполнение только моделями на которые есть данные
#         if model_parameters and model['datetime_done']:
#             plan_datetime = (datetime.datetime.combine(model['datetime_done'],
#                                                        datetime.datetime.min.time())
#                              + datetime.timedelta(days=30 * 7))  # отступ в днях TODO ТЕСТЫ!!!
#             dates.append(plan_datetime)
#             # цикл изделия
#             model_prod_cycle = int(model_parameters[0]['produce_cycle'].quantize(Decimal('1'),
#                                                                                  ROUND_CEILING))
#             # определение процента готовности с учётом трудоёмкости
#             done_rate = get_done_rate_with_td(td=model_parameters[0]['full_norm_tech'],
#                                               model_order=model['model_order_query']
#                                               )
#             # дата начала производства
#             # TODO * 1000 для результирующего context
#             date_start = int((plan_datetime - datetime.timedelta(days=model_prod_cycle)).timestamp())
#             # потребляемая трудоёмкость в день для изделия
#             required_td = model_parameters[0]['day_hours_amount']
#             # коэффициент срочности для первоначальной сортировки (приоритет)
#             ordering = (plan_datetime - today).days / model_prod_cycle
#             # обновление списка данных
#
#             planned_models.append({
#                 'id': model['id'],
#                 'ordering': ordering,
#                 'model_name': model['model_name'],
#                 'datetime_done': model['datetime_done'],
#                 'model_order_query': model['model_order_query'],
#                 'done_rate': done_rate,
#                 'date_start': date_start,
#                 'model_prod_cycle': model_prod_cycle,
#                 'required_td': required_td,
#                 'plan_datetime': plan_datetime
#             })
#     # сортировка по коэффициенту срочности
#     sorted_planned_models = sorted(planned_models, key=itemgetter('ordering'))[:30]
#     # интервал дат оп графику
#     start_date_range = datetime.datetime.now()
#     end_date_range = max(dates)  # сама поздняя дата из графика
#     daterange = [(start_date_range + datetime.timedelta(days=x)) for x in
#                  range(0, (end_date_range - start_date_range).days)]
#     completed_models = []
#     planned_models = []
#     # сдвиг по отсортированному списку
#     day_capacity = 200
#     for current_date in daterange:
#         required_td_list = []
#         for model in sorted_planned_models:
#             if model['model_order_query'] not in completed_models:
#                 # список трудоёмкостей за дату
#                 required_td_list.append(model['required_td'])
#                 # сохранение дат начала, которые уже прошли
#                 if datetime.datetime.fromtimestamp(model['date_start']) >= current_date:
#                     # если ещё не в работе, то сегодня
#                     new_date_start = {'date_start': current_date.timestamp()}
#                     model.update(new_date_start)
#
#                 # новая дата готовности
#                 model_done_date = (datetime.datetime.fromtimestamp(model['date_start'])
#                                    + datetime.timedelta(days=model['model_prod_cycle']))
#
#                 if sum(required_td_list) < day_capacity and model_done_date < current_date:
#                     # добавляем в список готовых
#                     completed_models.append(model['model_order_query'])
#                     # planned_models.remove(model['model_order_query'])
#                 elif sum(required_td_list) >= day_capacity:
#                     # меняем дату
#                     new_date_start = {'date_start': current_date.timestamp()}
#                     # new_date_start = {'date_start': (current_date + datetime.timedelta(days=100)).timestamp()}
#                     model.update(new_date_start)
#                 elif sum(required_td_list) < day_capacity:
#                     # добавляем в список запланированных
#                     pass
#                     # model_done_date = (datetime.datetime.fromtimestamp(model['date_start'])
#                     #                    + datetime.timedelta(days=model['model_prod_cycle']))
#                     # planned_models.append(model['model_order_query'])
#
#     for model in sorted_planned_models:
#         # результирующий контекст
#         context["tasks"].append({'id': model['id'],
#                                  'name': model['model_name'],
#                                  'progress': model['done_rate'],
#                                  'progressByWorklog': False,
#                                  'relevance': 0,
#                                  'type': '',
#                                  'typeId': '',
#                                  'description': '',
#                                  'code': model['model_order_query'],
#                                  'level': 0,
#                                  'status': 'STATUS_ACTIVE',
#                                  'depends': '',
#                                  'end': '',
#                                  'start': model['date_start'] * 1000,
#                                  'duration': model['model_prod_cycle'],
#                                  'startIsMilestone': False,
#                                  'endIsMilestone': False,
#                                  'collapsed': False,
#                                  'canWrite': True,
#                                  'canAdd': True,
#                                  'canDelete': True,
#                                  'canAddIssue': True,
#                                  'assigs': [],
#                                  'earlyStart': '',
#                                  'earlyFinish': '',
#                                  'latestStart': '',
#                                  'latestFinish': '',
#                                  "criticalCost": '',
#                                  "isCritical": False,
#                                  'hasChild': False,
#                                  }
#                                 )
#
#     # pprint(context)
#     # json_file = Path(r'C:\Users\user-18\Desktop\json_chk.json')
#     # with open(json_file, 'w') as js_file:
#     #     json.dump(context, js_file, indent=2)
#
#     # параметры запланированных моделей
#
#     # for planned_model in planned_models:
#     #     if planned_model in short_existing_models:
#     #         print(f'Совпадание моделей {planned_model}')
#     #
#     #     else:
#     #         print(f'НЕСовпадание моделей {planned_model}')
#
#     # for plan_model in planned_models:
#     #     if existing_model == plan_model:
#     #         print(f'Совпадание моделей {plan_model}-{existing_model}')
#
#     # pprint(planned_models)
#
#     #  заполнение данных для моделей параметров моделей изделия
#
#     return context


def NEW_get_strat_plan_context(workshop: int) -> dict:
    """
    Получение контекста для strat_plan ПЕРВАЯ ВЕРСИЯ
    :return:
    """

    # Первоначальные заполнения данных
    # series_parameters_set()  # заполнение первоначальных данных для моделей параметров серии
    # json_file_to_save_tst = r'D:\АСУП\Python\Projects\OmzitTerminal\misc\all_weights.json'
    # with open(json_file_to_save_tst, 'r') as file:
    #     model_data = json.load(file)
    # existing_models = clean_model_names(model_data)
    # # первоначальное заполнение данных серий и моделей
    # models_data_db_set(existing_models)

    # исходный контекст
    context = {
        'workshop': workshop,
        "tasks": [],
        "canAdd": True,
        "canWrite": True,
        "canWriteOnParent": True,
        "zoom": "1Q",
        "selectedRow": 1,
        "deletedTaskIds": [],
        "resources": [
            {
                "id": "tmp_1",
                "name": "Resource 1"
            },
            {
                "id": "tmp_2",
                "name": "Resource 2"
            },
            {
                "id": "tmp_3",
                "name": "Resource 3"
            },
            {
                "id": "tmp_4",
                "name": "Resource 4"
            }
        ],
        "roles": [
            {
                "id": "tmp_1",
                "name": "Project Manager"
            },
            {
                "id": "tmp_2",
                "name": "Worker"
            },
            {
                "id": "tmp_3",
                "name": "Stakeholder"
            },
            {
                "id": "tmp_4",
                "name": "Customer"
            }
        ],
    }
    _planned_models = []
    # запрос на получение запланированных моделей
    plan = (WorkshopSchedule.objects.filter(
        Q(order_status='запланировано')
        | Q(order_status='в работе')
        | Q(order_status='не запланировано')
    )
            .filter(workshop=workshop)
            .distinct()
            ).values()
    today = datetime.datetime.now()
    # заполнение параметров моделей
    dates = []

    for model in plan:
        banned_models = ('TRUBOPROVOD', 'PAROPEREGREVATEL', 'SHIBER', 'shiber')
        md_name: str = model['model_name']
        mod_ord: str = model['model_order_query']
        if 'SV' in md_name:
            md_name = md_name[:md_name.find('-')]
            # print(model['model_order_query'])
        for ban in banned_models:
            if ban in mod_ord:
                md_name = 'unknown'
        # model_parameters = ModelParameters.objects.filter(model_name=model['model_name']).values()
        model_parameters = ModelParameters.objects.filter(model_name=md_name).values()
        # заполнение только моделями на которые есть данные
        plan_datetime = datetime.datetime.combine(model['calculated_datetime_done'], datetime.datetime.min.time())
        if model_parameters and plan_datetime:

            # TODO ТЕСТЫ!!! отступ в днях !УДАЛИТЬ ПОСЛЕ!
            # plan_datetime = plan_datetime + datetime.timedelta(days=30 * 3)

            dates.append(plan_datetime)
            # цикл изделия
            model_prod_cycle = int(model_parameters[0]['produce_cycle'].quantize(Decimal('1'),
                                                                                 ROUND_HALF_EVEN))
            # model_prod_cycle = float(model_parameters[0]['produce_cycle'])
            # определение процента готовности с учётом трудоёмкости
            done_rate = get_done_rate_with_td(td=model_parameters[0]['full_norm_tech'],
                                              model_order=model['model_order_query']
                                              )
            # выбор процента наибольшего процента готовности
            if done_rate < model['done_rate']:
                done_rate = model['done_rate']
            # дата начала производства
            # TODO * 1000 для результирующего context
            date_start = (plan_datetime - datetime.timedelta(days=model_prod_cycle)).timestamp()
            # потребляемая трудоёмкость в день для изделия
            required_td = model_parameters[0]['day_hours_amount']
            # коэффициент срочности для первоначальной сортировки (приоритет)
            ordering = (plan_datetime - today).days / model_prod_cycle
            # обновление списка данных

            _planned_models.append({
                'id': model['id'],
                'ordering': ordering,
                'model_name': model['model_name'],
                # 'datetime_done': datetime.datetime.combine(model['datetime_done'], datetime.datetime.min.time()),
                # 'datetime_done': plan_datetime,
                'datetime_done': model['datetime_done'],
                'model_order_query': model['model_order_query'],
                'done_rate': float(done_rate),
                'date_start': date_start,
                'model_prod_cycle': model_prod_cycle,
                'required_td': required_td,
                'plan_datetime': plan_datetime,
                'status': 'STATUS_ACTIVE',
                'order': model['order'],
                'contract_start_date': model['contract_start_date'],
                'contract_end_date': model['contract_end_date'],
                'is_fixed': model['is_fixed']
            })
        else:
            # Отображение всех заказов независимо от наличия параметров
            plan_datetime = datetime.datetime.combine(model['calculated_datetime_done'], datetime.datetime.min.time())
            # model_prod_cycle = int(model['produce_cycle'].quantize(Decimal('1'), ROUND_HALF_EVEN))
            model_prod_cycle = float(model['produce_cycle'])
            done_rate = float(model['done_rate'])
            ordering = (plan_datetime - today).days / model_prod_cycle

            date_start = (plan_datetime - datetime.timedelta(days=model_prod_cycle)).timestamp()

            _planned_models.append({
                'id': model['id'],
                'ordering': ordering,
                'model_name': model['model_name'],
                # 'datetime_done': datetime.datetime.combine(model['datetime_done'], datetime.datetime.min.time()),
                # 'datetime_done': plan_datetime,
                'datetime_done': model['datetime_done'],
                'model_order_query': model['model_order_query'],
                'done_rate': done_rate,
                # 'date_start': plan_datetime.timestamp(),
                'date_start': date_start,
                'model_prod_cycle': model_prod_cycle,
                'required_td': 20,
                'plan_datetime': plan_datetime,
                'status': 'STATUS_ACTIVE',
                'order': model['order'],
                'contract_start_date': model['contract_start_date'],
                'contract_end_date': model['contract_end_date'],
                'is_fixed': model['is_fixed']
            })

    # сортировка по коэффициенту срочности
    # sorted_planned_models = sorted(planned_models, key=itemgetter('ordering'))[:30]
    sorted_planned_models = sorted(_planned_models, key=itemgetter('ordering'))

    # интервал дат оп графику
    start_date_range = datetime.datetime.now()
    end_date_range = max(dates)  # сама поздняя дата из графика
    daterange = [(start_date_range + datetime.timedelta(days=x)).timestamp() for x in
                 range(0, (end_date_range - start_date_range).days + 300)]
    if workshop == 1:
        max_day_capacity = 180  # максимальная трудоёмкость в день
    elif workshop == 2:
        max_day_capacity = 290
    completed_models = set()  # готовые
    planned_models = set()  # запланированные
    today_timestamp = datetime.datetime.now().timestamp()

    for current_timestamp in daterange:
        used_td = []
        for index, model in enumerate(sorted_planned_models):
            # обработка зафиксированных (если зафиксировано, то сразу в запланированные)
            if model['is_fixed']:
                # used_td.append(model['required_td'])
                planned_models.add(model['model_order_query'])
                model['model_done_date'] = model['date_start'] + model['model_prod_cycle'] * 86400
                # model['date_start'] = model['date_start'] + 86400
            if model['model_order_query'] not in completed_models:
                used_td.append(model['required_td'])
                sum_used_td = sum(used_td)
                # отображение прошлого со статусами
                if model['date_start'] < current_timestamp:
                    planned_models.add(model['model_order_query'])
                    model['model_done_date'] = model['date_start'] + model['model_prod_cycle'] * 86400
                    # статус отставание
                    if (model['date_start'] + model['model_prod_cycle'] * 86400 * (model['done_rate'] / 100)
                            < today_timestamp - 86400):
                        model['status'] = 'STATUS_SUSPENDED'
                    # статус провал
                    if model['model_done_date'] < today_timestamp:
                        model['status'] = 'STATUS_FAILED'
                else:
                    # статус ожидания (присваивается если запуск не ранее чем через 30 дней)
                    if model['date_start'] > today_timestamp + 10 * 86400:
                        model['status'] = 'STATUS_WAITING'
                # если не запланировано
                if model['model_order_query'] not in planned_models:
                    if sum_used_td < max_day_capacity:  # трудоёмкость есть
                        # планируем
                        planned_models.add(model['model_order_query'])
                        model['date_start'] = current_timestamp
                        model['model_done_date'] = model['date_start'] + model['model_prod_cycle'] * 86400
                    else:  # иначе трудоёмкости нет
                        # смещение
                        model['date_start'] = current_timestamp + 86400
                else:  # иначе запланировано
                    if current_timestamp >= model['model_done_date']:  # срок готовности подошел
                        completed_models.add(model['model_order_query'])  # в готовые
                        # planned_models.remove(model['model_order_query'])

    for model in sorted_planned_models:
        # for model in update_production_schedule(sorted_planned_models, 200):
        # результирующий контекст
        if model['contract_start_date']:
            contract_start_date = datetime.datetime.combine(model['contract_start_date'],
                                                            datetime.datetime.min.time()).timestamp() * 1000,
            contract_start_date_str = model['contract_start_date'].strftime('%d.%m.%Y')
        else:
            contract_start_date = None
            contract_start_date_str = ''
        if model['contract_end_date']:
            contract_end_date = datetime.datetime.combine(model['contract_end_date'],
                                                          datetime.datetime.min.time()).timestamp() * 1000,
            contract_end_date_str = model['contract_end_date'].strftime('%d.%m.%Y')
        else:
            contract_end_date = None
            contract_end_date_str = ''


        # print(f'{model["date_start"] * 1000=}')
        # print(f'{model["model_order_query"]=}')

        context["tasks"].append({'id': model['id'],
                                 'name': model['model_name'],
                                 'progress': int(model['done_rate']),
                                 'progressByWorklog': False,
                                 'relevance': 0,
                                 'type': '',
                                 'typeId': '',
                                 'description': model['datetime_done'].strftime('%d.%m.%Y'),
                                 'code': model['order'],
                                 'level': 0,
                                 'status': model['status'],
                                 'depends': '',
                                 'end': '',
                                 'start': model['date_start'] * 1000,
                                 'duration': model['model_prod_cycle'],
                                 'startIsMilestone': False,
                                 'endIsMilestone': False,
                                 'collapsed': False,
                                 'canWrite': True,
                                 'canAdd': True,
                                 'canDelete': True,
                                 'canAddIssue': True,
                                 'assigs': [],
                                 'earlyStart': '',
                                 'earlyFinish': '',
                                 'latestStart': '',
                                 'latestFinish': '',
                                 "criticalCost": '',
                                 "isCritical": False,
                                 'hasChild': False,
                                 'model_order_query': model['model_order_query'],
                                 # datetime.datetime.combine(model['calculated_datetime_done'],
                                 #                           datetime.datetime.min.time())
                                 'contract_start_date': contract_start_date,
                                 'contract_end_date': contract_end_date,
                                 'contract_start_date_str': str(contract_start_date_str),
                                 'contract_end_date_str': str(contract_end_date_str),
                                 'is_fixed': model['is_fixed']
                                 }
                                )
    return context


if __name__ == '__main__':
    pass
    # get_strat_plan_context()

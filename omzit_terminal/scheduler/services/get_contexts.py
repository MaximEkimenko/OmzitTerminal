"""
Функции получения контекстов
"""
import datetime
import json
from decimal import Decimal, ROUND_CEILING
from operator import itemgetter
from pathlib import Path
from pprint import pprint

from scheduler.models import WorkshopSchedule, ShiftTask, Doers, ModelParameters  # noqa
from m_logger_settings import logger  # noqa
from scheduler.services.initial_data_set import series_parameters_set, clean_model_names, models_data_db_set  # noqa
from django.db.models import Q
from .schedule_handlers import get_done_rate_with_td, get_done_rate


def get_strat_plan_context():
    """
    Получение контекста для strat_plan
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

    # TODO!
    #  сохранить данные графика производства для контекста
    #  передать первоначальный контекст
    #  расчёты по смещение по оси времени, скорректировать контекст
    #  вернуть контекст, перезаписать
    #  рабочее место технолога
    # исходный контекст
    context = {
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
    planned_models = []
    # запрос на получение запланированных моделей
    plan = (WorkshopSchedule.objects.filter(
        Q(order_status='запланировано')
        | Q(order_status='в работе')
    ).distinct()
            .exclude(model_order_query__contains='TRUBOPROVOD')
            .exclude(datetime_done=None)
            ).values()
    today = datetime.datetime.now()
    # заполнение параметров моделей
    dates = []
    for model in plan:
        model_parameters = ModelParameters.objects.filter(model_name=model['model_name']).values()
        # заполнение только моделями на которые есть данные
        if model_parameters and model['datetime_done']:
            plan_datetime = (datetime.datetime.combine(model['datetime_done'],
                                                       datetime.datetime.min.time())
                             + datetime.timedelta(days=30 * 7))  # отступ в днях TODO ТЕСТЫ!!!
            dates.append(plan_datetime)
            # цикл изделия
            model_prod_cycle = int(model_parameters[0]['produce_cycle'].quantize(Decimal('1'),
                                                                                 ROUND_CEILING))
            # определение процента готовности с учётом трудоёмкости
            done_rate = get_done_rate_with_td(td=model_parameters[0]['full_norm_tech'],
                                              model_order=model['model_order_query']
                                              )
            # дата начала производства
            # TODO * 1000 для результирующего context
            date_start = int((plan_datetime - datetime.timedelta(days=model_prod_cycle)).timestamp())
            # потребляемая трудоёмкость в день для изделия
            required_td = model_parameters[0]['day_hours_amount']
            # коэффициент срочности для первоначальной сортировки (приоритет)
            ordering = (plan_datetime - today).days / model_prod_cycle
            # обновление списка данных

            planned_models.append({
                'id': model['id'],
                'ordering': ordering,
                'model_name': model['model_name'],
                'datetime_done': model['datetime_done'],
                'model_order_query': model['model_order_query'],
                'done_rate': done_rate,
                'date_start': date_start,
                'model_prod_cycle': model_prod_cycle,
                'required_td': required_td,
                'plan_datetime': plan_datetime
            })
    # сортировка по коэффициенту срочности
    sorted_planned_models = sorted(planned_models, key=itemgetter('ordering'))
    # интервал дат оп графику
    start_date_range = datetime.datetime.now()
    end_date_range = max(dates)  # сама поздняя дата из графика
    daterange = [(start_date_range + datetime.timedelta(days=x)) for x in
                 range(0, (end_date_range - start_date_range).days)]
    # сдвиг по отсортированному списку
    day_capacity = 200
    for current_date in daterange:
        required_td_list = []
        models_in_date = []
        for model in sorted_planned_models:
            print(model['model_order_query'])
            # создание списка моделей в дате
            # model_done_date = model['plan_datetime'] + datetime.timedelta(days=model['model_prod_cycle'])
            # сохранение дат начала, которые уже прошли
            if datetime.datetime.fromtimestamp(model['date_start']) >= current_date:
                new_date_start = {'date_start': current_date.timestamp()}
            else:
                new_date_start = {'date_start': model['date_start']}
            model.update(new_date_start)

            model_done_date = current_date + datetime.timedelta(days=model['model_prod_cycle'])
            required_td_list.append(model['required_td'])

            if sum(required_td_list) <= day_capacity:
                continue
                # models_in_date.append(model)
            elif sum(required_td_list) > day_capacity:
                new_date_start = {'date_start': current_date.timestamp()}
                model.update(new_date_start)


            # elif model in models_in_date:
            #     models_in_date.remove(model)
            #     print('removed', model)

        # if model not in models_in_date:
        #     new_date_start = {'date_start': (current_date + datetime.timedelta(days=1)).timestamp()}
        #     model.update(new_date_start)

        # if new_date_start:

            # model.update({'date_start': model_done_date.timestamp() * 1000})
            # if (model['date_start'] + datetime.timedelta(days=model['model_prod_cycle'])).timestamp() <= current_date.timestamp():
            #     pass
    #         #
            # # добавление новой модели в график
        # print(len(models_in_date))

            #
            #
            #
            #

        # проход по списку моделей в интервале, сравнение с
        # day_capacity = 200
        # required_td_list.append(model['required_td'])
        # if sum(required_td_list) <= day_capacity and current_date.timestamp() < model['date_start']:
        #     model.update({'date_start': current_date.timestamp() * 1000})
        # else:
        #     model.update({'date_start': current_date + datetime.timedelta(days=1)})



    for model in sorted_planned_models:


        # результирующий контекст
        context["tasks"].append({'id': model['id'],
                                 'name': model['model_name'],
                                 'progress': model['done_rate'],
                                 'progressByWorklog': False,
                                 'relevance': 0,
                                 'type': '',
                                 'typeId': '',
                                 'description': '',
                                 'code': model['model_order_query'],
                                 'level': 0,
                                 'status': 'STATUS_ACTIVE',
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
                                 }
                                )

    # pprint(context)
    # json_file = Path(r'C:\Users\user-18\Desktop\json_chk.json')
    # with open(json_file, 'w') as js_file:
    #     json.dump(context, js_file, indent=2)

    # параметры запланированных моделей

    # for planned_model in planned_models:
    #     if planned_model in short_existing_models:
    #         print(f'Совпадание моделей {planned_model}')
    #
    #     else:
    #         print(f'НЕСовпадание моделей {planned_model}')

    # for plan_model in planned_models:
    #     if existing_model == plan_model:
    #         print(f'Совпадание моделей {plan_model}-{existing_model}')

    # pprint(planned_models)

    #  заполнение данных для моделей параметров моделей изделия

    example_context = {'canAdd': True,
                       'canWrite': True,
                       'canWriteOnParent': True,
                       'deletedTaskIds': [],
                       'resources': [{'id': 'tmp_1', 'name': 'Resource 1'},
                                     {'id': 'tmp_2', 'name': 'Resource 2'},
                                     {'id': 'tmp_3', 'name': 'Resource 3'},
                                     {'id': 'tmp_4', 'name': 'Resource 4'}],
                       'roles': [{'id': 'tmp_1', 'name': 'Project Manager'},
                                 {'id': 'tmp_2', 'name': 'Worker'},
                                 {'id': 'tmp_3', 'name': 'Stakeholder'},
                                 {'id': 'tmp_4', 'name': 'Customer'}],
                       'selectedRow': 8,
                       'tasks': [{'assigs': [],
                                  'canAdd': True,
                                  'canAddIssue': True,
                                  'canDelete': True,
                                  'canWrite': True,
                                  'code': '',
                                  'collapsed': False,
                                  'depends': '',
                                  'description': '',
                                  'duration': 184,
                                  'end': 1734631199999,
                                  'endIsMilestone': False,
                                  'hasChild': True,
                                  'id': -1,
                                  'level': 0,
                                  'name': 'Цех 2',
                                  'progress': 0,
                                  'progressByWorklog': False,
                                  'relevance': 0,
                                  'start': 1712512800000,
                                  'startIsMilestone': False,
                                  'status': 'STATUS_ACTIVE',
                                  'type': '',
                                  'typeId': ''},
                                 {'assigs': [],
                                  'canAdd': True,
                                  'canAddIssue': True,
                                  'canDelete': True,
                                  'canWrite': True,
                                  'code': '125(40)\\1916',
                                  'collapsed': False,
                                  'criticalCost': 39,
                                  'depends': '',
                                  'description': '',
                                  'duration': 39,
                                  'earlyFinish': 39,
                                  'earlyStart': 0,
                                  'end': 1717091999999,
                                  'endIsMilestone': False,
                                  'id': 'tmp_1716968006135',
                                  'isCritical': False,
                                  'latestFinish': 83,
                                  'latestStart': 44,
                                  'level': 1,
                                  'name': '5000M',
                                  'progress': 100,
                                  'progressByWorklog': False,
                                  'relevance': 0,
                                  'start': 1712512800000,
                                  'startIsMilestone': False,
                                  'status': 'STATUS_DONE',
                                  'type': '',
                                  'typeId': ''}]},
    return context


if __name__ == '__main__':
    get_strat_plan_context()

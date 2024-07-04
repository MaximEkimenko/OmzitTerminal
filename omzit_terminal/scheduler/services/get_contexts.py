"""
Функции получения контекстов
"""
import datetime
import json
from decimal import Decimal, ROUND_CEILING
from pathlib import Path
from pprint import pprint

from scheduler.models import WorkshopSchedule, ShiftTask, Doers, ModelParameters  # noqa
from m_logger_settings import logger  # noqa
from scheduler.services.initial_data_set import series_parameters_set, clean_model_names, models_data_db_set  # noqa
from django.db.models import Q


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
    # первоначальное заполнение данных серий и моделей
    # models_data_db_set(existing_models)

    # TODO!
    #  сохранить данные графика производства для контекста
    #  передать первоначальный контекст
    #  расчёты по смещение по оси времени, скорректировать контекст
    #  вернуть контекст, перезаписать
    #  рабочее место технолога
    # запланированное

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
    plan = WorkshopSchedule.objects.filter(
        Q(order_status='запланировано')
        | Q(order_status='в работе'))
    for model in plan:
        planned_models.append({
            'id': model.id,
            'model_name': model.model_name.split('-')[0],
            'datetime_done': model.datetime_done})

    # context["tasks"].append({'id': -1,
    #                          })
    for model in planned_models:
        model_parameters = ModelParameters.objects.filter(model_name=model['model_name']).values()
        if model_parameters:
            plan_datetime = datetime.datetime.combine(model['datetime_done'],
                                                      datetime.datetime.min.time())
            model_prod_cycle = int(model_parameters[0]['produce_cycle'].quantize(Decimal('1'),
                                                                                 ROUND_CEILING))
            # model_prod_cycle = datetime.timedelta(days=
            #                                       float(model_parameters[0]['produce_cycle'].quantize(Decimal('1'),
            #                                                                                           ROUND_CEILING))
            #                                       )

            # print (   datetime.date.fromtimestamp(int(plan_datetime.timestamp())))

            context["tasks"].append({'id': model['id'],
                                     'name': model_parameters[0]['model_name'],
                                     'progress': 0,
                                     'progressByWorklog': False,
                                     'relevance': 0,
                                     'type': '',
                                     'typeId': '',
                                     'description': '',
                                     'code': '',
                                     'level': 0,
                                     'status': 'STATUS_ACTIVE',
                                     'depends': '',

                                     # 'start': int(plan_datetime.timestamp()) * 1000,
                                     # 'end': int(plan_datetime.timestamp()) * 1000,
                                     'end': '',
                                     'start': int((plan_datetime -
                                                   datetime.timedelta(days=model_prod_cycle)).timestamp()) * 1000,
                                     'duration': model_prod_cycle,


                                     # 'end': int((plan_datetime +
                                     #             datetime.timedelta(days=model_prod_cycle)).timestamp()) * 1000,

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
                                     })

            # context['tasks'].append()
        else:
            print('we go zero here!')
    # pprint(context)
    json_file = Path(r'C:\Users\user-18\Desktop\json_chk.json')
    with open(json_file, 'w') as js_file:
        json.dump(context, js_file, indent=2)

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


if __name__ == '__main__':
    get_strat_plan_context()

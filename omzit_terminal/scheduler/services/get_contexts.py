"""
Функции получения контекстов
"""
import json
from pprint import pprint

from scheduler.models import WorkshopSchedule, ShiftTask, Doers, ModelParameters # noqa
from m_logger_settings import logger # noqa
from scheduler.services.initial_data_set import series_parameters_set, clean_model_names, models_data_db_set # noqa
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
    planned_models = []
    plan = WorkshopSchedule.objects.filter(
            Q(order_status='запланировано')
            | Q(order_status='в работе'))
    for model in plan:

        planned_models.append(model.model_name.split('-')[0])

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




    example_context = {'assigs': [],
                       'canAdd': True,
                       'canAddIssue': True,
                       'canDelete': True,
                       'canWrite': True,
                       'code': '',
                       'collapsed': False,
                       'criticalCost': 36,
                       'depends': '185',
                       'description': '',
                       'duration': 4,
                       'earlyFinish': 12,
                       'earlyStart': 8,
                       'end': 1718992799999,
                       'endIsMilestone': False,
                       'id': 'tmp_1717128101514',
                       'isCritical': False,
                       'latestFinish': 51,
                       'latestStart': 47,
                       'level': 2,
                       'name': '30',
                       'progress': 0,
                       'progressByWorklog': False,
                       'relevance': 0,
                       'start': 1718647200000,
                       'startIsMilestone': False,
                       'status': 'STATUS_SUSPENDED',
                       'type': '',
                       'typeId': ''},


if __name__ == '__main__':
    get_strat_plan_context()
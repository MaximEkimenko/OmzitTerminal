"""
Функции получения контекстов
"""
from scheduler.models import WorkshopSchedule, ShiftTask, Doers, ModelParameters # noqa
from m_logger_settings import logger # noqa
from scheduler.services.initial_data_set import series_parameters_set # noqa


def get_strat_plan_context():
    """
    Получение контекста для strat_plan
    :return:
    """
    series_parameters_set()  # заполнение первоначальных данных для моделей параметров серии
    # TODO!
    #  запрос в график производства - найти решения однозначного определения серии по model_order_query
    #  заполнить параметры модели с параметрами серии из графика производства
    #  сохранить данные графика производства для контекста
    #  передать первоначальный контекст
    #  расчёты по смещение по оси времени, скорректировать контекст
    #  вернуть контекст, перезаписать
    #  рабочее место технолога



    #  заполнение данных для моделей параметров моделей изделия


    # params = ModelParameters(
    #     model_name='test_name',
    #     model_weight=3000,
    #     full_norm_tech=560,
    #     # critical_chain_cycle_koef = 0.6,
    #     cycle_polynom_koef=[],
    #     # difficulty_koef=1,
    # )
    # params.save()

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
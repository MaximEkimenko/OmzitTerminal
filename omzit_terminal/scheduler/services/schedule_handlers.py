import os

from ..models import WorkshopSchedule, ShiftTask
import matplotlib.pyplot as plt
import matplotlib
from omzit_terminal.settings import BASE_DIR
from omzit_terminal.settings import STATIC_ROOT


def get_done_rate(order_number: str) -> float:
    """
    Получение процента готовности заказа
    :param order_number: номер заказа
    :return:
    """
    # метод расчёта по количеству принятых сменных заданий
    # TODO реализовать альтернативный метод расчёта по выполненной трудоёмкости.
    all_st = ShiftTask.objects.filter(order=order_number).count()
    done_st = ShiftTask.objects.filter(order=order_number, st_status='принято').count()
    try:
        done_rate = round(100 * (all_st - (all_st - done_st))/all_st, 2)
    except ZeroDivisionError:
        done_rate = 0
    return done_rate


def get_all_done_rate() -> None:
    """
    Получение процента готовности всех заказов, обновление записей done_rate в БД
    :return: None
    """
    order_rate_dict = dict()  # TODO удалить при рефакторинге
    all_orders = WorkshopSchedule.objects.values('order').distinct()
    for dict_order in all_orders:
        order = dict_order['order']
        done_rate = get_done_rate(order)
        order_rate_dict[order] = done_rate
        # установка статуса в зависимости от процента готовности
        if done_rate == float(0):
            order_status = None
        elif done_rate == float(100):
            order_status = 'выполнено'
        else:
            order_status = 'в работе'
        # запись в БД
        if order_status:
            WorkshopSchedule.objects.filter(order=order).update(done_rate=done_rate, order_status=order_status)
    # print(order_rate_dict)


def make_workshop_plan_plot(workshop, days_list, fact_list, aver_fact):
    """
    Функция для построения инфографики работы цеха
    :param workshop: цех
    :param days_list: список дней
    :param fact_list: список % фактического выполнения плана цехом по дням
    :param aver_fact: среднее значение факта
    :return:
    """
    matplotlib.use('agg')  # отключение интерактивного режима
    hundred_list = [100] * len(fact_list)
    aver_list = [aver_fact] * len(fact_list)
    plt.figure(figsize=(20, 10))  # размер графика
    plt.xlabel('Дата')
    plt.ylabel('% выполнения')
    plt.title(f"График выполнения плана цеха № {workshop}", fontsize=20)
    plt.yticks(range(0, 300, 10), fontsize=12)  # деления оси y
    fact_color = 'red' if aver_fact < 100 else 'green'  # цвет линии факта

    plt.plot(days_list, fact_list, lw=1, color='blue', alpha=1, marker='o', markersize=2)  # факт
    plt.plot(days_list, aver_list, lw=3, color=fact_color, alpha=1)  # факт средняя
    plt.plot(days_list, hundred_list, lw=3, color='black', alpha=1)  # 100%
    plt.grid(ls=':')  # сетка графика
    plt.legend(('Кривая выполнения плана', fr'Факт на {days_list[len(days_list)-1]} - '
                                           fr'{round(aver_fact, 2)}%', '100%'), loc=3)  # легенда

    # сохранение
    filename = rf'scheduler\static\scheduler\jpg\plan{workshop}-{days_list[0][-2:]}.jpg'
    filename_2 = rf'O:\Расчет эффективности\отчёты цехов\plan{workshop}-{days_list[0][-2:]}.jpg'
    filepath = os.path.join(BASE_DIR, filename)
    plt.savefig(fname=filepath,   orientation='landscape', bbox_inches='tight', transparent=True)
    # копия в расчёт эффективности
    plt.savefig(fname=filename_2, orientation='landscape', bbox_inches='tight', transparent=True)
    # plt.show()








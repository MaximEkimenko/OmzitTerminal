from datetime import datetime
from orders.utils.ppr import create_current_month_ppr_orders, create_next_month_ppr_orders
from orders.utils.workers_process import clear_all_dayworkers

# День, когда надо создавать заявки ППР на следующий месяц
CREATE_NEXT_MONTH_PPR_DAY = 27
# тестовое значение
#CREATE_NEXT_MONTH_PPR_DAY = 27

def suspend_orders_end_of_day():
    """
    Снимает работников со всех активных заявок в конце рабочего дня
    """
    clear_all_dayworkers()


def create_ppr_at_first_run():
    """
    Пр первом запуске приложения создает ППР на весть текущий месяц, начиная с сегодняшнего дня.
    А заодно и на следуюший месяц, если первый запуск происходит в конце месяца
    @return:
    """
    create_current_month_ppr_orders()
    # если сегодня день позже, чем день для создания заявок ППР
    # на следующий день, то создаем заявки на следующий месяц
    if datetime.now().day > CREATE_NEXT_MONTH_PPR_DAY:
        create_next_month_ppr_orders()


def create_ppr_for_next_month():
    """
    Создаёт заявки на ППР на следующий месяц
    """
    create_next_month_ppr_orders()

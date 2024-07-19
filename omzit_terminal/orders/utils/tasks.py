from datetime import datetime
from orders.utils.ppr import create_current_month_ppr_orders, create_next_month_ppr_orders
from orders.utils.workers_process import clear_all_dayworkers

# День, когда надо создавать заявки ППР на следующий месяц
# CREATE_NEXT_MONTH_PPR_DAY = 27

# тестовое значение
CREATE_NEXT_MONTH_PPR_DAY = 15

def suspend_orders_end_of_day():
    """
    Снимает работников со всех активных заявок в конце рабочего дня
    """
    clear_all_dayworkers()


def create_ppr_at_first_run():
    create_current_month_ppr_orders()
    # если сегодня день позже, чем день для создания заявок ППР
    # на следующий день, то создаем заявки на следующий месяц
    if datetime.now().day > CREATE_NEXT_MONTH_PPR_DAY:
        create_next_month_ppr_orders()


def create_ppr_for_next_month():
    create_next_month_ppr_orders()

def test_job_1():
    print(f'выполнилась тестовая задача {datetime.now()}')

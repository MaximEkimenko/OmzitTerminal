from datetime import datetime
from django.utils import timezone
from django.db.models import F
from orders.models import OrdersWorkers, Orders
from orders.utils.common import OrdStatus
from orders.utils.ppr import create_current_month_ppr_orders, create_next_month_ppr_orders

CREATE_NEXT_MONTH_PPR_DAY = 27


def clear_all_dayworkers():
    active_workers = OrdersWorkers.objects.filter(end_date__isnull=True).all()
    if active_workers:
        active_workers.update(end_date=timezone.now())
    Orders.objects.filter(status__in=[OrdStatus.START_REPAIR, OrdStatus.REPAIRING]).update(
        status=OrdStatus.SUSPENDED, previous_status=F("status")
    )


def create_ppr_at_first_run():
    create_current_month_ppr_orders()
    # если сегодня день позже, чем день для создания заявок ППР
    # на следующий день, то создаем заявки на следующий месяц
    if datetime.now().day > CREATE_NEXT_MONTH_PPR_DAY:
        create_next_month_ppr_orders()


def create_ppr_for_next_month():
    create_next_month_ppr_orders()

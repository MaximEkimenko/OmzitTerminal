from django.db.models import F
from django.utils import timezone

from orders.models import OrdersWorkers, Orders
from orders.utils.common import OrdStatus
from orders.utils.utils import remove_dayworkers_from_order


def clear_all_dayworkers():
    """
    Снимает со всех заданий работников.
    Должна вызвать ся по таймеру в конце рабочего дня.
    """
    active_workers = OrdersWorkers.objects.filter(end_date__isnull=True).all()
    if active_workers:
        active_workers.update(end_date=timezone.now())
    Orders.objects.filter(status__in=[OrdStatus.START_REPAIR, OrdStatus.REPAIRING]).update(
        status=OrdStatus.SUSPENDED, previous_status=F("status")
    )


def clear_all_string_dayworkers():
    """
    Снимает со всех заданий работников.
    Должна вызвать ся по таймеру в конце рабочего дня.
    """
    orders_with_workers = Orders.objects.exclude(dayworkers_string__isnull=True).all()
    for order in orders_with_workers:
        remove_dayworkers_from_order(order)

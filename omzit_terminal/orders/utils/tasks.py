from datetime import datetime
from django.utils import timezone
from django.db.models import F
from orders.models import OrdersWorkers, Orders
from orders.utils.common import OrdStatus


def clear_all_dayworkers():
    active_workers = OrdersWorkers.objects.filter(end_date__isnull=True).all()
    if active_workers:
        active_workers.update(end_date=timezone.now())
    Orders.objects.filter(status__in=[OrdStatus.START_REPAIR, OrdStatus.REPAIRING]).update(
        status=OrdStatus.SUSPENDED, previous_status=F("status")
    )

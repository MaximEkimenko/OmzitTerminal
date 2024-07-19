from datetime import datetime
from m_logger_settings import logger
from orders.models import Orders
from orders.utils.common import OrdStatus
from orders.utils.utils import remove_dayworkers_from_order, clear_dayworkers


def clear_all_dayworkers():
    """
    Снимает со всех заданий работников.
    Должна вызвать ся по таймеру в конце рабочего дня.
    """
    active_orders = Orders.objects.exclude(dayworkers_string__isnull=True).all()
    if active_orders:
        for order in active_orders:
            clear_dayworkers(order)
    logger.info(f"Удаление ремонтников со всех заявок в конце рабочего дня {datetime.now()}")


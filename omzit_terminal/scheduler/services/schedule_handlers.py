from ..models import WorkshopSchedule, ShiftTask


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








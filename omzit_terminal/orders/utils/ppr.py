import calendar
from datetime import date, datetime, timedelta

from django.utils.timezone import make_aware

from orders.models import Orders, Equipment


def create_current_month_ppr_orders():
    """
    Создает заявки ППР от сегодняшнего числа до конца месяца.
    Функция должна запускаться по расписанию - при запуске приложения и срабатывать один раз.
    Нужна, чтобы при первом запуске приложения заявки ППР на текущий месяц создавались,
    если они отсутствуют.
    """
    today = date.today()
    max_day = calendar.monthrange(today.year, today.month)[1]
    last_day = date(today.year, today.month, max_day)
    ppr_orders_count = (
        Orders.fresh_orders()
        .filter(breakdown_date__gt=today, breakdown_date__lte=last_day)
        .filter(is_ppr=True)
        .count()
    )
    print("количество заявок в этом месяце:", ppr_orders_count)
    # создаем заявки на ППР
    ppr_equipment = (
        Equipment.objects.filter(ppr_plan_day__gte=today.day).order_by("ppr_plan_day").all()
    )
    if ppr_orders_count == 0:
        for equip in ppr_equipment:
            br_date = datetime(today.year, today.month, equip.ppr_plan_day, 8)
            new_ppr_order = Orders(
                is_ppr=True,
                equipment=equip,
                breakdown_description="Плановый ремонт",
                breakdown_date=make_aware(br_date),
                identified_employee="Создано автоматически",
            )
            new_ppr_order.save()


def create_next_month_ppr_orders():
    """
    Создает заявки ППР на следующий месяц по всему оборудованию, у которого имеется дата ППР.
    Должна запускаться по расписанию ориентировочно 27 числа каждого месяца.
    """
    today = date.today()
    # номер следующего месяца
    next_month_number = today.month + 1 if today.month + 1 < 13 else 1
    next_month_length = calendar.monthrange(today.year, next_month_number)[1]
    # дата через месяц от сегодняшнего дня, для точного определения номера месяца и года в следующем месяце
    next_month: date = today + timedelta(days=next_month_length)

    # проверяем, что в следующем месяце нет заявок ППР
    # Если их нет, значит надо создавать
    # Если заявок на следующий месяц >0, значит задание уже отработало
    first_day_of_next_month = date(next_month.year, next_month.month, 1)
    next_month_orders_count = (
        Orders.fresh_orders()
        .filter(breakdown_date__gte=first_day_of_next_month, is_ppr=True)
        .count()
    )
    print("количество заявок в следующем месяце:", next_month_orders_count)
    if next_month_orders_count == 0:
        # Создаем заявки на ППР.
        # Получаем список оборудования, у которого проставлена дата ПРР и проходимся по нему,
        # создавая на каждое оборудование заявку.
        ppr_equipment = Equipment.objects.exclude(ppr_plan_day__isnull=True).order_by(
            "ppr_plan_day"
        )
        for equip in ppr_equipment:
            # для каждого оборудования создаем свою дату заявки на основе дня ППР
            br_date = datetime(next_month.year, next_month.month, equip.ppr_plan_day, 8)
            new_ppr_order = Orders(
                is_ppr=True,
                equipment=equip,
                breakdown_description="Плановый ремонт",
                breakdown_date=make_aware(br_date),
                identified_employee="Создано автоматически",
            )
            new_ppr_order.save()

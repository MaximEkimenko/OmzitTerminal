from datetime import date, datetime
from typing import Any

from django import forms
from django.db.models import QuerySet
from django.utils.timezone import make_naive, make_aware

from m_logger_settings import logger
from scheduler.filters import get_filterset
from orders.utils.common import OrdStatus, button_context
from orders.utils.roles import Position, get_employee_position
from orders.forms import AddOrderForm

from orders.models import FlashMessage, Orders, OrderStatus, Materials


def get_order_verbose_names():
    verbose_names = dict()
    for field in Orders._meta.get_fields():
        if hasattr(field, "verbose_name"):
            verbose_names[field.name] = field.verbose_name
        else:
            verbose_names[field.name] = field.name
    return verbose_names


def create_flash_message(name: str):
    FlashMessage.objects.create(name=name)


def pop_flash_messages() -> list[str]:
    fm = FlashMessage.objects.all()
    l = []
    for m in fm:
        l.append(m.name)
    FlashMessage.objects.all().delete()
    return l


def get_table_data(q: QuerySet) -> dict[str, Any]:
    header = {
        "row_number": "№",
        "name": "имя",
        "inv_number": "инвентарный номер",
        "category__name": "категория",
    }
    td = []
    for rec in q:
        row = []
        for key in header:
            row.append(rec[key])
        td.append(row)
    return {"header": list(header.values()), "data": td}


def orders_record_to_dict(record: Orders, fields: list[str]) -> dict[str, Any]:
    """
    Преобразует запись в таблице Orders в словарь
    """
    res = {}
    complex_keys = ["equipment", "status", "materials"]
    for key in fields:
        if key in complex_keys:
            temp_obj = getattr(record, key)
            if temp_obj:
                res[key] = temp_obj.name
            else:
                res[key] = None

        else:
            res[key] = getattr(record, key)
            try:
                res[key] = make_naive(res[key])
                res[key] = res[key].strftime("%d.%m.%Y %H:%M")
            except Exception:
                pass

    return res


def orders_to_dict(model: QuerySet) -> list[dict[str, Any]]:
    """
    Преобразует QuerySet в список словарей. Каждый словарь, это строка таблицы,
    а ключ словаря указывает на конкретную ячейку в строке.
    """

    def get_table_fields() -> list[str]:
        """
        Возвращает список имен полей таблицы
        """
        fields = []
        for i in Orders._meta._get_fields():
            fields.append(i.name)
        return fields

    fields = get_table_fields()  # получаем имена полей таблицы
    table_dict = []
    for rec in model:
        rec_dict = orders_record_to_dict(rec, fields)
        table_dict.append(rec_dict)
    return table_dict


def get_doers_list(form: forms.Form) -> list[str]:
    fios = list(
        filter(
            lambda x: x != "None",
            (str(form.cleaned_data[f"fio_{i}"]) for i in range(1, 4)),
        )
    )
    return fios


def convert_name(doers: list[str]) -> str:
    doers_fio = []
    for e in doers:
        f = e.split(" ")
        new_name = " ".join([f[part][0] + "." if part > 0 else f[part] for part in range(len(f))])
        doers_fio.append(new_name)
    return ", ".join(sorted(doers_fio))


def orders_get_context(request) -> dict[str, Any]:
    cols = [
        "id",
        "equipment_id",
        "equipment__unique_name",
        "status",
        "status__name",
        "priority",
        "breakdown_date",
        "breakdown_description",
        "identified_employee",
        "inspection_date",
        "expected_repair_date",
        "materials__name",
        "repair_date",
        "acceptance_date",
        "accepted_employee",
        "doers_fio",
        "materials_request",
        "revision_cause",
    ]

    order_table_data = (
        Orders.objects.exclude(acceptance_date__lt=date.today())
        .all()
        .prefetch_related("equipment", "status", "materials")
        .values(*cols)
    )
    equipment_filter = get_filterset(data=request.GET, queryset=order_table_data, fields=cols)

    context = {
        "create_order": [Position.Admin, Position.HoS],  # добавить заявку
        "role": get_employee_position(request.user.username),
        "order_filter": equipment_filter,
        "status": OrdStatus,
        "add_order_form": AddOrderForm(),
        "alerts": pop_flash_messages(),
        "button_context": button_context,
    }

    return context


def get_order_edit_context(request) -> dict[str, Any]:
    employees = {
        "worker": [Position.Admin, Position.HoS],
        "breakdown_description": [Position.Admin, Position.HoS],
        "expected_repair_date": [Position.Admin, Position.HoRT, Position.Repairman],
        "materials": [Position.Admin, Position.HoRT, Position.Repairman],
        "extra_materials": [Position.Admin, Position.HoRT, Position.Repairman],
        "materials_request": [Position.Admin, Position.Dispatcher],
        "breakdown_cause": [Position.Admin, Position.HoRT, Position.Repairman],
        "solution": [Position.Admin, Position.HoRT, Position.Repairman],
    }

    stages = {
        "worker": [
            OrdStatus.DETECTED,
            OrdStatus.START_REPAIR,
            OrdStatus.WAIT_FOR_MATERIALS,
            OrdStatus.REPAIRING,
            OrdStatus.REPAIRING,
        ],
        "breakdown_description": [
            OrdStatus.DETECTED,
            OrdStatus.START_REPAIR,
            OrdStatus.WAIT_FOR_MATERIALS,
            OrdStatus.REPAIRING,
        ],
        "expected_repair_date": [
            OrdStatus.START_REPAIR,
            OrdStatus.WAIT_FOR_MATERIALS,
            OrdStatus.REPAIRING,
        ],
        "materials": [
            OrdStatus.START_REPAIR,
            OrdStatus.WAIT_FOR_MATERIALS,
        ],
        "extra_materials": [
            OrdStatus.START_REPAIR,
            OrdStatus.WAIT_FOR_MATERIALS,
        ],
        "materials_request": [OrdStatus.WAIT_FOR_MATERIALS, OrdStatus.REPAIRING],
        "breakdown_cause": [OrdStatus.REPAIRING, OrdStatus.FIXED],
        "solution": [OrdStatus.REPAIRING, OrdStatus.FIXED],
    }
    return {
        "stages": stages,
        "employees": employees,
        "role": get_employee_position(request.user.username),
    }


def process_repair_expect_date(d: date) -> datetime:
    md = datetime.combine(d, datetime.max.time())
    return make_aware(md)


def apply_order_status(order: Orders, status: OrdStatus) -> None:
    flag = False
    stat = OrderStatus.objects.get(pk=status)
    try:
        order.status = stat
        order.save()
        flag = True
        logger.info(f"Заявка № {order.id} переведена в статус {stat}")
    except Exception as e:
        logger.error(f"Ошибка при переходе заявки № {order.id} в статус {stat}")
        logger.error(e)
    return flag


def create_extra_materials(exma: str) -> Materials | None:
    try:
        m = Materials.objects.filter(name=exma).first()
        if m is None:
            m = Materials.objects.create(name=exma)
            alert_message = "Добавлены новые материалы"
            create_flash_message(alert_message)
            logger.info(f"Созданы новые материалы для ремонта {exma}")

    except Exception as e:
        alert_message = "Ошибка при выборе материалов"
        create_flash_message(alert_message)
        logger.error(f"Ошибка при выборе или удалении материалов {exma}")
        logger.exception(e)
        m = None
    return m

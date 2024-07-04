from datetime import date, datetime
from typing import Any
import json
from django import forms
from django.contrib.postgres.aggregates import StringAgg
from django.db import models
from django.db.models import QuerySet, OuterRef, Subquery
from django.utils import timezone
from django.utils.timezone import make_naive, make_aware

from m_logger_settings import logger
from scheduler.filters import get_filterset
from orders.utils.common import OrdStatus, button_context
from orders.utils.roles import Position, get_employee_position
from orders.forms import AddOrderForm

from orders.models import (
    FlashMessage,
    Orders,
    OrderStatus,
    Materials,
    Equipment,
    Repairmen,
    OrdersWorkers,
)


def get_order_verbose_names() -> dict[str, str]:
    """
    Возвращает словарь подписей к полям таблицы заявок на ремонт (Orders)
    Ключ: название поля (имя переменной, ссылающейся на поле)
    Значение: русское название поля, взятое из атрибута verbose_names поля

    """
    verbose_names = dict()
    for field in Orders._meta.get_fields():
        # не обрабатываем поле многие-ко-многим, потому что в форме его автоматом вывести нельзя
        # print(field.name, type(field))
        # if not type(field) in [models.ManyToManyField, models.ManyToManyRel, models.ManyToOneRel]:
        if True:
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


def get_doers_list(form: forms.Form) -> list[Repairmen]:
    """
    Возвращает список работников (объектов Repairmen) при начале ремонта
    """
    fios = list(
        filter(
            lambda x: x is not None,
            (form.cleaned_data[f"fio_{i}"] for i in range(1, 4)),
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
    """
    Добавляет в контекст для представления orders следующую информацию:
    create_order: каким группам пользователей позволено создавать заявку, нужно для появления
        на странице кнопки "создать заявку"
    role: к какой группе принадлежит пользователь (для формирования кнопок этапов ремонта)
    order_filter: объект для фильтрации заявок по значениям в столбцах таблицы
    add_order_form: форма создания новой заявки на ремонт
    alerts: всплывающие сообщения о действиях пользователя
    button_context: список, но основе которого происходит формирование кнопок
    """
    #
    cols = [
        "id",
        "equipment_id",
        "equipment__unique_name",
        "status",
        "status__name",
        "priority",
        "breakdown_date",
        "breakdown_description",
        "expected_repair_date",
        "materials__name",
        "materials_request",
        "revision_cause",
    ]

    cols_extended = [
        "id",
        "equipment_id",
        "equipment__unique_name",
        "status",
        "status__name",
        "previous_status__name",
        "priority",
        "breakdown_date",
        "breakdown_description",
        "expected_repair_date",
        "materials__name",
        "dayworkers_fio",
        "materials_request",
        "revision_cause",
    ]

    assigned_workers_subquery = (
        Repairmen.assignable_workers.filter(
            orders=OuterRef("pk"), assignments__end_date__isnull=True
        )
        .values("orders")
        .annotate(assigned_workers_string=StringAgg("fio", delimiter=", ", ordering="fio"))
        .values("assigned_workers_string")
    )

    order_table_data = (
        Orders.objects.exclude(acceptance_date__lt=date.today())
        .all()
        .annotate(dayworkers_fio=Subquery(assigned_workers_subquery))
        .prefetch_related("equipment", "status", "materials")
        .values(*cols_extended)
    )
    orders_filter = get_filterset(data=request.GET, queryset=order_table_data, fields=cols)

    equipment_json = json.dumps(
        list(Equipment.objects.all().values("id", "unique_name", "shop_id"))
    )

    context = {
        "create_order": [Position.Admin, Position.HoS],  # добавить заявку
        "role": get_employee_position(request.user.username),
        "order_filter": orders_filter,
        "equipment_json": equipment_json,
        "add_order_form": AddOrderForm(),
        "alerts": pop_flash_messages(),
        "button_context": button_context,
    }

    return context


def get_order_edit_context(request) -> dict[str, Any]:
    """
    Возвращает условия, когда и какому пользователю можно редактировать отдельные поля карточки заявки на ремонт.
    """
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
    """
    Выбирает дату окончания ремонта, но поле должно содержать и время. На тот случай,
    если задача занимает час или два. Теоретически должна быть возможность определять
    срок выполнения задачи с точностью до минуты.
    Так что в данной функции к дате прибавляется время сразу перед началом следующего
    дня и возвращается datetime.
    """
    md = datetime.combine(d, datetime.max.time())
    return make_aware(md)


def apply_order_status(order: Orders, status: OrdStatus) -> bool:
    """
    Переводит заявку в статус, переданный в параметре, сохраняет объект заявки и
    записывает в лог результат данной опреации.
    """
    flag = False
    stat = OrderStatus.objects.get(pk=status)
    try:
        order.previous_status = order.status
        order.status = stat
        order.save()
        flag = True
        logger.info(f"Заявка № {order.id} переведена в статус {stat}")
    except Exception as e:
        logger.error(f"Ошибка при переходе заявки № {order.id} в статус {stat}")
        logger.error(e)
    return flag


def create_extra_materials(exma: str) -> Materials | None:
    """
    Принимает введенную вручную строку с требуемыми для ремонта материалами.
    Если такая строка уже есть, просто возвращает объект материалов.
    Если нет, то создает его и возвращает.
    """
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


def check_order_resume(order: Orders):
    """
    Если заявка находится в статусе "приостановлено", а предыдущий статус: "ремонт начат" или "в ремонте"
    и у нее имеется активный исполнитель, то заявка возвращается к предыдущему статусу
    """
    if (
        order.active_workers_count() > 0
        and order.status_id == OrdStatus.SUSPENDED
        and order.previous_status_id
        in (
            OrdStatus.START_REPAIR,
            OrdStatus.REPAIRING,
        )
    ):
        apply_order_status(order, order.previous_status_id)


def check_order_suspend(order: Orders):
    """
    Если заявка находится в статусе "ремонт начат" или "в ремонте" и на нее не назначено
    ни одного исполнителя (например, в конце рабочего дня все исполнители автоматически
    сняты), то заявка переходит в статус "приостановлено"
    """
    if order.active_workers_count() == 0 and order.status_id in (
        OrdStatus.START_REPAIR,
        OrdStatus.REPAIRING,
    ):
        apply_order_status(order, OrdStatus.SUSPENDED)


def clear_dayworkers(order: Orders):
    """
    Снимаем всех сотрудников с заявки, а дальше она, в зависимости от статуса, может перейти
    в состояние "приостановлено"
    """
    active_workers = OrdersWorkers.objects.filter(order=order, end_date__isnull=True).all()
    if active_workers:
        active_workers.update(end_date=timezone.now())
        check_order_suspend(order)


ORDER_CARD_COLUMNS = (
    "equipment",
    "status",
    "priority",
    "dayworkers_fio",
    "materials",
    "materials_request",
    "material_request_file",
    "breakdown_date",
    "breakdown_description",
    "worker",
    "expected_repair_date",
    "breakdown_cause",
    "solution",
    "identified_employee",
    "inspection_date",
    "inspected_employee",
    "clarify_date",
    "repair_date",
    "repaired_employee",
    "acceptance_date",
    "accepted_employee",
    "revision_date",
    "revision_cause",
    "revised_employee",
    "cancel_cause",
    "materials_request",
    "materials_request_date",
    "material_dispatcher",
    "confirm_materials_date",
    "supply_request",
    "supply_request_date",
)

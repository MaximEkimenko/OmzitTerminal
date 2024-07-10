from enum import Enum
from dataclasses import dataclass, field
from orders.utils.roles import Position

# максимальное количество работников, которое может быть одновременно приписано к одному ремонту
MAX_DAYWORKERS_PER_ORDER = 4
# если материалы не требуются, то пропускаем этап "требуются материалы" и сразу переходим к ремонту
# сравниваем со строкой из выпадающего списка требуемых материалов
MATERIALS_NOT_REQUIRED = "материалы не требуются"


def forDjango(cls):
    """Позволяет передавать перечисление в шаблон и там обращаться к его полям через точку"""
    cls.do_not_call_in_templates = True
    return cls


@forDjango
class OrdStatus(int, Enum):
    """Перечисление этапов ремонта"""

    DETECTED = 1  # требует ремонта
    START_REPAIR = 2  # ремонт начался, но еще не определились с материалами и сроками
    WAIT_FOR_MATERIALS = 3  # ждем подтверждения материалов
    WAIT_FOR_ACT = 4  # ожидание акта
    REPAIRING = 5  # в ремонте
    FIXED = 6  # ремонт окончен
    ACCEPTED = 7  # ремонт принят
    CANCELLED = 8  # ремонт отменен
    UNREPAIRABLE = 9  # неремонтопригодно
    SUSPENDED = 10  # задача приостановлена (требует назначения новых сотрудников)


ALL_STATES = [i for i in OrdStatus]


class Button:
    """
    Объект описания кнопки, который отправляется в шаблон orders.
    На основе полей объекта на странице формируется кнопка.
    Изначально я хотел сделать кнопку через dataclass, но шаблоны django его не понимают.
    """

    def __init__(
        self,
        name: str,
        title: str,
        groups: list[Position],
        url: str = "",
        states: list[OrdStatus] = [],
    ):
        self.name = name
        self.title = title
        self.groups = groups
        self.url = url
        self.states = states


"""
Список, содержащий всю информацию по кнопкам, которыми управляется состояние заявки на ремонт, а именно:
- название кнопки
- эндпоинт, который обрабатывает нажатие кнопки
- состояние ремонта, на котором появляется кнопка
- группы, к которым должен принадлежать пользователь, чтобы для него эта кнопка появилась   
"""
button_context = [
    Button(
        name="start",
        title="начать ремонт",
        url="start_repair",
        states=[OrdStatus.DETECTED],
        groups=[Position.Admin, Position.HoRT, Position.Repairman],
    ),
    Button(
        name="clarify",
        title="уточнить детали ремонта",
        url="clarify_repair",
        states=[OrdStatus.START_REPAIR],
        groups=[Position.Admin, Position.HoRT, Position.Repairman],
    ),
    Button(
        name="commit",
        title="подтвердить наличие материалов",
        url="confirm_materials",
        states=[OrdStatus.WAIT_FOR_MATERIALS],
        groups=[Position.Admin, Position.Dispatcher],
    ),
    Button(
        name="finish",
        title="закончить ремонт",
        url="finish_repair",
        states=[OrdStatus.REPAIRING],
        groups=[Position.Admin, Position.HoRT, Position.Repairman],
    ),
    Button(
        name="accept",
        title="принять ремонт",
        url="accept_repair",
        states=[OrdStatus.FIXED],
        groups=[Position.Admin, Position.HoS],
    ),  # принять ремонт
    Button(
        name="revise",
        title="вернуть на доработку",
        url="revision_repair",
        states=[OrdStatus.FIXED],
        groups=[Position.Admin, Position.HoS],
    ),
    Button(
        name="cancel",
        title="отменить ремонт",
        url="cancel_repair",
        states=[
            OrdStatus.START_REPAIR,
            OrdStatus.START_REPAIR,
            OrdStatus.WAIT_FOR_MATERIALS,
            OrdStatus.REPAIRING,
            OrdStatus.FIXED,
        ],
        groups=[Position.Admin, Position.HoS],
    ),
    Button(
        name="delete",
        title="удалить заявку",
        url="delete_repair",
        states=[OrdStatus.DETECTED],
        groups=[Position.Admin, Position.HoS],
    ),
    Button(
        name="add_repairman",
        title="назначить исполнителей",
        url="start_repair",
        states=[OrdStatus.SUSPENDED],
        groups=[Position.Admin, Position.HoRT, Position.Repairman],
    ),
    Button(
        name="clear_repairman",
        title="снять всех исполнителей",
        url="clear_workers",
        states=[OrdStatus.START_REPAIR, OrdStatus.REPAIRING],
        groups=[Position.Admin],
    ),
]


def can_edit_workers(status_id, role):
    """
    Определяет, кто и когда может редактировать состав ремонтников, приписанных к заявке.
    Возвращает True или False. В зависимости от результата на странице рисуется кнопка для
    перехода на страницу редактирования ремонтников.
    """
    if role in [Position.Admin, Position.HoRT, Position.Repairman] and status_id in [
        OrdStatus.START_REPAIR,
        OrdStatus.WAIT_FOR_MATERIALS,
        OrdStatus.REPAIRING,
    ]:
        return True
    return False

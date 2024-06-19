from enum import Enum
from dataclasses import dataclass, field
from orders.utils.roles import Position


def forDjango(cls):
    """позволяет передавать перечисление в шаблон и там обращаться к его полям через точку"""
    cls.do_not_call_in_templates = True
    return cls


@forDjango
class OrdStatus(int, Enum):
    DETECTED = 1  # требует ремонта
    START_REPAIR = 2  # ремонт начался, но еще не определились с материалами и сроками
    WAIT_FOR_MATERIALS = 3  # ждем подтверждения материалов
    WAIT_FOR_ACT = 4  # ожидание акта
    REPAIRING = 5  # в ремонте
    FIXED = 6  # ремонт окончен
    ACCEPTED = 7  # ремонт принят
    CANCELLED = 8  # ремонт отменен
    UNPRPAIRABLE = 9  # неремонтопригодно


class Button:
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
]

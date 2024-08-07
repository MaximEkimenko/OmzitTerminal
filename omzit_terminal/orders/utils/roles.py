from enum import Enum
from typing import Literal
from collections import namedtuple
from django.core.exceptions import PermissionDenied

from m_logger_settings import logger


class Position(int, Enum):
    HoS = 1  # начальник цеха
    HoRT = 2  # начальник ремонтной бригады
    Engineer = 3
    Admin = 4
    Dispatcher = 5  # человек, подтверждающий наличие материалов для ремонта
    Worker = 6  # Работник. Может смотреть, но ни к каким кнопкам у него доступа нет
    Repairman = 7
    Controller = 8
    Technolog = 9


USER_GROUPS = {
    Position.Admin: ["admin", "admin2", "admin3",],
    Position.Engineer: ["engineer"],
    Position.HoS: ["chief_ceh", "chief_ceh2", "chief_ceh3"],
    Position.HoRT: ["chief_rep", "chief_rep2"],
    Position.Dispatcher: ["dispatcher", "dispatcher2"],
    Position.Worker: ["worker"],
    Position.Repairman: ["repair", "repair2", "repair3", "repair4"],
    Position.Controller: ["controler", "controler2", "controler3"],
    Position.Technolog: ["tehnolog", "tehnolog1", "tehnolog2"],
}

PERMITTED_USERS = []
for g in USER_GROUPS.values():
    PERMITTED_USERS.extend(g)


def get_employee_position(username):
    """
    Возвращает группу пользователя (его роль) на основе имени пользователя
    """
    for ug in USER_GROUPS:
        if username in USER_GROUPS[ug]:
            return ug
    return None


def custom_login_check(request) -> Literal[True]:
    """
    Проверяет, есть ли username в списке разрешенных пользователей PERMITTED_USERS.
    Если есть, продолжает работу, если нет - возбуждает исключение PermissionDenied,
    таким образом функция-представление не открывается для сторонних пользователей

    """
    username = request.user.username
    if username not in PERMITTED_USERS:
        logger.warning(f"Попытка доступа к рабочему месту диспетчера пользователем {username}")
        raise PermissionDenied
    return True

DropdownMenuItem = namedtuple("DropdownMenuItem", ["roles", "title", "link"])

menu_items = {
        "tehnolog": DropdownMenuItem(
        [Position.Technolog],
        "Технолог",
        "tehnolog"
    ),
    "orders": DropdownMenuItem(
        [Position.HoS, Position.HoRT, Position.Engineer, Position.Repairman, Position.Dispatcher, Position.Worker],
        "Заявки на ремонт",
        "orders",
        ),
    "equipment": DropdownMenuItem(
        [Position.HoS, Position.HoRT, Position.Engineer,Position.Repairman, Position.Dispatcher, Position.Worker],
        "Оборудование",
        "equipment"
    ),
    "controller": DropdownMenuItem(
        [Position.Controller, Position.Technolog, Position.HoS],
        "Акты о браке",
        "controller:index"
    ),
}


def get_menu_context(request) -> dict:
    return {
        "role": get_employee_position(request.user.username),
        "permitted_users": PERMITTED_USERS,
        "menu_items": menu_items
        }

from enum import Enum
from typing import Literal

from django.core.exceptions import PermissionDenied

from m_logger_settings import logger


class Position(int, Enum):
    HoS = 1  # начальник цеха
    HoRT = 2  # начальник ремонтной бригады
    Engineer = 3
    Admin = 4
    Dispatcher = 5  # человек, подтверждающий наличие материалов для ремонта


USER_GROUPS = {
    Position.Admin: [
        "admin",
        "admin2",
        "admin3",
    ],
    Position.Engineer: ["engineer"],
    Position.HoS: ["chief_ceh", "chief_ceh2"],
    Position.HoRT: ["chief_rep"],
    Position.Dispatcher: ["dispatcher", "dispatcher2"],
}
PERMITED_USERS = []
for g in USER_GROUPS.values():
    PERMITED_USERS.extend(g)


def get_employee_position(username):
    for ug in USER_GROUPS:
        if username in USER_GROUPS[ug]:
            return ug
    return None


def custom_login_check(request) -> Literal[True]:
    username = request.user.username
    if not any(map(lambda x: x == username, PERMITED_USERS)):
        logger.warning(
            f"Попытка доступа к рабочему месту диспетчера пользователем {request.user.username}"
        )
        raise PermissionDenied
    return True

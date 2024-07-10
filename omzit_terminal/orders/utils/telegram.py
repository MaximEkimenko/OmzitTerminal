import asyncio
from orders.models import Orders
from orders.utils.common import OrdStatus
from m_logger_settings import logger

from orders.telegram_token import orders_telegram_group_id, shop_chief_telegram_ids, TelegramID
from typing import Any, Callable

from worker.services.master_call_function import terminal_message_to_id


# если True, то не отправляет в телегу сообщения, просто печатает их в консоль
TELEGRAM_TEST = True

"""
Словарь содержит сообщения, которые нужно отправлять в телеграм-чаты при изменении статуса заявок,
а также функции, которе должны отправлять эти сообщения и идентификаторы чатов 
"""
telegram_handle_dict = {
    OrdStatus.DETECTED: {
        "message": "Создана заявка № {id} на ремонт оборудования '{equipment}' ({shop}) с приоритетом № {priority}.",
        "handlers": [{"func": "send_telegram_messages", "tids": [orders_telegram_group_id]}],
    },
    OrdStatus.START_REPAIR: {
        "message": "Начат ремонт оборудования '{equipment}' ({shop}) по заявке № {id}.",
        "handlers": [{"func": "send_telegram_messages", "tids": [orders_telegram_group_id]}],
    },
    OrdStatus.WAIT_FOR_MATERIALS: {
        "message": "Уточнены детали по ремонту  оборудования '{equipment}' ({shop}) по заявке № {id}.",
        "handlers": [{"func": "send_telegram_messages", "tids": [orders_telegram_group_id]}],
    },
    OrdStatus.WAIT_FOR_ACT: {
        "message": "не реализовано",
        "handlers": [{"func": "send_telegram_messages", "tids": [orders_telegram_group_id]}],
    },
    OrdStatus.REPAIRING: {
        "message": "Подтверждено наличие материалов по заявке № {id} на ремонт оборудования '{equipment}' ({shop}).",
        "handlers": [{"func": "send_telegram_messages", "tids": [orders_telegram_group_id]}],
    },
    OrdStatus.FIXED: {
        "message": "Ремонт  оборудования '{equipment}' ({shop}) по заявке № {id} закончен.",
        "handlers": [
            {"func": "send_telegram_messages", "tids": [orders_telegram_group_id]},
            {"func": "notify_shop_chiefs", "tids": shop_chief_telegram_ids},
        ],
    },
    OrdStatus.ACCEPTED: {
        "message": "Оборудование {equipment}' ({shop}) после ремонта по заявке № {id} принято в эксплуатацию.",
        "handlers": [{"func": "send_telegram_messages", "tids": [orders_telegram_group_id]}],
    },
    OrdStatus.CANCELLED: {
        "message": "Ремонт оборудования '{equipment}' ({shop}) по заявке № {id} отменен.",
        "handlers": [{"func": "send_telegram_messages", "tids": [orders_telegram_group_id]}],
    },
    OrdStatus.UNREPAIRABLE: {
        "message": "не реализовано",
        "handlers": [{"func": "fake_telegram_messages", "tids": [orders_telegram_group_id]}],
    },
    OrdStatus.SUSPENDED: {
        "message": "не реализовано",
        "handlers": [{"func": "fake_telegram_messages", "tids": [orders_telegram_group_id]}],
    },
}


def send_telegram_message(telegram_id: TelegramID, message: str, error_template: str) -> bool:
    result = False
    try:
        if TELEGRAM_TEST:
            print(telegram_id, "отправлено сообщение:")
            print(message)
        else:
            asyncio.run(terminal_message_to_id(to_id=telegram_id, text_message_to_id=message))
    except Exception as e:
        error = error_template + f"в чат {telegram_id}"
        logger.error(error)
        logger.exception(e)
    else:
        result = True
    return result


def send_telegram_messages(
    telegram_ids: list[TelegramID], message: str, error_template: str, params: dict[str, Any]
):
    for tid in telegram_ids:
        send_telegram_message(tid, message, error_template)


def fake_telegram_messages(*args, **kwargs):
    print(args)


def notify_shop_chiefs(
    chefs_dict: dict[str, list[TelegramID]],
    message: str,
    error_template: str,
    params: dict[str, Any],
):
    for shop_id in chefs_dict:
        if params["shop"] == shop_id:
            send_telegram_messages(chefs_dict[shop_id], message, error_template, params)
            break


def order_telegram_notification(
    status: OrdStatus, order: Orders, custom_message: None | str = None
) -> None:
    """
    Отправляет в телеграм сообщения о переходе заявки на новый этап.
    Запускает произвольное количество обработчиков сообщений, указанных в словаре telegram_handle_dict.
    Идентификаторы чатов указаны в том же словаре.
    А обработчики рассылают сообщения по разным чатам или группам.
    """
    format_dict = {
        "equipment": order.equipment.name,
        "shop": order.equipment.shop.name,
        "id": order.id,
        "priority": order.priority,
        "status": order.status.name,
    }
    if custom_message:
        message = custom_message.format(**format_dict)
    else:
        message = telegram_handle_dict[status]["message"].format(**format_dict)
    error_template = (
        "Ошибка отправки сообщения боту во время присвоения заявке № {id} статуса " "'{status}'"
    ).format(**format_dict)
    for handler in telegram_handle_dict[status]["handlers"]:
        func: Callable = globals()[handler["func"]]
        tids: list | dict = handler["tids"]
        func(tids, message, error_template, format_dict)

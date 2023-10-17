import os
from aiogram import Bot, Dispatcher
TOKEN = os.getenv('RSU_TOKEN')

bot = Bot(token=TOKEN)  # инициализация бота
dp = Dispatcher(bot)  # инициализация диспетчера
# ids
# admin_id = int(os.getenv('ADMIN_TELEGRAM_ID'))
# users = (admin_id,)  # админ
# masters = (admin_id,)  # мастера
# posohov_id = 2051721470  # цех 1
# ermishkin_id = 5221029965
# gordii_id = 6374431046
# kondratiev_id = 6125791135
# achmetov_id = 1153114403
# savchenko_id = 2131171377  # ПДО
# pavluchenkova_id = 1151694995
# dispatcher_list = (admin_id, savchenko_id, pavluchenkova_id,)  # диспетчеры
# master_list = (admin_id, ermishkin_id, posohov_id, gordii_id, kondratiev_id, achmetov_id)  # производство
# группа мастеров
omzit_master_group1_id = -4005524766


async def send_call_master(message_to_master):
    """
    Отправка сообщения в группу мастерам
    :param message_to_master:
    :return:
    """
    await bot.send_message(chat_id=omzit_master_group1_id, text=message_to_master)


async def send_call_dispatcher(message_to_master):
    await bot.send_message(chat_id=omzit_master_group1_id, text=message_to_master)


async def terminal_message_to_id(to_id, text_message_to_id):
    """
    Отправляет сообщение для id
    :param to_id: получатель
    :param text_message_to_id: текст сообщения
    :return:
    """
    await bot.send_message(chat_id=to_id, text=text_message_to_id)


def get_client_ip(request):
    """
    Получение IP из запроса
    :param request:
    :return:
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[-1].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

import os
from asyncio import sleep

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
omzit_master_group2_id = -4109421151


# omzit_master_group1_id = -4027358064


async def send_call_master(message_to_master, ws_number):
    """
    Отправка сообщения в группу мастерам
    :param message_to_master:
    :param ws_number: номер терминала
    :return:
    """
    ws_numbers_c1 = ('11', '12', '13', '14', '15', '16')
    ws_numbers_c2 = ('22', '23', '24', '25', '26', '27', '28', '29', '210', '211')
    print(ws_number)
    if str(ws_number) in ws_numbers_c1:
        await bot.send_message(chat_id=omzit_master_group1_id, text=message_to_master)
    elif str(ws_number) in ws_numbers_c2:
        await bot.send_message(chat_id=omzit_master_group2_id, text=message_to_master)
    else:
        print(f'Ошибка отправки сообщения мастеру в цехе №{ws_number}, {message_to_master}')


async def send_call_dispatcher(message_to_master, ws_number):
    """
    Отправка сообщения в группу мастерам для диспетчера
    :param message_to_master:
    :param ws_number: номер терминала
    :return:
    """
    # TODO сравнить с send_call_master и заменить на него если не понадобится разделять процессы мастера и диспетчера
    #  до обновления 5
    ws_numbers_c1 = ('11', '12', '13', '14', '15', '16')
    ws_numbers_c2 = ('22', '23', '24', '25', '26', '27', '28', '29', '210', '211')
    print(ws_number)
    if str(ws_number) in ws_numbers_c1:
        await bot.send_message(chat_id=omzit_master_group1_id, text=message_to_master)
    elif str(ws_number) in ws_numbers_c2:
        await bot.send_message(chat_id=omzit_master_group2_id, text=message_to_master)
    else:
        print(f'Ошибка отправки сообщения диспетчеру в цехе №{ws_number}, {message_to_master}')


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
    # TODO убрать HTTP_X_FORWARDED_FOR, если не понадобится до обновления 4
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[-1].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

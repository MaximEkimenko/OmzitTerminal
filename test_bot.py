import datetime
import logging
import os
import re
from aiogram import Bot, Dispatcher, executor, types, filters
# работа с БД
from terminal_db import (ws_list_get, status_change_to_otk, st_list_get, master_id_get, control_man_id_set,
                         decision_data_set)
logging.basicConfig(filename="log.log", level=logging.DEBUG, filemode='w',
                    format=' %(levelname)s - %(asctime)s; файл - %(filename)s; сообщение - %(message)s')
TOKEN = os.getenv('RSU_TOKEN')

admin_id = int(os.getenv('ADMIN_TELEGRAM_ID'))
users = (admin_id, )  # админ

masters = (admin_id, )

control_mans_list = (admin_id, )
# telegram ids
test_group_id = -908012934

bot = Bot(token=TOKEN)  # инициализация бота
dp = Dispatcher(bot)  # инициализация диспетчера

# шаблоны re для callback
pattern_call_otk = r'(call)\d\d\d'  # шаблон для вызова ОТК
pattern_answ_otk = r'(answ)\d\d\d'  # шаблон для ответа ОТК
pattern_dcgo_otk = r'(dcgo)\d\d\d'  # шаблон запуска решения
pattern_stid_otk = r'(stid)\d'  # шаблон для вызова вариантов решений ОТК
pattern_dscn_otk = r'(dcsn)\d'  # шаблон принятого решения ОТК


async def on_startup(_):  # функция выполняется при запуске бота
    # await bot.send_message(admin_id, "Бот РСУ вышел в онлайн.")
    print(f'ТЕСТ БОТ онлайн в {datetime.datetime.now().strftime("%H:%M:%S")}.')


async def send_call_master(message_to_master):
    """ Функция вызова мастера. Импортируется в terminal_listener"""
    await bot.send_message(chat_id=admin_id, text=message_to_master)

# TODO найти, повторить и разрешить баг с выбором последней записи в инлайн кнопке при нажатии на любую.


def call_get_re(pattern: str, call: str) -> str:  # TODO перенести в отдельный модуль
    """
    Функция получения строки из pattern re. Используется в lambda в call_back_handler вместо фильтра regexp
    :param pattern: шаблон re
    :param call: строка для проверки
    :return: string
    """
    try:
        result_string = re.match(pattern, call).string
    except Exception as e:
        result_string = ''
        print(e)

    return result_string


@dp.message_handler(commands=['start'])
async def start_rsu_bot(message: types.Message):
    await message.reply(text='')


@dp.message_handler(commands=['help'])
async def help_rsu_bot(message: types.Message):
    if message.from_user.id in users:
        await message.reply(text='')


# TODO docstring для всх обработчиков
# TODO разграничить права доступа
# ------------------------------------------------ Мастер вызывает контролёра
# отображение inline ws_number для мастера при вызове ОТК. Обработка команды otk_send
@dp.message_handler(commands=['otk_send'])
async def master_otk_send(message: types.Message):
    if message.from_user.id in masters:
        # создание inline keyboard РЦ со статусом ожидание мастера
        inline_ws_buttons = types.InlineKeyboardMarkup()  # объект
        ws_list = ws_list_get("ожидание мастера")
        for ws in ws_list:
            btn = types.InlineKeyboardButton(text=f'{ws}', callback_data=f'call{ws}{message.from_user.id}')
            inline_ws_buttons.insert(btn)
        await message.answer('Выбор РЦ', reply_markup=inline_ws_buttons)
    else:
        await message.reply('У вас нет доступа к этому функционалу.')


# обработчик callback otk_send вызова контролёра МАСТЕРОМ на РЦ
@dp.callback_query_handler(lambda callback: call_get_re(pattern_call_otk, callback.data[:-10]))
async def otk_call(callback_query: types.CallbackQuery):
    master_id = callback_query.data[-10:]  # id мастера
    ws_number = callback_query.data[4:-10]  # номер РЦ
    # отправка сообщения о заявке на контролёра в группу ОТК
    await bot.send_message(chat_id=test_group_id, text=f"Вас ожидают на РЦ {ws_number}. Запрос от {master_id}")
    # Обратная связь мастеру
    await bot.send_message(chat_id=master_id, text="Запрос в отк отправлен.")
    # Статус ожидание контролёра
    status_change_to_otk(ws_number=ws_number, initiator_id=master_id)
    await callback_query.answer()  # закрытие inline кнопок
# ------------------------------------------------


# ------------------------------------------------ Контролёр отвечает мастеру
# отображение inline ws_number для контролёра при ответе на запрос. Обработка команды otk_answer.
@dp.message_handler(commands=['otk_answer'])
async def otk_answer_master_send(message: types.Message):
    if message.from_user.id in control_mans_list:
        # создание inline keyboard РЦ со статусом ожидание контролёра
        inline_ws_buttons = types.InlineKeyboardMarkup()  # объект инлайн кнопок РЦ
        ws_list = ws_list_get("ожидание контролёра")
        for ws in ws_list:
            btn = types.InlineKeyboardButton(text=f'{ws}', callback_data=f'answ{ws}{message.from_user.id}')
            inline_ws_buttons.insert(btn)
        await message.answer('Выбор РЦ', reply_markup=inline_ws_buttons)
    else:
        await message.reply('У вас нет доступа к этому функционалу.')


# обработчик callback otk_answer ответа контролёра МАСТЕРУ на РЦ
@dp.callback_query_handler(lambda callback: call_get_re(pattern_answ_otk, callback.data[:-10]))
async def otk_call(callback_query: types.CallbackQuery):
    controlman_id = callback_query.data[-10:]  # id контролёра
    ws_number = callback_query.data[4:-10]  # номер РЦ
    # TODO Получить статус по номеру РЦ, если ожидание контролёра, то стоп
    # запрос в БД на id мастера
    master_id = master_id_get(ws_number=ws_number)[0]
    # отправка сообщения о заявке на контролёра в группу ОТК
    await bot.send_message(chat_id=test_group_id, text=f"Контролёр {controlman_id} ответил на запрос РЦ{ws_number}.")
    # обратная связь мастеру
    await bot.send_message(chat_id=master_id, text=f"Контролёр {controlman_id} ответил на запрос РЦ{ws_number}.")
    # сообщение в личку контролёру
    await bot.send_message(chat_id=controlman_id, text=f"Вы ответили на запрос РЦ{ws_number}.")
    # Запись в БД информации об ответе контролёра
    control_man_id_set(ws_number, controlman_id)
    await callback_query.answer()
# ------------------------------------------------


# ------------------------------------------------ Контролёр принимает решение
# отображение inline для решения отк. Обработка команды otk_decision
@dp.message_handler(commands=['otk_decision'])
async def otk_answer_master_send(message: types.Message):
    if message.from_user.id in control_mans_list:
        # создание inline keyboard РЦ со статусом ожидание контролёра
        inline_ws_buttons = types.InlineKeyboardMarkup()  # объект инлайн кнопок РЦ
        ws_list = ws_list_get("ожидание контролёра")
        for ws in ws_list:
            btn = types.InlineKeyboardButton(text=f'{ws}', callback_data=f'dcgo{ws}{message.from_user.id}')
            inline_ws_buttons.insert(btn)
        await message.answer('Выбор РЦ для принятия решения:', reply_markup=inline_ws_buttons)
    else:
        await message.reply('У вас нет доступа к этому функционалу.')


# обработчик callback otk_decision принятия решения по СЗ на РЦ для отображение инлайн СЗ
@dp.callback_query_handler(lambda callback: call_get_re(pattern_dcgo_otk, callback.data[:-10]))
async def otk_answer(callback_query: types.CallbackQuery):
    controlman_id = callback_query.data[-10:]  # id контролёра
    ws_number = callback_query.data[4:-10]  # номер РЦ
    inline_st_buttons = types.InlineKeyboardMarkup()  # объект инлайн кнопок номера СЗ
    # получение списка СЗ
    shift_task_list = st_list_get(ws_number)
    shift_task_id = st_list_get(ws_number)[0][2:5]  # id СЗ
    for task in shift_task_list:
        btn = types.InlineKeyboardButton(text=f'{task}',
                                         callback_data=f'stid{shift_task_id}{controlman_id}')
        inline_st_buttons.add(btn)
    await bot.send_message(chat_id=controlman_id, text=f'для РЦ{ws_number} выберите СЗ:',
                           reply_markup=inline_st_buttons)
    await callback_query.answer()  # закрытие inline кнопок


# обработчик callback otk_decision принятия решения по СЗ на РЦ отображение инлайн кнопок для принятия решения
@dp.callback_query_handler(lambda callback: call_get_re(pattern_stid_otk, callback.data[:-10]))
async def otk_answer(callback_query: types.CallbackQuery):
    controlman_id = callback_query.data[-10:]  # id контролёра
    # print(controlman_id)
    st_id = callback_query.data[4:-10]  # id СЗ
    # print(st_id)
    inline_dcsn_buttons = types.InlineKeyboardMarkup()  # объект инлайн кнопок решения контролёра
    # получение списка СЗ
    btn_good = types.InlineKeyboardButton(text=f'ПРИНЯТО', callback_data=f'dcsn{st_id}1{controlman_id}')
    btn_bad = types.InlineKeyboardButton(text=f'БРАК', callback_data=f'dcsn{st_id}2{controlman_id}')
    btn_miss = types.InlineKeyboardButton(text=f'НЕ ПРИНЯТО', callback_data=f'dcsn{st_id}3{controlman_id}')
    inline_dcsn_buttons.add(btn_good)
    inline_dcsn_buttons.add(btn_bad)
    inline_dcsn_buttons.add(btn_miss)
    await bot.send_message(chat_id=controlman_id, text=f'Для СЗ №{st_id}:', reply_markup=inline_dcsn_buttons)
    await callback_query.answer()  # закрытие inline кнопок


# обработчик callback записи данных по решению в базу и выдаче обратной связи мастеру
@dp.callback_query_handler(lambda callback: call_get_re(pattern_dscn_otk, callback.data[:-10]))
async def otk_answer(callback_query: types.CallbackQuery):
    st_id = callback_query.data[4:-11]  # id СЗ
    print(st_id)
    controlman_id = callback_query.data[-10:]  # id контролёра
    print(controlman_id)
    if callback_query.data[-11:-10] == '1':  # решение контролёра
        decision = 'принято'
    elif callback_query.data[-11:-10] == '2':
        decision = 'брак'
    else:
        decision = 'не принято'
    print(decision)
    # запрос из базы на РЦ и id мастера
    master_id, ws_number = master_id_get(st_id=st_id)
    # запись в базу
    decision_data_set(st_id, controlman_id, decision)
    # Сообщение в группу
    await bot.send_message(chat_id=test_group_id,
                           text=f'Контролёр {controlman_id} определил "{decision}" на РЦ {ws_number} для СЗ №{st_id}')
    # сообщение в личку
    await bot.send_message(chat_id=controlman_id,
                           text=f'Вы определили "{decision}" на РЦ {ws_number} для СЗ №{st_id}')
    # сообщение мастеру
    await bot.send_message(chat_id=master_id,
                           text=f'Контролёр {controlman_id} определил "{decision}" на РЦ {ws_number} для СЗ №{st_id}')
    await callback_query.answer()  # закрытие inline кнопок
# ------------------------------------------------


async def on_shutdown(_):  # функция выполняется при завершении работы бота
    # await bot.send_message(admin_id, "Bot is offline!")
    print('Бот офлайн.')


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True, on_startup=on_startup, on_shutdown=on_shutdown, timeout=10)

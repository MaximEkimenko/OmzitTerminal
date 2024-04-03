import datetime
import logging
import os
import re
import time

from aiogram import Bot, Dispatcher, executor, types, filters
# работа с БД
from terminal_db import (ws_list_get, status_change_to_otk, st_list_get, master_id_get, control_man_id_set,
                         decision_data_set, lines_count, control_man_id_get, all_active_st_get)

# from terminal_db import confirm_downtime, reject_downtime

logging.basicConfig(filename="log.log", level=logging.DEBUG, filemode='w',
                    format=' %(levelname)s - %(asctime)s; файл - %(filename)s; сообщение - %(message)s')
# TOKEN = os.getenv('RSU_TOKEN')
# тестовый token
TOKEN = ''

# ids
admin_id = int(os.getenv('ADMIN_TELEGRAM_ID'))
posohov_id = 2051721470  # цех 1
ermishkin_id = 5221029965
gordii_id = 6374431046
kondratiev_id = 6125791135
achmetov_id = 1153114403

ostrijnoi_id = 5380143506  # цех 2
mailashov_id = 546976234
gorojanski_id = 6299557037
kulbashin_id = 5426476877
pospelov_id = 1377896858
skorobogatov_id = 5439414299
rihmaer_id = 6305730497
lipski_id = 6424114889

savchenko_id = 2131171377  # ПДО
pavluchenkova_id = 1151694995

averkina_id = 1563020113  # ОТК
donskaya_id = 6359131276
sultigova_id = 6049253475
potapova_id = 5010645397
sofinskaya_id = 1358370501
sheglov_id = 1501419738
dubenuk_id = 1359982302
dolganev_id = 1907891961

mhitaryan_id = 413559952  # ПКО
saks_id = 1366631138  # ОГТ
# groups
# omzit_otk_group_id = -981440150
# terminal_group_id = -908012934
# omzit_master_group1_id = -4005524766  # цех 1
# omzit_master_group2_id = -4109421151  # цех 2

# test groups
omzit_otk_group_id = admin_id
terminal_group_id = admin_id
omzit_master_group1_id = admin_id
omzit_master_group2_id = admin_id

ws_numbers_c1 = ('11', '12', '13', '14', '15', '16')  # терминалы цех 1
ws_numbers_c2 = ('22', '23', '24', '25', '26', '27', '28', '29', '210', '211')  # терминалы цех 2

# fios
id_fios = {admin_id: 'Екименко М.А.',
           posohov_id: 'Посохов О.С.',
           ermishkin_id: 'Ермишкин В.М.',  # Мастера
           gordii_id: 'Гордий В.В.',
           kondratiev_id: 'Кондратьев П.В.',
           achmetov_id: 'Ахметов К.',

           mailashov_id: 'Майлашов О.',
           gorojanski_id: 'Горожанский Н.Н.',
           pospelov_id: 'Поспелов К.С.',
           kulbashin_id: 'Кульбашин Ю.А.',
           skorobogatov_id: 'Скоробогатов А.',
           ostrijnoi_id: 'Острижной К.',
           rihmaer_id: 'Рихмаер Ю.С.',

           savchenko_id: 'Савченко Е.Н.',  # ПДО
           pavluchenkova_id: 'Павлюченкова Н. Л.',
           donskaya_id: 'Донская Ю.Г.',  # ОТК
           averkina_id: 'Аверкина О.В.',
           sultigova_id: 'Султыгова О.',
           potapova_id: 'Потапова М. А.',
           sofinskaya_id: 'Софинская А. Г.',
           dolganev_id: 'Долганев А.Н.',
           dubenuk_id: 'Дубенюк А. П.',
           sheglov_id: 'Щеглов В.',

           mhitaryan_id: 'Мхитарян К.',  # ПКО
           saks_id: 'Сакс В.И.'  # ОГТ
           }

# пользователи имеющие доступ
users = (admin_id,  # root
         posohov_id, ermishkin_id, gordii_id, kondratiev_id, achmetov_id,  # производство
         savchenko_id, pavluchenkova_id,  # ПДО
         donskaya_id, averkina_id, sultigova_id, potapova_id, sofinskaya_id, sheglov_id, dubenuk_id, dolganev_id,  # ОТК
         mhitaryan_id,  # ПКО
         saks_id,  # ОГТ
         mailashov_id, gorojanski_id, pospelov_id, kulbashin_id, skorobogatov_id, ostrijnoi_id, rihmaer_id,  # цех 2
         )

# производство
masters_list = (admin_id, ermishkin_id, posohov_id, gordii_id, kondratiev_id, achmetov_id,  # цех 1
                # цех 2
                mailashov_id, gorojanski_id, pospelov_id, kulbashin_id, skorobogatov_id, ostrijnoi_id, rihmaer_id,
                )

dispatchers_list = (admin_id, savchenko_id, pavluchenkova_id,)  # диспетчеры

control_mans_list = (admin_id, donskaya_id, averkina_id, sultigova_id, potapova_id, sofinskaya_id, dolganev_id,
                     sheglov_id, dubenuk_id)  # контролёры

bot = Bot(token=TOKEN)  # инициализация бота
dp = Dispatcher(bot)  # инициализация диспетчера

# шаблоны re для callback
pattern_call_otk = r'(call)\d\d'  # шаблон для вызова ОТК
pattern_answ_otk = r'(answ)\d\d'  # шаблон для ответа ОТК
pattern_dcgo_otk = r'(dcgo)\d\d'  # шаблон запуска решения
pattern_stid_otk = r'(stid)\d'  # шаблон для вызова вариантов решений ОТК
pattern_dscn_otk = r'(dcsn)\d'  # шаблон принятого решения ОТК


async def on_startup(_):  # функция выполняется при запуске бота
    await bot.send_message(admin_id, "Терминал бот вышел в онлайн.")
    print(f'Terminal_bot вышел онлайн в {datetime.datetime.now().strftime("%H:%M:%S")}.')


def call_get_re(pattern: str, call: str) -> str:
    """
    Функция получения строки из pattern re. Используется в lambda в call_back_handler вместо фильтра regexp
    :param pattern: шаблон re
    :param call: строка для проверки
    :return: string
    """
    try:
        result_string = re.match(pattern, call).string
        # print(result_string)
    except Exception as e:
        result_string = ''
        # print('ошибка определения RegExp', e)

    return result_string


@dp.message_handler(commands=['start'])
async def start_rsu_bot(message: types.Message):
    await message.reply(text='Вас приветствует бот для работы с терминалами ЗАО ОмЗиТ! Чтобы воспользоваться ботом '
                             'используйте меню.')


@dp.message_handler(commands=['help'])
async def help_rsu_bot(message: types.Message):
    if message.from_user.id in users:
        await message.reply(text="""
        #### Последовательность процесса и взаимодействие с ботом:
        1. После того как рабочий выполнил операцию он вызывает мастера кнопкой через терминал.
        2. Сообщение приходит в группу мастеров **"ОмЗИТ Мастера цех1"** со всеми данными сменного задания.
        3. Мастер после проведения первичной приёмки выполняет вызов контролёра. 
        4. Для того, чтобы вызвать контролёра, мастер **находясь в группе, в которую пришло сообщение** нажимает символ 
        **/** рядом с полем **"Сообщение"**. В появившемся меню выбирает команду **otk_send вызов контролёра** и 
        выбирает соответствующий терминал на который нужно вызвать контролёра. 
        5. Сообщение приходит в группу контролёров **"ОмЗИТ ОТК"** .
        6. Контролёр отвечает на запрос вызовом команды **/otk_answer ответ контролёра** и выбирает терминал. 
        Сообщение о принятии вызова и  данными контролёра придёт мастеру, выполнившему вызов, и в группу мастеров 
        **"ОмЗИТ Мастера цех1"**, а также будет продублировано в группу котроллеров **"ОмЗИТ ОТК"**.
        7. В отличии от мастеров, контролёрам рекомендуется работать с ботом **omzit_terminal_bot** и отправлять 
        команды ему, а не в группе. Это сократит количество сообщений в группе.
        8. После приёмки для вынесения решения контролёру нужно воспользоваться командой **/otk_decision решение 
        контролёра** и далее следовать всплывающим кнопкам: выбирается терминал, выбирается сменное задание, выбирается 
        решение (принято, не принято, брак) Сообщения с решениям контролёра дублируются в группу мастеров 
        **"ОмЗИТ Мастера цех1"**.
        9. Сменные задание после решения контролёра **"брак"** и **"не принято"** возвращаются диспетчеру на повторное 
        распределение.
        10. Также рабочий может вызвать диспетчера с терминала в случае если у него появились вопросы 
        по сменному заданию. В этом случае сообщение придёт в группу **"ОмЗИТ Мастера цех1"**.
        11. Команда /text выводит список всех сменных заданий, которые ожидают контролёра.
        """)
    else:
        await message.reply(text="К сожалению в не являетесь зарегистрированным пользователем.")


# ------------------------------------------------ Мастер вызывает контролёра
# отображение inline ws_number для мастера при вызове ОТК. Обработка команды otk_send
@dp.message_handler(commands=['otk_send'])
async def master_otk_send(message: types.Message):
    """
    Вызов контролёра мастером через команду otk_send
    :param message:
    :return:
    """
    if message.from_user.id in masters_list:
        # создание inline keyboard РЦ со статусом ожидание мастера
        inline_ws_buttons = types.InlineKeyboardMarkup()  # объект
        ws_list = ws_list_get("ожидание мастера")
        print('список РЦ из master_otk_send', ws_list)
        if ws_list != ():
            for ws in ws_list:
                btn = types.InlineKeyboardButton(text=f'{ws}', callback_data=f'call{ws}{message.from_user.id}')
                inline_ws_buttons.insert(btn)
            await message.answer('Выбор терминала', reply_markup=inline_ws_buttons)
        else:
            await message.reply('Сменные задания со статусом "Вызов мастера" отсутствуют.')
    else:
        await message.reply('У вас нет доступа к этому функционалу.')


# обработчик callback otk_send вызова контролёра МАСТЕРОМ на РЦ
@dp.callback_query_handler(lambda callback: call_get_re(pattern_call_otk, callback.data[:-10]))
async def otk_call(callback_query: types.CallbackQuery):
    """
    Обработка callback_data при вызове контролёра otk_send
    :param callback_query:
    :return:
    """
    master_id = callback_query.data[-10:]  # id мастера
    ws_number = callback_query.data[4:-10]  # номер РЦ
    # Статус ожидание контролёра
    status_change_to_otk(ws_number=ws_number, initiator_id=master_id)
    st_count = lines_count(ws_number=str(ws_number))[0]  # количество СЗ с ожиданием контролёра
    ultra_sound_string = lines_count(ws_number=str(ws_number))[1]  # количество СЗ с ожиданием контролёра
    print('Количество сменных заданий для приёмки', st_count, f'{st_count=}')
    print('Наличие УЗК', ultra_sound_string, f'{ultra_sound_string=}')
    # отправка сообщения о заявке на контролёра в группу ОТК
    if ultra_sound_string:
        await bot.send_message(chat_id=omzit_otk_group_id, text=f"Контролёра ожидают на Т{ws_number}. Запрос от "
                                                                f"{id_fios[int(master_id)]}.\n"
                                                                f"Количество сменных заданий для приёмки: {st_count}.\n"
                                                                f"операция УЗК: {ultra_sound_string}")
    else:
        await bot.send_message(chat_id=omzit_otk_group_id, text=f"Контролёра ожидают на Т{ws_number}. Запрос от "
                                                                f"{id_fios[int(master_id)]}.\n"
                                                                f"Количество сменных заданий для приёмки: {st_count}.")
    # Обратная связь мастеру
    await bot.send_message(chat_id=master_id, text="Запрос в отк отправлен.")
    if str(ws_number) in ws_numbers_c1:
        await bot.send_message(chat_id=omzit_master_group1_id, text="Запрос в отк отправлен.")
    elif str(ws_number) in ws_numbers_c2:
        await bot.send_message(chat_id=omzit_master_group2_id, text="Запрос в отк отправлен.")
    else:
        print('Ошибка в номере рабочего центра ')
    await callback_query.answer()  # закрытие inline кнопок


# ------------------------------------------------


# ------------------------------------------------ Контролёр отвечает мастеру
# отображение inline ws_number для контролёра при ответе на запрос. Обработка команды otk_answer.
@dp.message_handler(commands=['otk_answer'])
async def otk_answer_master_send(message: types.Message):
    """
    Ответ контролёра на все вызовы мастера на выбранном терминале
    :param message:
    :return:
    """
    if message.from_user.id in control_mans_list:
        ws_list = ws_list_get("ожидание контролёра")  # список терминалов с ожиданием контролёра
        inline_ws_buttons = types.InlineKeyboardMarkup()  # объект инлайн кнопок РЦ
        if ws_list != ():
            for ws in ws_list:
                btn = types.InlineKeyboardButton(text=f'{ws}', callback_data=f'answ{ws}{message.from_user.id}')
                inline_ws_buttons.insert(btn)
            await message.answer('Выбор терминала', reply_markup=inline_ws_buttons)
        else:
            await message.reply('Терминалы с ожиданием контролёра отсутствуют.')
    else:
        await message.reply('У вас нет доступа к этому функционалу.')


# обработчик callback otk_answer ответа контролёра МАСТЕРУ на РЦ
@dp.callback_query_handler(lambda callback: call_get_re(pattern_answ_otk, callback.data[:-10]))
async def otk_call_handler(callback_query: types.CallbackQuery):
    """
    Обработчик callback.data при ответе контролёра
    :param callback_query:
    :return:
    """
    controlman_id = callback_query.data[-10:]  # id контролёра
    ws_number = callback_query.data[4:-10]  # номер РЦ
    # запрос в БД на id мастера
    master_id = master_id_get(ws_number=ws_number)[0]
    try:
        # проверка уже вышедшего контролёра
        if not control_man_id_get(ws_number)[0]:
            # отправка сообщения о заявке на контролёра в группу ОТК
            await bot.send_message(chat_id=omzit_otk_group_id,
                                   text=f"Контролёр {id_fios[int(controlman_id)]} ответил на запрос Т{ws_number}.")
            # обратная связь мастеру
            await bot.send_message(chat_id=master_id, text=f"Контролёр {id_fios[int(controlman_id)]} ответил "
                                                           f"на запрос Т{ws_number}.")
            # обратная связь в группу мастерам
            if str(ws_number) in ws_numbers_c1:
                await bot.send_message(chat_id=omzit_master_group1_id,
                                       text=f"Контролёр {id_fios[int(controlman_id)]} ответил "
                                            f"на запрос Т{ws_number}.")
            elif str(ws_number) in ws_numbers_c2:
                await bot.send_message(chat_id=omzit_master_group2_id,
                                       text=f"Контролёр {id_fios[int(controlman_id)]} ответил "
                                            f"на запрос Т{ws_number}.")
            # сообщение в личку контролёру
            await bot.send_message(chat_id=controlman_id, text=f"Вы ответили на запрос Т{ws_number}.")
            # Запись в БД информации об ответе контролёра
            control_man_id_set(ws_number, controlman_id)
            await callback_query.answer()
        else:
            # отправка сообщений ЧТО УЖЕ БЫЛ КОНТРОЛЁР
            await bot.send_message(chat_id=omzit_otk_group_id,
                                   text=f'Контролёр {id_fios.get(int(control_man_id_get(ws_number)[0]), "Unknown")} '
                                        f'уже ответил на заявку Т{ws_number}')
            # сообщение в личку контролёру
            await bot.send_message(chat_id=controlman_id,
                                   text=f'Контролёр {id_fios.get(int(control_man_id_get(ws_number)[0]), "Unknown")} '
                                        f'уже ответил на заявку Т{ws_number}')
    except Exception as e:
        print(e, ' Ошибка в otk_call_handler')


# ------------------------------------------------


# ------------------------------------------------ Контролёр принимает решение
# отображение inline для решения отк. Обработка команды otk_decision
@dp.message_handler(commands=['otk_decision'])
async def otk_decision_terminal_choice(message: types.Message):
    """
    Принятие решения контролёром по сменному заданию. Выбор терминала.
    :param message:
    :return:
    """
    if message.from_user.id in control_mans_list:
        # создание inline keyboard РЦ со статусом ожидание контролёра
        inline_ws_buttons = types.InlineKeyboardMarkup()  # объект инлайн кнопок РЦ
        ws_list = ws_list_get("ожидание контролёра")
        if ws_list != ():
            for ws in ws_list:
                btn = types.InlineKeyboardButton(text=f'{ws}', callback_data=f'dcgo{ws}{message.from_user.id}')
                inline_ws_buttons.insert(btn)
            await message.answer('Выбор терминала для принятия решения:', reply_markup=inline_ws_buttons)
        else:
            await message.reply('Терминалы с СЗ для приёмки отсутствуют.')
    else:
        await message.reply('У вас нет доступа к этому функционалу.')


# обработчик callback otk_decision принятия решения по СЗ на РЦ для отображение инлайн СЗ
@dp.callback_query_handler(lambda callback: call_get_re(pattern_dcgo_otk, callback.data[:-10]))
async def otk_decision_shift_task_choice(callback_query: types.CallbackQuery):
    """
    Обработчик callback_data для отображения inline кнопок сменного задания. Выбор сменного задания.
    :param callback_query:
    :return:
    """
    controlman_id = callback_query.data[-10:]  # id контролёра
    ws_number = callback_query.data[4:-10]  # номер РЦ
    inline_st_buttons = types.InlineKeyboardMarkup()  # объект инлайн кнопок номера СЗ
    # проверка новых кнопок
    # inline_st_buttons2 = types.ReplyKeyboardMarkup()
    # получение списка СЗ
    shift_task_list = st_list_get(ws_number)
    full_task_text = '\n'.join(shift_task_list)
    for task in shift_task_list:
        # print('Сменное задание в otk_decision_shift_task_choice: ', task)
        # print(['task_id в otk_decision_shift_task_choice', str(task).find("|") - 1])
        shift_task_id = task[2:str(task).find("|") - 1]  # id СЗ
        btn = types.InlineKeyboardButton(text=f'ВЫБРАТЬ СЗ: № {shift_task_id}',
                                         callback_data=f'stid{shift_task_id}{controlman_id}')
        inline_st_buttons.add(btn)
        # проверка новых кнопок
        # btn2 = types.KeyboardButton(text=f'{ws}', callback_data=f'answ{ws}{message.from_user.id}')
        # inline_st_buttons2.insert(btn2)
    # добавить full_task_text в текст перед кнопками?
    # await bot.send_message(chat_id=controlman_id, text=f'для Т{ws_number} выберите СЗ:',
    #                        reply_markup=inline_st_buttons)
    await bot.send_message(chat_id=controlman_id, text='Список СЗ для приёмки: \n' + full_task_text,
                           reply_markup=inline_st_buttons)
    # проверка новых кнопок
    # await bot.send_message(chat_id=controlman_id, text=f'для Т{ws_number} выберите СЗ:',
    #                        reply_markup=inline_st_buttons2)
    await callback_query.answer()  # закрытие inline кнопок


# обработчик callback otk_decision принятия решения по СЗ на РЦ отображение инлайн кнопок для принятия решения
@dp.callback_query_handler(lambda callback: call_get_re(pattern_stid_otk, callback.data[:-10]))
async def otk_decision_choice(callback_query: types.CallbackQuery):
    """
    Отображение inline решения контролёра. Выбор решения контролёра.
    :param callback_query:
    :return:
    """
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
async def otk_decision_register(callback_query: types.CallbackQuery):
    """
    Обработка решения callback.data решения контролёра. Запись решения в БД.
    :param callback_query:
    :return:
    """
    st_id = callback_query.data[4:-11]  # id СЗ
    controlman_id = callback_query.data[-10:]  # id контролёра
    if callback_query.data[-11:-10] == '1':  # решение контролёра
        decision = 'принято'
    elif callback_query.data[-11:-10] == '2':
        decision = 'брак'
    else:
        decision = 'не принято'
    # запрос из базы на РЦ и id мастера
    master_id, ws_number = master_id_get(st_id=st_id)
    # запись в базу
    decision_data_set(st_id, controlman_id, decision)
    # Сообщение в группу
    await bot.send_message(chat_id=omzit_otk_group_id,
                           text=f'Контролёр {id_fios[int(controlman_id)]} определил "{decision}" на Т{ws_number} '
                                f'для СЗ №{st_id}')
    # сообщение в личку
    await bot.send_message(chat_id=controlman_id,
                           text=f'Вы определили "{decision}" на Т{ws_number} для СЗ №{st_id}')
    # сообщение в группу мастерам
    if str(ws_number) in ws_numbers_c1:
        await bot.send_message(chat_id=omzit_master_group1_id,
                               text=f'Контролёр {id_fios[int(controlman_id)]} определил "{decision}" на Т{ws_number} '
                                    f'для СЗ №{st_id}')
    elif str(ws_number) in ws_numbers_c2:
        await bot.send_message(chat_id=omzit_master_group2_id,
                               text=f'Контролёр {id_fios[int(controlman_id)]} определил "{decision}" на Т{ws_number} '
                                    f'для СЗ №{st_id}')
    # сообщение мастеру
    await bot.send_message(chat_id=master_id,
                           text=f'Контролёр {id_fios[int(controlman_id)]} определил "{decision}" на Т{ws_number} '
                                f'для СЗ №{st_id}')
    await callback_query.answer()  # закрытие inline кнопок


# TODO ЗАКОНСЕРВИРОВАНО Функционал простоев
# @dp.message_handler(lambda message: 'Подтвердите простой на Т' in message.reply_to_message.text)
# async def downtime_master_decision(message: types.Message):
#     """
#     Обработка решения мастера по простою
#     """
#     # получаем ФИО мастера по telegram id
#     master_fio = id_fios.get(message.from_user.id, message.from_user.id)
#     # получаем номер сменного задания
#     st_match = re.match(r'.*Номер СЗ: (\d+)\.', message.reply_to_message.text)
#     if st_match:
#         st_number = st_match.group(1)
#
#         # Проверяем правильность формата ответа
#         answer_match = re.match(r'(^\bДа\b|^\bНет\b)\s*(.*)', message.text)
#         if answer_match:
#             answer, description = answer_match.group(1, 2)
#             if answer == 'Да':
#
#                 confirm_downtime(st_number, master_fio, description)
#                 await message.answer(f'Простой по СЗ {st_number} подтвержден')
#
#                 question_match = re.match(
#                     r'.*на (.+) по причине: (.*)\n\nДлительным.*', message.reply_to_message.text)
#                 if question_match:
#                     question = f'{question_match.group(1)}. {question_match.group(2)} Описание: {description}'
#                     await bot.send_message(chat_id=terminal_group_id, text=f'{question}')
#
#             elif answer == 'Нет':
#                 reject_downtime(st_number, master_fio, description)
#                 await message.answer(f'Простой по СЗ {st_number} отклонен')
#
#             # удаляем исходное сообщение
#             if message.reply_to_message.message_id:
#                 await bot.delete_message(chat_id=message.chat.id, message_id=message.reply_to_message.message_id)
#         else:
#             await message.reply(f'Неверный формат ответа! Введите "Да" или "Нет", '
#                                 f'при необходимости через пробел укажите описание проблемы')


# ------------------------------------------------


@dp.message_handler(commands=['text'])  # получение активных запросов отк в виде строки
async def report_active_shift_tasks(message: types.Message):
    if message.from_user.id in control_mans_list:
        try:
            active_tasks = all_active_st_get()
            if active_tasks:
                await message.reply(text=active_tasks)
            else:
                await message.answer(text='Активных запросов на контролёра на данный момент нет.')
        except Exception as e:
            print(e)
    else:
        await message.answer(text='У вас не доступа к этому функционалу. Обратитесь к руководителю.')
    pass


async def on_shutdown(_):  # функция выполняется при завершении работы бота
    # await bot.send_message(admin_id, "Bot is offline!")
    print('Бот офлайн.')


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True, on_startup=on_startup, on_shutdown=on_shutdown, timeout=10)

from django.contrib.auth.decorators import login_required
import datetime
import json
import os
import time
import asyncio
import socket
from django.http import FileResponse
from django.http import HttpResponse
from django.shortcuts import redirect
from django.db.models import Q, QuerySet, F
from django.shortcuts import render
from django.core.exceptions import PermissionDenied
from django.utils import timezone

from omzit_terminal.settings import BASE_DIR
from scheduler.models import ShiftTask, Downtime

from .forms import WorkplaceChoose, DowntimeReasonForm
from .services.master_call_db import select_master_call, select_dispatcher_call
from .services.master_call_function import send_call_master, send_call_dispatcher, terminal_message_to_id
from .services.master_call_function import get_client_ip


# @login_required(login_url="login")
def ws_number_choose(request):
    """
    Выбор РЦ
    :param request:
    :return:
    """
    # users = ('admin', 'termi')
    # if str(request.user.username).strip()[:5] not in users:
    #     raise PermissionDenied
    if request.method == 'POST':
        ws_number_form = WorkplaceChoose(request.POST)
        # получение номера РЦ
        if ws_number_form.is_valid():
            ws_number = ws_number_form.cleaned_data['ws_number'].ws_number
            print(ws_number)
            # редирект на страницу РЦ
            return redirect(f'/worker/{ws_number}')
    else:
        ws_number_form = WorkplaceChoose()
    context = {'ws_number_form': ws_number_form}
    return render(request, r"worker/worker_ws_choose.html", context=context)


# @login_required(login_url="login")
def worker(request, ws_number):
    """
    Обработка данных на странице терминала РЦ ws_number
    :param request:
    :param ws_number:
    :return:
    """
    # if str(request.user.username).strip()[:5] != "admin" or str(request.user.username).strip() != "termi":
    #     raise PermissionDenied
    # users = ('admin', 'termi')
    # if str(request.user.username).strip()[:5] not in users:
    #     raise PermissionDenied
    # список разрешённых по имени компа
    allowed_terminal_list = ('APM-0036',  # Екименко
                             'SPR-008',  # Терминал №3
                             'APM-0168',  # Отто
                             'APM-0314',  # Чекаловец
                             'APM-0168',
                             'TZ-001',  # Новые терминалы по порядку
                             'TZ-002',
                             'TZ-003',
                             'TZ-004',
                             'TZ-005',
                             'TZ-006',
                             'TZ-007',
                             'TZ-008',
                             'TZ-009',
                             'APM-0229',  # Планшет
                             )
    terminal_ip = get_client_ip(request)  # определение IP терминала
    terminal_name = socket.getfqdn(terminal_ip)  # определение полного имени по IP
    if terminal_name[:terminal_name.find('.')] not in allowed_terminal_list:
        raise PermissionDenied
    else:
        print(f'Permission granted to {terminal_name[:terminal_name.find(".")]}')
    # вывод таблицы распределённых РЦ
    today = datetime.datetime.now().strftime('%d.%m.%Y')
    initial_shift_tasks = (ShiftTask.objects.values('id', 'ws_number', 'model_name', 'order', 'op_number',
                                                    'op_name_full', 'norm_tech', 'fio_doer', 'st_status',
                                                    'datetime_job_start', 'decision_time')
                           .filter(ws_number=ws_number, next_shift_task=None).exclude(fio_doer='не распределено')
                           .exclude(Q(decision_time__lte=datetime.datetime.strptime(today, '%d.%m.%Y')) &
                                    Q(st_status='принято'))
                           .exclude(Q(decision_time__lte=datetime.datetime.strptime(today, '%d.%m.%Y')) &
                                    Q(st_status='брак'))
                           .exclude(Q(decision_time__lte=datetime.datetime.strptime(today, '%d.%m.%Y')) &
                                    Q(st_status='не принято'))
                           .order_by("st_status"))
    select_shift_task = ((ShiftTask.objects.values('id', 'ws_number', 'model_name', 'order', 'op_number',
                                                   'op_name_full', 'norm_tech', 'fio_doer', 'st_status',
                                                   'datetime_job_start', 'decision_time')
                          .filter(ws_number=ws_number)).exclude(fio_doer='не распределено')
                         .exclude(st_status='брак')
                         .exclude(st_status='не принято')
                         .exclude(st_status='принято')
                         .order_by("st_status"))
    # формирование сообщений
    if request.method == 'POST':
        print(request.POST)
        if 'сменное' not in request.POST['task_id']:
            # определение id записи
            if 'брак' in request.POST['task_id']:
                alert_message = 'Это СЗ уже принято как БРАК. Необходимо перепланирование.'
            elif 'принято' in request.POST['task_id']:
                alert_message = 'Сменно задание закрыто.'
            elif 'ожидание мастера' in request.POST['task_id']:
                alert_message = 'Мастер УЖЕ вызван.'
            elif 'ожидание контролёра' in request.POST['task_id']:
                alert_message = 'Ожидается контролёр.'
            elif 'в работе' in request.POST['task_id']:
                alert_message = 'Требуется вызов мастера'
            elif 'запланировано' in request.POST['task_id']:
                alert_message = 'СЗ принято в работу.'
            else:
                alert_message = 'Все ок'
            index = request.POST['task_id'].find('--')
            task_id = request.POST['task_id'][:index]
            # статус в работе
            # если статус запланировано или пауза установка статуса в работе
            if 'запланировано' in request.POST['task_id'] or 'пауза' in request.POST['task_id']:
                # if 'ожидание мастера' not in request.POST['task_id']:  # если нет статуса ожидания мастера
                print('task_id: ', task_id)
                # обновление данных
                if not ShiftTask.objects.filter(pk=task_id, st_status='в работе'):
                    ShiftTask.objects.filter(pk=task_id).update(st_status='в работе',
                                                                datetime_job_start=datetime.datetime.now(),
                                                                datetime_job_resume=datetime.datetime.now(),
                                                                job_duration=datetime.timedelta(0),
                                                                )
                    alert_message = 'Сменное задание запущенно в работу.'
            elif 'пауза' in request.POST['task_id']:
                resume_work(task_id=task_id)
            elif 'простой' in request.POST['task_id']:
                resume_work(task_id=task_id, from_status='простой')
            else:
                print("Это СЗ уже взято в работу!")
        else:
            print('Выберите ещё раз.')
            alert_message = 'Неверный выбор. Выберите ещё раз. '
    else:
        if request.GET.get('call') == 'True':
            alert_message = 'Вызов мастеру отправлен.'
        elif request.GET.get('call') == 'False_wrong':
            alert_message = 'Неверный выбор.'
        elif request.GET.get('call') == 'False':
            alert_message = 'Сменное задание не принято в работу или вызов мастеру был отправлен ранее.'
        elif request.GET.get('call') == 'True_disp':
            alert_message = 'Сообщение диспетчеру отправлено.'
        else:
            alert_message = ''
    context = {'initial_shift_tasks': initial_shift_tasks, 'ws_number': ws_number,
               'select_shift_task': select_shift_task, 'alert': alert_message}
    if 'Mobile' in request.META['HTTP_USER_AGENT'] or terminal_name[:terminal_name.find('.')] == 'APM-0229':
        return render(request, r"worker/worker-mobile.html", context=context)
    else:
        return render(request, r"worker/worker.html", context=context)


def draws(request, ws_st_number: str):
    """
    Выбор чертежей
    :param request:
    :param ws_st_number:
    :return:
    """
    # получение переменных из строки запроса
    ws_number = str(ws_st_number).split('--')[0]
    op_number = str(ws_st_number).split('--')[1]
    model_name = str(ws_st_number).split('--')[2]
    st_number = str(ws_st_number).split('--')[3]
    header_string = f'Т{ws_number} СЗ {st_number}'

    # # Выбор списка чертежей
    select_draws = (ShiftTask.objects.values('ws_number', 'model_name', 'op_number', 'op_name_full', 'draw_path',
                                             'draw_filename', 'model_order_query')
                    .filter(ws_number=ws_number, op_number=op_number, model_name=model_name, id=st_number))
    print(select_draws)
    draw_path = fr"C:\draws\{select_draws[0]['model_order_query']}\\"

    pdf_links = []  # список словарей чертежей
    # если несколько чертежей
    if select_draws[0]['draw_filename'] is not None:
        if ',' in select_draws[0]['draw_filename']:
            draw_filenames = select_draws[0]['draw_filename'].split(',')
            for draw_filename in draw_filenames:
                pdf_links.append({'link': fr"{draw_path}{str(draw_filename).strip()}", 'filename': draw_filename})
        else:
            draw_filename = select_draws[0]['draw_filename']
            pdf_links.append({'link': fr"{draw_path}{str(draw_filename).strip()}", 'filename': draw_filename})
        print('pdf_links', pdf_links)
    context = {'ws_number': ws_number, 'st_number': st_number, 'select_draws': select_draws, 'pdf_links': pdf_links}
    terminal_ip = get_client_ip(request)  # определение IP терминала
    terminal_name = socket.getfqdn(terminal_ip)  # определение полного имени по IP
    if 'Mobile' in request.META['HTTP_USER_AGENT'] or terminal_name[:terminal_name.find('.')] == 'APM-0229':
        return render(request, r"worker/draws-mobile.html", context=context)
    else:
        return render(request, r"worker/draws.html", context=context)


def show_draw(request, ws_number, pdf_file):
    # TODO сделать отмену если ссылки на чертёж нет или она не валидная
    # преобразование строки из запроса в ссылку
    try:
        path_to_file = (str(pdf_file).replace('--', '/')) + '.pdf'
        response = FileResponse(open(fr'{path_to_file}', 'rb'))
        response['X-Frame-Options'] = 'SAMEORIGIN'
        return response
    except FileNotFoundError as e:
        print(e)


def make_master_call(request, ws_st_number):
    ws_number = str(ws_st_number)[:str(ws_st_number).find('-')]
    st_number = str(ws_st_number)[str(ws_st_number).rfind('-') + 1:]
    print('ws = ', ws_number)
    print('st = ', st_number, type(st_number))
    print('ws-st', ws_st_number)
    # if st_number == '0':
    #     return redirect(f'/worker/{ws_number}?call=False')
    # выборка вызовов мастера на РЦ ws_number
    messages = select_master_call(ws_number=str(ws_number), st_number=str(st_number))
    print('messages=', messages)
    time.sleep(1)  # пауза 1 сек
    if messages:
        print('Вызов мастера')
        for message in messages:
            asyncio.run(send_call_master(message))  # отправка в группу мастерам телеграм ботом
            # отправка в группу
            # asyncio.run(terminal_message_to_id(to_id=group_id, text_message_to_id=message))
        print('Окончание вызова')
        return redirect(f'/worker/{ws_number}?call=True')
    elif st_number == '0':
        return redirect(f'/worker/{ws_number}?call=False_wrong')
    else:
        return redirect(f'/worker/{ws_number}?call=False')


def make_dispatcher_call(request, ws_st_number):
    # group_id = -908012934  # тг группа
    ws_number = str(ws_st_number)[:str(ws_st_number).find('-')]
    st_number = str(ws_st_number)[str(ws_st_number).rfind('-') + 1:]
    print('ws = ', ws_number)
    print('st = ', st_number, type(st_number))
    print('ws-st', ws_st_number)
    if st_number == '0':
        return redirect(f'/worker/{ws_number}?call=False_wrong')
    # выборка вызовов мастера на РЦ ws_number
    messages = select_dispatcher_call(ws_number=str(ws_number), st_number=str(st_number))
    print('messages=', messages)
    time.sleep(1)  # пауза 1 сек
    if messages:
        print('Вызов диспетчера')
        for message in messages:
            asyncio.run(send_call_dispatcher(message))  # отправка в группу мастерам и диспетчерам телеграм ботом
            # отправка в группу
            # asyncio.run(terminal_message_to_id(to_id=group_id, text_message_to_id=message))
        print('Окончание вызова')
        return redirect(f'/worker/{ws_number}?call=True_disp')
    elif st_number == 0:
        return redirect(f'/worker/{ws_number}?call=False_wrong')


def pause_work(task_id=None, is_lunch=False, to_status='пауза'):
    """
    Постановка СЗ на паузу
    Если task_id (номер СЗ) не указан, то приостанавливаются все СЗ со статусом в 'в работе'
    """
    stopped_shift_tasks = []
    shift_tasks = ShiftTask.objects.filter(st_status='в работе')
    if task_id:  # если выбрано конкретное СЗ для остановки
        shift_tasks = shift_tasks.filter(pk=task_id)
    for st in shift_tasks:
        # если указан обед, то добавляем все СЗ со статусом "в работе" в список для записи в json
        if is_lunch and not task_id:
            stopped_shift_tasks.append(st.pk)
        message_to_master = (f"Приостановлена работа на Т{st.ws_number}. Номер СЗ: {st.id}. "
                             f"Заказ: {st.order}. Изделие: {st.model_name}. "
                             f"Операция: {st.op_number} {st.op_name_full}. "
                             f"Исполнители: {st.fio_doer}")
        try:
            asyncio.run(send_call_master(message_to_master))
        except Exception as ex:
            print(f"При попытке отправки сообщения мастеру из функции 'pause_work' вызвано исключение: {ex}")

    shift_tasks.update(
        st_status=to_status,
        job_duration=F("job_duration") + (timezone.now() - F("datetime_job_resume")),
    )

    if is_lunch:  # если автоматическая пауза в обеденное время

        # открываем существующий json или создаем новый со списком остановленных СЗ под ключом "lunch_stop"
        json_path = os.path.join(BASE_DIR, "storage.json")
        try:
            if os.path.exists(json_path):
                with open(json_path, "r") as file:
                    data = json.load(file)
                print(f"Файл storage.json чтение {data}")
                data["lunch_stop"] = stopped_shift_tasks
                with open(json_path, "w") as file:
                    json.dump(data, file)
                print(f"Файл storage.json запись {data}")
            else:
                raise Exception("Файл storage.json не найден!")
        except Exception as ex:
            print(f"Ошибка при чтении storage.json: {ex}")
            with open(json_path, "w") as file:
                data = {
                    "lunch_stop": stopped_shift_tasks
                }
                json.dump(data, file)
            print(f"Новый файл storage.json {data}")


def resume_work(task_id=None, is_lunch=False, from_status='пауза'):
    """
    Возобновление работы по СЗ
    Если task_id (номер СЗ) не указан, то возобновляются все СЗ со статусом в 'пауза', остановленные в обед
    """
    shift_tasks = []
    if task_id:  # если выбрано конкретное СЗ для возобновления
        shift_tasks = ShiftTask.objects.filter(st_status=from_status, pk=task_id)
    elif is_lunch:  # если возобновляем СЗ после обеда

        # открываем json, читаем список остановленных на время обеда СЗ
        json_path = os.path.join(BASE_DIR, "storage.json")
        try:
            if os.path.exists(json_path):
                with open(json_path, "r") as file:
                    data = json.load(file)
                print(f"Файл storage.json чтение {data}")
                stopped_shift_tasks = data.get("lunch_stop")
                data["lunch_stop"] = []
                with open(json_path, "w") as file:
                    json.dump(data, file)
                print(f"Файл storage.json запись {data}")
            else:
                raise Exception("Файл storage.json не найден!")
        except Exception as ex:
            print(f"Ошибка при чтении storage.json: {ex}")
            stopped_shift_tasks = None

        if stopped_shift_tasks:
            shift_tasks = ShiftTask.objects.filter(st_status='пауза', pk__in=stopped_shift_tasks)
    else:
        print('Непредусмотренный случай возобновления работы!')
    for st in shift_tasks:
        message_to_master = (f"Возобновлена работа на Т{st.ws_number}. Номер СЗ: {st.id}. "
                             f"Заказ: {st.order}. Изделие: {st.model_name}. "
                             f"Операция: {st.op_number} {st.op_name_full}. "
                             f"Исполнители: {st.fio_doer}")
        try:
            asyncio.run(send_call_master(message_to_master))
        except Exception as ex:
            print(f"При попытке отправки сообщения мастеру из функции 'resume_work' вызвано исключение: {ex}")
    if isinstance(shift_tasks, QuerySet):
        shift_tasks.update(st_status='в работе', datetime_job_resume=timezone.now())


def downtime_reason(request, ws_number, st_number):
    """
    Выбор причины простоя по СЗ
    :param request:
    :param ws_number: номер терминала
    :param st_number: номер сменного задания
    """
    shift_task = ShiftTask.objects.get(pk=int(st_number))
    context = {
        'st_number': st_number,
        'ws_number': ws_number,
        'form': DowntimeReasonForm(),
        'alert': ' ',
        'shift_task': shift_task,
        'alert_time': 30,  # время в секундах отображения сообщения
    }
    if request.method == 'POST':
        data = request.POST
        reason = data.get('reason')
        if reason:
            Downtime.objects.create(shift_task=shift_task, reason=reason)
            message_to_master = (f"❗Подтвердите простой на Т{shift_task.ws_number} по причине: {reason}. "
                                 f"Номер СЗ: {shift_task.id}. "
                                 f"Заказ: {shift_task.order}. Изделие: {shift_task.model_name}. "
                                 f"Операция: {shift_task.op_number} {shift_task.op_name_full}. "
                                 f"Исполнители: {shift_task.fio_doer}"
                                 f"Длительным нажатием на данное сообщение вызовите меню и выберите 'Ответить'. "
                                 f"Для подтверждения введите 'Да' и через пробел описание проблемы, "
                                 f"'Нет' для отмены запроса и продолжения работы"
                                 )
            try:
                pass
                asyncio.run(send_call_master(message_to_master))
            except Exception as ex:
                print(f"При попытке отправки сообщения мастеру из функции 'downtime_reason' вызвано исключение: {ex}")
            context['alert'] = f'Направлено сообщение мастеру для подтверждения простоя по причине: {reason}'
            context['alert_time'] = 15
        else:
            context['alert'] = f'Выберите причину простоя'

    terminal_ip = get_client_ip(request)  # определение IP терминала
    terminal_name = socket.getfqdn(terminal_ip)  # определение полного имени по IP
    if 'Mobile' in request.META['HTTP_USER_AGENT'] or terminal_name[:terminal_name.find('.')] == 'APM-0229':
        return render(request, r"worker/downtime-reasons-mobile.html", context=context)
    else:
        return render(request, r"worker/downtime-reasons.html", context=context)

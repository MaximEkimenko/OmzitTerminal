import datetime
import time
import asyncio

from django.shortcuts import redirect
from django.db.models import Q
from django.shortcuts import render

from scheduler.models import ShiftTask
from tehnolog.models import TechData

from .forms import WorkplaceChoose
from .services.master_call_db import select_master_call
from .services.master_call_function import send_call_master


# TODO найти решение аналогов РЦ. Убрать обозначение РЦ "РЦ№1/РЦ№2" - вместо "/" использовать "-"
#

def ws_number_choose(request):
    """
    Выбор РЦ
    :param request:
    :return:
    """
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


def worker(request, ws_number):
    """
    Обработка данных на странице терминала РЦ ws_number
    :param request:
    :param ws_number:
    :return:
    """
    # вывод таблицы распределённых РЦ
    context = {}
    today = datetime.datetime.now().strftime('%d.%m.%Y')
    initial_shift_tasks = (ShiftTask.objects.values('id', 'ws_number', 'model_name', 'order', 'op_number',
                                                    'op_name_full', 'norm_tech', 'fio_doer', 'st_status',
                                                    'datetime_job_start', 'decision_time')
                           .filter(ws_number=ws_number).exclude(fio_doer='не распределено')
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
    # terminal_listener должен быть включён!
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
            index = request.POST['task_id'].find('---')
            task_id = request.POST['task_id'][:index]
            # статус в работе
            if 'запланировано' in request.POST['task_id']:  # если статус запланировано установка статуса в работе
                # if 'ожидание мастера' not in request.POST['task_id']:  # если нет статуса ожидания мастера
                print('task_id: ', task_id)
                # обновление данных
                if not ShiftTask.objects.filter(pk=task_id, st_status='в работе'):
                    ShiftTask.objects.filter(pk=task_id).update(st_status='в работе',
                                                                datetime_job_start=datetime.datetime.now())
                    alert_message = 'Сменное задание запущенно в работу.'
                    # return redirect(f'/worker/{ws_number}', context={'alert': alert_message})  # обновление страницы
                # else:
                #     print("Мастер уже вызван!")
            else:
                print("Это СЗ уже взято в работу!")
        else:
            print('Выберите ещё раз.')
            alert_message = 'Неверный выбор. Выберите ещё раз. '
    else:
        if request.GET.get('call') == 'True':
            alert_message = 'Вызов мастеру отправлен.'
        elif request.GET.get('call') == 'False':
            alert_message = 'Вызов мастеру уже был отправлен ранее.'
        else:
            alert_message = ''
    print('select_shift_task', select_shift_task)
    context = {'initial_shift_tasks': initial_shift_tasks, 'ws_number': ws_number,
               'select_shift_task': select_shift_task, 'alert': alert_message}

    # print(context)
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
    header_string = f'РЦ {ws_number} СЗ {st_number}'

    # TODO сделать запрос к ShiftTask после заполнения данных
    # # Выбор списка чертежей
    select_draws = (TechData.objects.values('ws_number', 'model_name', 'op_number', 'op_name_full', 'draw_path',
                                            'draw_filename')
                    .filter(ws_number=ws_number, op_number=op_number, model_name=model_name)
                    )
    print(select_draws)

    draw_path = select_draws[0]['draw_path']  # путь к чертежам
    pdf_links = []  # список словарей чертежей
    # если несколько чертежей
    if ',' in select_draws[0]['draw_filename']:
        draw_filenames = select_draws[0]['draw_filename'].split(',')
        for draw_filename in draw_filenames:
            pdf_links.append({'link': fr"{draw_path}\{draw_filename}", 'filename': draw_filename})
    else:
        draw_filename = select_draws[0]['draw_filename']
        pdf_links.append({'link': fr"{draw_path}\{draw_filename}", 'filename': draw_filename})

    # TODO
    #  выбор из списка
    #  прослушивание кнопки для перехода на чертёж подготовка view (и template?) для отображения
    #  управление кнопками внутри открывшегося чертежа (открывать чертёж в iframe?)
    #  закрытие всего по прослушанной кнопке выхода = редирект на worker

    context = {'header_string': header_string, 'select_draws': select_draws, 'pdf_links': pdf_links}
    return render(request, r"worker/draws.html", context=context)


def make_master_call(request, ws_st_number):
    ws_number = str(ws_st_number)[:str(ws_st_number).find('-')]
    st_number = str(ws_st_number)[str(ws_st_number).rfind('-') + 1:]
    print('ws = ', ws_number)
    print('st = ', st_number, type(st_number))
    print('ws-st', ws_st_number)
    if st_number == '0':
        return redirect(f'/worker/{ws_number}?call=False')
    # выборка вызовов мастера на РЦ ws_number
    messages = select_master_call(ws_number=str(ws_number), st_number=str(st_number))
    print('messages=', messages)
    time.sleep(1)  # пауза 1 сек
    if messages:
        print('Вызов мастера')
        for message in messages:
            asyncio.run(send_call_master(message))  # отправка мастеру в телеграм ботом
        print('Окончание вызова')
        return redirect(f'/worker/{ws_number}?call=True')
    else:
        return redirect(f'/worker/{ws_number}?call=False')

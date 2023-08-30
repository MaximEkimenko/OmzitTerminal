import datetime

from django.shortcuts import render
from .forms import WorkplaceChoose
from django.shortcuts import redirect
from scheduler.models import ShiftTask

from pynput import keyboard
from pynput.keyboard import Key, Controller

keyboard_class = Controller()


# TODO найти решение аналогов РЦ. Убрать обозначение РЦ "РЦ№1/РЦ№2" - вместо "/" использовать "-"


def ws_number_choose(request):
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
    # вывод таблицы распределённых РЦ
    context = {}
    initial_shift_tasks = (ShiftTask.objects.values('id', 'ws_number', 'model_name', 'order', 'op_number',
                                                    'op_name_full', 'norm_tech', 'fio_doer', 'st_status',
                                                    'datetime_job_start', 'decision_time', 'norm_fact')
                           .filter(ws_number=ws_number)).exclude(fio_doer='не распределено').order_by("st_status")
    select_shift_task = (ShiftTask.objects.values('id', 'ws_number', 'model_name', 'order', 'op_number',
                                                  'op_name_full', 'norm_tech', 'fio_doer', 'st_status',
                                                  'datetime_job_start', 'decision_time', 'norm_fact')
                         .filter(ws_number=ws_number)).exclude(fio_doer='не распределено').order_by("st_status")

    # terminal_listener должен быть включён!
    if request.method == 'POST':
        print(request.POST)
        if 'сменное' not in request.POST['task_id']:
            # определение id записи
            index = request.POST['task_id'].find('---')
            task_id = request.POST['task_id'][:index]
            # статус в работе
            if 'в работе' not in request.POST['task_id']:  # если нет статуса в работе
                if 'ожидание мастера' not in request.POST['task_id']:  # если нет статуса ожидания мастера
                    print('task_id: ', task_id)
                    # обновление данных
                    if not ShiftTask.objects.filter(pk=task_id, st_status='в работе'):
                        ShiftTask.objects.filter(pk=task_id).update(st_status='в работе',
                                                                    datetime_job_start=datetime.datetime.now())
                        return redirect(f'/worker/{ws_number}')  # обновление страницы
                else:
                    print("Мастер уже вызван!")
            else:
                print("Это СЗ уже взято в работу!")
            # статус ожидание мастера
            if 'в работе' in request.POST['task_id']:  # если статус "в работе"
                print('Меняем статус СЗ')
                # количество вызовов мастера
                master_calls = ShiftTask.objects.filter(pk=task_id).values('master_calls')[0]['master_calls']
                print('master call:', master_calls)
                # обновление данных
                print('Сообщение мастеру отправлено')
                if not ShiftTask.objects.filter(pk=task_id, st_status='ожидание мастера'):
                    ShiftTask.objects.filter(pk=task_id).update(st_status='ожидание мастера',
                                                                datetime_master_call=datetime.datetime.now(),
                                                                master_calls=master_calls + 1
                                                                )

                    return redirect(f'/worker/{ws_number}')  # обновление страницы



        else:
            print('Выберите ещё раз.')
            return redirect(f'/worker/{ws_number}')  # обновление страницы

    context = {'initial_shift_tasks': initial_shift_tasks,
               'ws_number': ws_number, 'select_shift_task': select_shift_task}

    # print(context)

    return render(request, r"worker/worker.html", context=context)

import datetime
from django.shortcuts import render, redirect
from .forms import SchedulerWorkshop, SchedulerWorkplace, FioDoer
from .models import WorkshopSchedule, ShiftTask
from tehnolog.models import TechData
from django.db.models import Q
from django.db.models import F


def scheduler(request):
    """
    Планирование графика цеха
    :param request:
    :return:
    """
    # выборка для графика цеха и списка заявок на чертежи
    # график
    workshop_schedule = (WorkshopSchedule.objects.values('workshop', 'order', 'model_name', 'datetime_done',
                                                         'order_status').filter(order_status='запланировано'))
    # перечень запросов на КД
    td_queries = WorkshopSchedule.objects.values('order', 'model_query', 'td_status').exclude(td_status='отработано')
    # TODO вернуть в шаблон сообщение об успехе!
    if request.method == 'POST':
        form_workshop_plan = SchedulerWorkshop(request.POST)
        if form_workshop_plan.is_valid():
            print(form_workshop_plan.cleaned_data)
            # заполнение модели графика цеха новыми данными при планировании если заполнено имя модели
            if form_workshop_plan.cleaned_data['model_name']:
                try:
                    # если не выбран цех
                    if form_workshop_plan.cleaned_data['workshop'] == '5':
                        form_workshop_plan.add_error(None, 'Не выбран цех.')
                        context = {'form_workshop_plan': form_workshop_plan, 'td_queries': td_queries}
                        return render(request, r"scheduler/scheduler.html", context=context)
                    if not (WorkshopSchedule.objects.filter(order=form_workshop_plan.cleaned_data['order'],
                                                            model_name=form_workshop_plan.cleaned_data['model_name'],
                                                            workshop=form_workshop_plan.cleaned_data['workshop'],
                                                            datetime_done=form_workshop_plan.cleaned_data[
                                                                'datetime_done']
                                                            ).exists()):
                        WorkshopSchedule.objects.create(order=form_workshop_plan.cleaned_data['order'],
                                                        model_name=form_workshop_plan.cleaned_data['model_name'],
                                                        workshop=form_workshop_plan.cleaned_data['workshop'],
                                                        datetime_done=form_workshop_plan
                                                        .cleaned_data['datetime_done'],
                                                        plan_datetime=datetime.datetime.now(),
                                                        )
                        print('Данные в график успешно занесены!')
                        formed_model_name = form_workshop_plan.cleaned_data['model_name']
                        # выборка по имени модели из модели TechData для заполнения ShiftTask
                        tech_data = TechData.objects.filter(model_name=formed_model_name)
                        # заполнение модели ShiftTask данными планирования цехов
                        for line in tech_data.values():
                            ShiftTask.objects.create(workshop=form_workshop_plan.cleaned_data['workshop'],
                                                     model_name=form_workshop_plan.cleaned_data['model_name'],
                                                     datetime_done=form_workshop_plan.cleaned_data['datetime_done'],
                                                     order=form_workshop_plan.cleaned_data['order'],
                                                     op_number=line['op_number'],
                                                     op_name=line['op_name'],
                                                     ws_name=line['ws_name'],
                                                     op_name_full=line['op_name_full'],
                                                     ws_number=line['ws_number'],
                                                     norm_tech=line['norm_tech'],
                                                     datetime_techdata_create=line['datetime_create'],
                                                     datetime_techdata_update=line['datetime_update'],
                                                     datetime_plan_wp=datetime.datetime.now()
                                                     )
                            print('Данные сменного задания успешно занесены!')
                        return redirect('scheduler')  # обновление страницы при успехе
                    else:
                        form_workshop_plan.add_error(None, 'Такой заказ уже запланирован!')
                        context = {'form_workshop_plan': form_workshop_plan, 'td_queries': td_queries}
                except Exception as e:
                    print(e, ' Ошибка запаси в базу SchedulerWorkshop')
            else:
                # TODO сделать запрос на КД
                # обработка заполнения поля запроса КД
                if not form_workshop_plan.cleaned_data['model_query']:
                    form_workshop_plan.add_error(None, 'Не заполнена модель запроса КД.')
                # если не выбран цех
                if form_workshop_plan.cleaned_data['workshop'] == '5':
                    form_workshop_plan.add_error(None, 'Не выбран цех.')
                    context = {'form_workshop_plan': form_workshop_plan, 'schedule': workshop_schedule,
                               'td_queries': td_queries}
                    return render(request, r"scheduler/scheduler.html", context=context)
                # if form_workshop_plan.cleaned_data['workshop'] != '5':
                if not (WorkshopSchedule.objects.filter(order=form_workshop_plan.cleaned_data['order'],
                                                        model_query=form_workshop_plan.cleaned_data
                                                        ['model_query'],
                                                        workshop=form_workshop_plan.cleaned_data[
                                                            'workshop']).exists()):
                    WorkshopSchedule.objects.create(order=form_workshop_plan.cleaned_data['order'],
                                                    model_query=form_workshop_plan.cleaned_data['model_query'],
                                                    workshop=form_workshop_plan.cleaned_data['workshop']
                                                    )
                    print('Заявка на КД сформирована')
                    return redirect('scheduler')  # обновление страницы при успехе
                context = {'form_workshop_plan': form_workshop_plan, 'schedule': workshop_schedule,
                           'td_queries': td_queries}

        else:
            context = {'form_workshop_plan': form_workshop_plan, 'schedule': workshop_schedule,
                       'td_queries': td_queries}

    else:
        # чистые формы для первого запуска
        form_workshop_plan = SchedulerWorkshop()
        context = {'form_workshop_plan': form_workshop_plan, 'schedule': workshop_schedule, 'td_queries': td_queries}
    return render(request, r"scheduler/scheduler.html", context=context)


def schedulerwp(request):
    """
    Планирование графика РЦ
    :param request:
    :return:
    """
    # отображение графика РЦ
    # выборка из уже занесенного
    workplace_schedule = ((
        ShiftTask.objects.values('id', 'workshop', 'order', 'model_name', 'datetime_done', 'ws_number',
                                 'op_number', 'op_name_full', 'norm_tech', 'fio_doer', 'st_status').all())
                          .order_by("ws_number", "model_name"))

    if request.method == 'POST':
        form_workplace_plan = SchedulerWorkplace(request.POST)
        if form_workplace_plan.is_valid():
            ws_number = form_workplace_plan.cleaned_data['ws_number'].ws_number
            datetime_done = form_workplace_plan.cleaned_data['datetime_done'].datetime_done
            print(ws_number, datetime_done)
            try:
                filtered_workplace_schedule = (ShiftTask.objects.values
                                               ('id', 'workshop', 'order', 'model_name', 'datetime_done', 'ws_number',
                                                'op_number', 'op_name_full', 'norm_tech', 'fio_doer', 'st_status').
                                               filter(ws_number=str(ws_number), datetime_done=datetime_done)
                                               .filter(Q(fio_doer='не распределено') | Q(st_status='брак')
                                                       | Q(st_status='не принято'))
                                               )
            except Exception as e:
                filtered_workplace_schedule = dict()
                print('Ошибка получения filtered_workplace_schedule', e)
            if filtered_workplace_schedule:
                return redirect(f'/scheduler/schedulerfio{ws_number}_{datetime_done}')
            else:
                alert_message = f'Для РЦ {ws_number} на {datetime_done} нераспределённые задания отсутствуют.'
                form_workplace_plan = SchedulerWorkplace()
                context = {'workplace_schedule': workplace_schedule, 'form_workplace_plan': form_workplace_plan,
                           'alert_message': alert_message}
                return render(request, fr"schedulerwp/schedulerwp.html", context=context)
    else:
        form_workplace_plan = SchedulerWorkplace()
        context = {'workplace_schedule': workplace_schedule, 'form_workplace_plan': form_workplace_plan}
        return render(request, fr"schedulerwp/schedulerwp.html", context=context)
        # return redirect(f'/scheduler/schedulerwp')


def schedulerfio(request, ws_number, datetime_done):
    """
    Распределение ФИО на РЦ
    :param datetime_done:
    :param ws_number:
    :param request:
    :return:
    """

    def if_not_none(obj):  # функция замены None и НЕТ на пустоту в списке сиполнителей
        if obj is None or obj == 'НЕТ':
            return ''
        else:
            return ',' + str(obj)

    print(ws_number)
    print(datetime_done)
    formatted_datetime_done = datetime.datetime.strptime(datetime_done, '%Y-%m-%d')
    # определения рабочего центра и id
    try:
        filtered_workplace_schedule = (ShiftTask.objects.values
                                       ('id', 'workshop', 'order', 'model_name', 'datetime_done', 'ws_number',
                                        'op_number', 'op_name_full', 'norm_tech', 'fio_doer', 'st_status').
                                       filter(ws_number=str(ws_number), datetime_done=formatted_datetime_done)
                                       .filter(Q(fio_doer='не распределено') | Q(st_status='брак')
                                               | Q(st_status='не принято'))
                                       )
    except Exception as e:
        filtered_workplace_schedule = dict()
        print('Ошибка получения filtered_workplace_schedule', e)
    if request.method == 'POST':
        form_fio_doer = FioDoer(request.POST, ws_number=ws_number, datetime_done=formatted_datetime_done)
        if form_fio_doer.is_valid():
            doers_fios = (str(form_fio_doer.cleaned_data['fio_1']) +
                          if_not_none(str((form_fio_doer.cleaned_data['fio_2'])).strip()) +
                          if_not_none(str(form_fio_doer.cleaned_data['fio_3'])).strip() +
                          if_not_none(str(form_fio_doer.cleaned_data['fio_4'])).strip())
            print('DOERS-', doers_fios)
            (ShiftTask.objects.filter(pk=form_fio_doer.cleaned_data['st_number'].id).update(
                fio_doer=doers_fios, datetime_assign_wp=datetime.datetime.now(), st_status='запланировано',
                datetime_job_start=None, decision_time=None))
            alert_message = f'Успешно распределено!'
            context = {'filtered_workplace_schedule': filtered_workplace_schedule,
                       'form_fio_doer': form_fio_doer,
                       'alert_message': alert_message}
            return render(request, r"schedulerfio/schedulerfio.html", context=context)
    else:
        alert_message = ''
        form_fio_doer = FioDoer(ws_number=ws_number, datetime_done=formatted_datetime_done)
        context = {'filtered_workplace_schedule': filtered_workplace_schedule,
                   'form_fio_doer': form_fio_doer,
                   'alert_message': alert_message}
        return render(request, r"schedulerfio/schedulerfio.html", context=context)

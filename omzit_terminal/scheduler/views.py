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

    def if_not_none(obj):
        if obj is None:
            return ''
        else:
            return ',' + str(obj)

    # отображение графика РЦ
    # выборка из уже занесенного
    workplace_schedule = (
        ShiftTask.objects.values('id', 'workshop', 'order', 'model_name', 'datetime_done', 'ws_number',
                                 'op_number', 'op_name_full', 'norm_tech', 'fio_doer', 'st_status').all())

    if request.method == 'POST':
        form_workplace_plan = SchedulerWorkplace(request.POST)
        if form_workplace_plan.is_valid():
            # вывод отфильтрованного графика с бракованными и непринятыми для перезапуска
            # определения рабочего центра и id
            try:
                filtered_workplace_schedule = (ShiftTask.objects.values
                                               ('id', 'workshop', 'order', 'model_name', 'datetime_done', 'ws_number',
                                                'op_number', 'op_name_full', 'norm_tech', 'fio_doer', 'st_status').
                                               filter(ws_number=form_workplace_plan.cleaned_data['ws_number'].ws_number,
                                                      datetime_done=form_workplace_plan.cleaned_data[
                                                          'datetime_done'].datetime_done)
                                               .filter(Q(fio_doer='не распределено') | Q(st_status='брак')
                                                       | Q(st_status='не принято'))
                                               )
            except Exception as e:
                filtered_workplace_schedule = dict()
                print(e)
            # Вывод формы для заполнения ФИО
            form_fio_doer = FioDoer(request.POST)
            # обновление данных
            if form_fio_doer.is_valid():
                print(form_fio_doer.cleaned_data)
                print(form_fio_doer.cleaned_data['st_number'])
                doers_fios = (str(form_fio_doer.cleaned_data['fio_1']) +
                              if_not_none((form_fio_doer.cleaned_data['fio_2'])) +
                              if_not_none(form_fio_doer.cleaned_data['fio_3']) +
                              if_not_none(form_fio_doer.cleaned_data['fio_4']))
                print(doers_fios)
                (ShiftTask.objects.filter(pk=form_fio_doer.cleaned_data['st_number'].id).update(
                    fio_doer=doers_fios, datetime_assign_wp=datetime.datetime.now(), st_status='запланировано',
                    datetime_job_start=None, decision_time=None))
                print('Распределено!')
            # (ShiftTask.objects.filter(ws_number=form_workplace_plan.cleaned_data['ws_number'],
            #                           datetime_done=str(form_workplace_plan.cleaned_data['datetime_done']))
            #  .update(fio_doer=form_fio_doer.cleaned_data['fio_doer']))

            context = {'form_workplace_plan': form_workplace_plan,
                       'filtered_workplace_schedule': filtered_workplace_schedule,
                       'form_fio_doer': form_fio_doer}
            # TODO сделать редирект на success! либо дать JS alert
            return render(request, r"schedulerwp/schedulerwp.html",
                          context=context)
    else:
        # чистые форма для первого запуска
        form_workplace_plan = SchedulerWorkplace({'ws_number': 105})
        context = {'form_workplace_plan': form_workplace_plan, 'workplace_schedule': workplace_schedule}
    context = {'form_workplace_plan': form_workplace_plan, 'workplace_schedule': workplace_schedule}
    return render(request, r"schedulerwp/schedulerwp.html", context=context)

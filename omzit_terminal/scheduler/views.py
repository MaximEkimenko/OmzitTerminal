from django.shortcuts import render, redirect
from .forms import SchedulerWorkshop, SchedulerWorkplace
from .models import WorkshopSchedule, ShiftTask
from tehnolog.models import TechData


def scheduler(request):
    """
    Планирование графика цеха
    :param request:
    :return:
    """
    # отображение графика цеха
    workshop_schedule = WorkshopSchedule.objects.values('workshop', 'order', 'model_name',  # выборка из уже занесенного
                                                        'datetime_done', 'order_status')
    if request.method == 'POST':
        form_workshop_plan = SchedulerWorkshop(request.POST)
        if form_workshop_plan.is_valid():
            # заполнение модели графика цеха новыми данными
            try:
                if not (WorkshopSchedule.objects.filter(order=form_workshop_plan.cleaned_data['order'],
                                                        model_name=form_workshop_plan.cleaned_data['model_name'],
                                                        workshop=form_workshop_plan.cleaned_data['workshop'],
                                                        datetime_done=form_workshop_plan.cleaned_data['datetime_done']
                                                        ).exists()):
                    WorkshopSchedule.objects.create(order=form_workshop_plan.cleaned_data['order'],
                                                    model_name=form_workshop_plan.cleaned_data['model_name'],
                                                    workshop=form_workshop_plan.cleaned_data['workshop'],
                                                    datetime_done=form_workshop_plan.cleaned_data['datetime_done'])
                    print('Данные в график успешно занесены!')
                    # переменные для передачи в базу # TODO если не пригодятся - удалить!
                    formed_workshop = form_workshop_plan.cleaned_data['workshop']
                    formed_model_name = form_workshop_plan.cleaned_data['model_name']
                    formed_datetime_done = form_workshop_plan.cleaned_data['datetime_done']
                    formed_order = form_workshop_plan.cleaned_data['order']
                    # выборка по имени модели из модели TechData для заполнения ShiftTask
                    tech_data = TechData.objects.filter(model_name=formed_model_name)
                    # заполнение модели ShiftTask данными планирования цехов
                    for line in tech_data.values():
                        ShiftTask.objects.create(workshop=formed_workshop,
                                                 model_name=formed_model_name,
                                                 datetime_done=formed_datetime_done,
                                                 order=formed_order,
                                                 op_number=line['op_number'],
                                                 op_name=line['op_name'],
                                                 ws_name=line['ws_name'],
                                                 op_name_full=line['op_name_full'],
                                                 ws_number=line['ws_number'],
                                                 norm_tech=line['norm_tech'],
                                                 datetime_techdata_create=line['datetime_create'],
                                                 datetime_techdata_update=line['datetime_update']
                                                 )
                        print('Данные сменные задания успешно занесены!')
                    return redirect('scheduler')  # обновление страницы при успехе TODO сделать сообщение об успехе!
                else:
                    form_workshop_plan.add_error(None, 'Такой заказ уже запланирован!')
                    context = {'form_workshop_plan': form_workshop_plan}

            except Exception as e:
                print(e, ' Ошибка запаси в базу SchedulerWorkshop')
        else:
            context = {'form_workshop_plan': form_workshop_plan, 'schedule': workshop_schedule}
        # отображение формы планирования РЦ
        form_workplace_plan = SchedulerWorkplace(request.POST)
        if form_workplace_plan.is_valid():
            print(form_workplace_plan.cleaned_data)





    else:
        # чистые форма для первого запуска
        form_workshop_plan = SchedulerWorkshop()
        form_workplace_plan = SchedulerWorkplace()
        context = {'form_workshop_plan': form_workshop_plan, 'form_workplace_plan': form_workplace_plan,
                   'schedule': workshop_schedule}
    return render(request, r"scheduler/scheduler.html", context=context)


def schedulerwp(request):
    """
    Планирование графика РЦ
    :param request:
    :return:
    """
    if request.method == 'POST':
        form_workplace_plan = SchedulerWorkplace(request.POST)
        if form_workplace_plan.is_valid():
            print(form_workplace_plan.cleaned_data)


    else:
        # чистые форма для первого запуска
        form_workplace_plan = SchedulerWorkplace()
        context = {'form_workplace_plan': form_workplace_plan}
    return render(request, r"schedulerwp/schedulerwp.html", context=context)

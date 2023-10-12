import asyncio
import datetime
import os

from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.contrib.auth.forms import AuthenticationForm

from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.db.models import Q

from .forms import SchedulerWorkshop, SchedulerWorkplace, FioDoer, QueryDraw
from .models import WorkshopSchedule, ShiftTask

from .services.schedule_handlers import get_all_done_rate
from worker.services.master_call_function import terminal_message_to_id


@login_required(login_url="login/")
def scheduler(request):
    """
    Планирование графика цеха и создание запросов на КД
    :param request:
    :return:
    """
    group_id = -908012934  # тг группа
    # обновление процента готовности всех заказов
    # TODO модифицировать расчёт процента готовности всех заказов по взвешенной трудоёмкости
    get_all_done_rate()
    # график изделий
    workshop_schedule = (WorkshopSchedule.objects.values('workshop', 'order', 'model_name', 'datetime_done',
                                                         'order_status', 'done_rate')
                         .exclude(datetime_done=None).exclude(order_status='не запланировано')
                         .order_by('datetime_done'))
    # перечень запросов на КД
    td_queries = WorkshopSchedule.objects.values('model_order_query', 'query_prior', 'td_status').exclude(
        td_status='отработано')
    # форма запроса КД
    form_query_draw = QueryDraw()
    if request.method == 'POST':
        form_workshop_plan = SchedulerWorkshop(request.POST)
        if form_workshop_plan.is_valid():
            print(form_workshop_plan.cleaned_data)
            # заполнение графика цеха датой готовности и цехом
            try:
                # если не выбран цех
                if form_workshop_plan.cleaned_data['workshop'] == '5':
                    form_workshop_plan.add_error(None, 'Не выбран цех.')
                    context = {'form_workshop_plan': form_workshop_plan, 'td_queries': td_queries}
                    return render(request, r"scheduler/scheduler.html", context=context)
                # Планирование графика цеха
                # срок готовности, категория изделия, статус изделия, ФИО планировщика
                (WorkshopSchedule.objects.filter(model_order_query=form_workshop_plan.
                                                 cleaned_data['model_order_query'].model_order_query).update(
                    datetime_done=form_workshop_plan.cleaned_data['datetime_done'],
                    workshop=form_workshop_plan.cleaned_data['workshop'],
                    product_category=str(form_workshop_plan.cleaned_data['category']),
                    order_status='запланировано',
                    dispatcher_plan_ws_fio=f'{request.user.first_name} {request.user.last_name}'
                ))
                # Заполнение данных СЗ,
                # статус СЗ, ФИО планировщика, категория изделия,
                alert = 'Данные в график успешно занесены! '
                print('Данные в график успешно занесены!\n')
                # заполнение модели ShiftTask данными планирования цехов
                (ShiftTask.objects.filter(
                    model_order_query=form_workshop_plan.cleaned_data['model_order_query'].model_order_query)
                 .update(workshop=form_workshop_plan.cleaned_data['workshop'],
                         datetime_done=form_workshop_plan.cleaned_data['datetime_done'],
                         product_category=str(form_workshop_plan.cleaned_data['category'])
                         ))
                print('Данные сменного задания успешно занесены!')
                alert += 'Данные сменного задания успешно занесены.'
                context = {'form_workshop_plan': form_workshop_plan, 'td_queries': td_queries, 'alert': alert,
                           'workshop_schedule': workshop_schedule, 'form_query_draw': form_query_draw}
                # сообщение в группу
                success_group_message = (f"Заказ-модель: "
                                         f"{form_workshop_plan.cleaned_data['model_order_query'].model_order_query} "
                                         f"успешно запланирован на {form_workshop_plan.cleaned_data['datetime_done']}. "
                                         f"Запланировал: {request.user.first_name} {request.user.last_name}.")
                asyncio.run(terminal_message_to_id(to_id=group_id, text_message_to_id=success_group_message))
            except Exception as e:
                print(e, ' Ошибка запаси в базу SchedulerWorkshop')
                alert = f'Ошибка занесения данных.'
                context = {'form_workshop_plan': form_workshop_plan, 'workshop_schedule': workshop_schedule,
                           'td_queries': td_queries, 'form_query_draw': form_query_draw, 'alert': alert}
                return render(request, r"scheduler/scheduler.html", context=context)
        else:
            context = {'form_workshop_plan': form_workshop_plan, 'workshop_schedule': workshop_schedule,
                       'td_queries': td_queries, 'form_query_draw': form_query_draw}
    else:
        # чистые формы для первого запуска
        form_workshop_plan = SchedulerWorkshop()
        context = {'form_workshop_plan': form_workshop_plan, 'workshop_schedule': workshop_schedule,
                   'td_queries': td_queries, 'form_query_draw': form_query_draw}
    return render(request, r"scheduler/scheduler.html", context=context)


@login_required(login_url="login/")
def td_query(request):
    """
    Обработка формы запросы чертежей
    :param request:
    :return:
    """
    group_id = -908012934  # тг группа
    if request.method == 'POST':
        form_query_draw = QueryDraw(request.POST)
        if form_query_draw.is_valid():
            # модель_заказ
            model_order_query = (f"{form_query_draw.cleaned_data['order_query'].strip()}_"
                                 f"{form_query_draw.cleaned_data['model_query'].strip()}")
            # заполнение графика цеха данными запроса на чертеж
            if not (WorkshopSchedule.objects.filter(order=form_query_draw.cleaned_data['order_query'].strip(),
                                                    model_order_query=model_order_query,
                                                    query_prior=form_query_draw.cleaned_data
                                                    ['query_prior'],
                                                    model_name=form_query_draw.cleaned_data
                                                    ['model_query'].strip()).exists()):
                WorkshopSchedule.objects.create(order=form_query_draw.cleaned_data['order_query'].strip(),
                                                model_order_query=model_order_query,
                                                query_prior=form_query_draw.cleaned_data
                                                ['query_prior'],
                                                model_name=form_query_draw.cleaned_data
                                                ['model_query'].strip(),
                                                td_status="запрошено",
                                                dispatcher_query_td_fio=f"{request.user.first_name} "
                                                                        f"{request.user.last_name}")

                # сообщение об успехе для отправки в группу
                success_group_message = (f"Поступила заявка на КД. Изделие: "
                                         f"{form_query_draw.cleaned_data['model_query']}. Заказ:  "
                                         f"{form_query_draw.cleaned_data['order_query']}. Приоритет: "
                                         f"{form_query_draw.cleaned_data['query_prior']}. "
                                         f"Заявку составил: {request.user.first_name} {request.user.last_name}.")
                asyncio.run(terminal_message_to_id(to_id=group_id, text_message_to_id=success_group_message))
                # создание папки в общем доступе для чертежей модели
                if not os.path.exists(rf'C:\draws\{model_order_query}'):
                    os.mkdir(rf'C:\draws\{model_order_query}')
        else:
            pass

    return redirect('scheduler')  # обновление страницы при успехе


@login_required(login_url="login/")
def schedulerwp(request):
    """
    Планирование графика РЦ
    :param request:
    :return:
    """
    # отображение графика РЦ
    # выборка из уже занесенного
    workplace_schedule = ((ShiftTask.objects.values('id', 'workshop', 'order', 'model_name', 'datetime_done',
                                                    'ws_number', 'op_number', 'op_name_full', 'norm_tech', 'fio_doer',
                                                    'st_status').all()).exclude(datetime_done=None)
                          .order_by("ws_number", "model_name",))

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
                alert_message = f'Для Т{ws_number} на {datetime_done} нераспределённые задания отсутствуют.'
                form_workplace_plan = SchedulerWorkplace()
                context = {'workplace_schedule': workplace_schedule, 'form_workplace_plan': form_workplace_plan,
                           'alert_message': alert_message}
                return render(request, fr"schedulerwp/schedulerwp.html", context=context)
    else:
        form_workplace_plan = SchedulerWorkplace()
        context = {'workplace_schedule': workplace_schedule, 'form_workplace_plan': form_workplace_plan}
        return render(request, fr"schedulerwp/schedulerwp.html", context=context)


@login_required(login_url="login/")
def schedulerfio(request, ws_number, datetime_done):
    """
    Распределение ФИО на РЦ
    :param datetime_done:
    :param ws_number:
    :param request:
    :return:
    """
    def if_not_none(obj):  # функция замены None и НЕТ на пустоту в списке исполнителей
        if obj is None or obj == '' or obj == 'None':
            return ''
        else:
            return ',' + str(obj)
    print(ws_number)
    print(datetime_done)
    formatted_datetime_done = datetime.datetime.strptime(datetime_done, '%Y-%m-%d')
    # определения рабочего центра и id
    if not request.user.username:  # если не авторизован, то отправляется на авторизацию
        return redirect('login/')
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
                datetime_job_start=None, decision_time=None, master_assign_wp_fio=f'{request.user.first_name} '
                                                                                  f'{request.user.last_name}'))
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


# авторизация пользователей
class LoginUser(LoginView):
    form_class = AuthenticationForm
    template_name = 'scheduler/login.html'

    def get_success_url(self):  # редирект после логина
        if 'admin' in self.request.user.username:
            return reverse_lazy('home')
        elif 'disp' in self.request.user.username:
            return reverse_lazy('scheduler')
        elif 'tehnolog' in self.request.user.username:
            return reverse_lazy('tehnolog')
        elif 'constructor' in self.request.user.username:
            return reverse_lazy('constructor')
        print(self.request.user.username)


def logout_user(request):  # разлогинивание пользователя
    logout(request)
    return redirect('login')

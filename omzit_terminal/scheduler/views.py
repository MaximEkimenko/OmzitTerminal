import asyncio
import datetime
import os
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.contrib.auth.forms import AuthenticationForm
from django.core.exceptions import PermissionDenied
from django.http import FileResponse

from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.db.models import Q

from .filters import get_filterset
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
    if str(request.user.username).strip()[:5] != "admin" and str(request.user.username[:4]).strip() != "disp":
        raise PermissionDenied
    group_id = -908012934  # тг группа

    # обновление процента готовности всех заказов
    # TODO модифицировать расчёт процента готовности всех заказов по взвешенной трудоёмкости
    #  сделать невозможным заполнять запрос с кириллицей
    get_all_done_rate()
    # график изделий
    workshop_schedule_fields = ('workshop', 'order', 'model_name', 'datetime_done', 'order_status', 'done_rate')
    workshop_schedule = (WorkshopSchedule.objects.values(*workshop_schedule_fields)
                         .exclude(datetime_done=None).exclude(order_status='не запланировано')
                         .order_by('datetime_done'))
    # фильтры в колонки графика
    f_w = get_filterset(data=request.GET, queryset=workshop_schedule, fields=workshop_schedule_fields, index=1)
    # перечень запросов на КД
    td_queries_fields = ('model_order_query', 'query_prior', 'td_status')  # поля таблицы
    td_queries = (WorkshopSchedule.objects.values(*td_queries_fields).exclude(td_status='завершено'))
    # фильтры в колонки заявок
    # f_q = get_filterset_second_table(data=request.GET, queryset=td_queries, fields=td_queries_fields)
    f_q = get_filterset(data=request.GET, queryset=td_queries, fields=td_queries_fields, index=2)

    # форма запроса КД
    form_query_draw = QueryDraw()
    if request.method == 'POST':
        form_workshop_plan = SchedulerWorkshop(request.POST)
        if form_workshop_plan.is_valid():
            print(form_workshop_plan.cleaned_data)
            # заполнение графика цеха датой готовности и цехом
            try:
                # Планирование графика цеха
                # заполнение срока готовности, категория изделия, статус изделия, ФИО планировщика
                (WorkshopSchedule.objects.filter(model_order_query=form_workshop_plan.
                                                 cleaned_data['model_order_query'].model_order_query).update(
                    datetime_done=form_workshop_plan.cleaned_data['datetime_done'],
                    workshop=form_workshop_plan.cleaned_data['workshop'],
                    product_category=str(form_workshop_plan.cleaned_data['category']),
                    order_status='запланировано',
                    dispatcher_plan_ws_fio=f'{request.user.first_name} {request.user.last_name}'))
                # Заполнение данных СЗ, статус СЗ, ФИО планировщика, категория изделия,
                alert = 'Данные в график успешно занесены! '
                print('Данные в график успешно занесены!\n')
                # заполнение модели ShiftTask данными планирования цехов
                print(ShiftTask.objects.filter(model_order_query=form_workshop_plan.cleaned_data['model_order_query']))
                (ShiftTask.objects.filter(
                    model_order_query=form_workshop_plan.cleaned_data['model_order_query'].model_order_query)
                 .update(workshop=form_workshop_plan.cleaned_data['workshop'],
                         datetime_done=form_workshop_plan.cleaned_data['datetime_done'],
                         product_category=str(form_workshop_plan.cleaned_data['category']),
                         ))
                print('Данные сменного задания успешно занесены!')
                alert += 'Данные сменного задания успешно занесены.'
                context = {'form_workshop_plan': form_workshop_plan, 'td_queries': td_queries, 'alert': alert,
                           'workshop_schedule': workshop_schedule, 'form_query_draw': form_query_draw,
                           'filter_w': f_w, 'filter_q': f_q}
                # сообщение в группу
                success_group_message = (f"Заказ-модель: "
                                         f"{form_workshop_plan.cleaned_data['model_order_query'].model_order_query} "
                                         f"успешно запланирован на {form_workshop_plan.cleaned_data['datetime_done']}. "
                                         f"Запланировал: {request.user.first_name} {request.user.last_name}.")
                # asyncio.run(terminal_message_to_id(to_id=group_id, text_message_to_id=success_group_message))
            except Exception as e:
                print(e, ' Ошибка запаси в базу SchedulerWorkshop')
                alert = f'Ошибка занесения данных.'
                context = {'form_workshop_plan': form_workshop_plan, 'workshop_schedule': workshop_schedule,
                           'td_queries': td_queries, 'form_query_draw': form_query_draw, 'alert': alert,
                           'filter_w': f_w, 'filter_q': f_q}
                return render(request, r"scheduler/scheduler.html", context=context)
        else:
            context = {'form_workshop_plan': form_workshop_plan, 'workshop_schedule': workshop_schedule,
                       'td_queries': td_queries, 'form_query_draw': form_query_draw,
                       'filter_w': f_w, 'filter_q': f_q}
    else:
        # чистые формы для первого запуска
        form_workshop_plan = SchedulerWorkshop()
        context = {'form_workshop_plan': form_workshop_plan, 'workshop_schedule': workshop_schedule,
                   'td_queries': td_queries, 'form_query_draw': form_query_draw,
                   'filter_w': f_w, 'filter_q': f_q}
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
    if str(request.user.username).strip()[:5] != "admin" and str(request.user.username[:4]).strip() != "disp":
        raise PermissionDenied
    shift_task_fields = (
        'id',
        'workshop',
        'order',
        'model_name',
        'datetime_done',
        'ws_number',
        'op_number',
        'op_name_full',
        'norm_tech',
        'fio_doer',
        'st_status'
    )
    workplace_schedule = (ShiftTask.objects.values(*shift_task_fields).all().exclude(datetime_done=None)
                          .order_by("ws_number", "model_name", ))
    f = get_filterset(data=request.GET, queryset=workplace_schedule, fields=shift_task_fields)
    alert_message = ''
    if request.method == 'POST':
        form_workplace_plan = SchedulerWorkplace(request.POST)
        if form_workplace_plan.is_valid():
            ws_number = form_workplace_plan.cleaned_data['ws_number'].ws_number
            datetime_done = form_workplace_plan.cleaned_data['datetime_done'].datetime_done
            print(ws_number, datetime_done)
            try:
                filtered_workplace_schedule = (
                    ShiftTask.objects.values(*shift_task_fields)
                    .filter(ws_number=str(ws_number), datetime_done=datetime_done)
                    .filter(Q(fio_doer='не распределено') | Q(st_status='брак') | Q(st_status='не принято'))
                )
            except Exception as e:
                filtered_workplace_schedule = dict()
                print('Ошибка получения filtered_workplace_schedule', e)
            if filtered_workplace_schedule:
                return redirect(f'/scheduler/schedulerfio{ws_number}_{datetime_done}')
            else:
                alert_message = f'Для Т{ws_number} на {datetime_done} нераспределённые задания отсутствуют.'
                form_workplace_plan = SchedulerWorkplace()
    else:
        form_workplace_plan = SchedulerWorkplace()
    context = {
        'workplace_schedule': workplace_schedule,
        'form_workplace_plan': form_workplace_plan,
        'alert_message': alert_message,
        'filter': f
    }
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
    if str(request.user.username).strip() != "admin" and str(request.user.username[:4]).strip() != "disp":
        raise PermissionDenied

    print(ws_number)
    print(datetime_done)
    shift_task_fields = (
        'id', 'workshop', 'order', 'model_name', 'datetime_done', 'ws_number',
        'op_number', 'op_name_full', 'norm_tech', 'fio_doer', 'st_status'
    )
    formatted_datetime_done = datetime.datetime.strptime(datetime_done, '%Y-%m-%d')
    # определения рабочего центра и id
    if not request.user.username:  # если не авторизован, то отправляется на авторизацию
        return redirect('login/')
    try:
        filtered_workplace_schedule = (
            ShiftTask.objects.values(*shift_task_fields)
            .filter(ws_number=str(ws_number), datetime_done=formatted_datetime_done)
            .filter(Q(fio_doer='не распределено') | Q(st_status='брак') | Q(st_status='не принято'))
        )
        f = get_filterset(data=request.GET, queryset=filtered_workplace_schedule, fields=shift_task_fields)
    except Exception as e:
        filtered_workplace_schedule = dict()
        print('Ошибка получения filtered_workplace_schedule', e)

    success = 1
    alert_message = ''

    if request.method == 'POST':
        print('POST')
        form_fio_doer = FioDoer(request.POST, ws_number=ws_number, datetime_done=formatted_datetime_done)
        if form_fio_doer.is_valid():
            # Получение списка без None
            fios = list(filter(
                lambda x: x != 'None',
                (str(form_fio_doer.cleaned_data[f'fio_{i}']) for i in range(1, 5))
            ))
            unique_fios = set(fios)
            doers_fios = ', '.join(unique_fios)  # получение уникального списка
            print('DOERS-', doers_fios)
            if len(fios) == len(unique_fios):  # если есть повторения в списке fios
                (ShiftTask.objects.filter(pk=form_fio_doer.cleaned_data['st_number'].id).update(
                    fio_doer=doers_fios, datetime_assign_wp=datetime.datetime.now(), st_status='запланировано',
                    datetime_job_start=None, decision_time=None, master_assign_wp_fio=f'{request.user.first_name} '
                                                                                      f'{request.user.last_name}'))
                alert_message = f'Успешно распределено!'
            else:
                alert_message = f'Исполнители дублируются. Измените исполнителей.'
                success = 0
    else:
        form_fio_doer = FioDoer(ws_number=ws_number, datetime_done=formatted_datetime_done)

    context = {
        'filtered_workplace_schedule': filtered_workplace_schedule,
        'form_fio_doer': form_fio_doer,
        'alert_message': alert_message,
        'success': success,
        'filter': f,
    }
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


def show_workshop_scheme(request):
    """
    Загрузка планировки
    :param request:
    :return:
    """
    try:
        path_to_file = r"O:\ПТО\1 Екименко М.А\Планировка\Планирока участков(цех1, цех2, цех3)+РЦ+Расписание+Виды.xlsm"
        response = FileResponse(open(fr'{path_to_file}', 'rb'))
        response['X-Frame-Options'] = 'SAMEORIGIN'
        return response
    except FileNotFoundError as e:
        print(e)

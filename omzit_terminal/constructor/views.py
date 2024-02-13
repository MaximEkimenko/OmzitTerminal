import os
import asyncio
import datetime
from django.http import FileResponse
from tehnolog.services.service_handlers import handle_uploaded_file
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from scheduler.models import WorkshopSchedule
from .forms import QueryAnswer
from worker.services.master_call_function import terminal_message_to_id
from django.core.exceptions import PermissionDenied
from scheduler.filters import get_filterset
# ADMIN_TELEGRAM_ID
TERMINAL_GROUP_ID = os.getenv('ADMIN_TELEGRAM_ID')

# TODO ЗАКОНСЕРВИРОВАНО Функционал простоев
# from scheduler.models import Downtime


@login_required(login_url="../scheduler/login/")
def constructor(request):
    if str(request.user.username).strip()[:5] != "admin" and str(request.user.username[:11]).strip() != "constructor":
        raise PermissionDenied
    group_id = TERMINAL_GROUP_ID  # тг группа
    td_queries_fields = ('model_order_query', 'query_prior', 'td_status', 'td_remarks', 'datetime_done',
                         'td_query_datetime')  # поля таблицы
    td_queries = (WorkshopSchedule.objects.values(*td_queries_fields).exclude(td_status='завершено'))
    f = get_filterset(data=request.GET, queryset=td_queries, fields=td_queries_fields)  # фильтры в колонки
    query_answer_form = QueryAnswer()
    if request.method == 'POST':
        alert = ''
        query_answer_form = QueryAnswer(request.POST, request.FILES)
        if query_answer_form.is_valid():
            print(query_answer_form.cleaned_data)
            filenames = dict(request.FILES)["draw_files"]  # имя файла
            print(filenames)
            i = 0
            for file in filenames:
                i += 1
                print('-----', str(file))
                # TODO плавающий баг при загрузке чертежей
                order_path = query_answer_form.cleaned_data['model_order_query'].model_order_query
                file_save_path = rf"C:\draws\{order_path}\\"
                # обработчик загрузки файла
                try:
                    handle_uploaded_file(f=file, filename=str(file),
                                         path=file_save_path)
                    alert = 'Все файлы успешно загружены.'
                    success_message = True
                except Exception as e:
                    print(f'Ошибка загрузки {str(file)}', e)
                    alert = f'Ошибка загрузки {str(file)}.'
                    success_message = False

                # обновление данных в БД
                WorkshopSchedule.objects.filter(model_order_query=query_answer_form.
                                                cleaned_data['model_order_query'].model_order_query).update(
                    td_status='передано',  # статус СЗ
                    td_const_done_datetime=datetime.datetime.now(),  # время загрузки
                    constructor_query_td_fio=f'{request.user.first_name} {request.user.last_name}',  # ФИО констр
                    td_remarks='')

            if success_message:
                success_group_message = (f"Передано КД. Заказ-модель "
                                         f"{query_answer_form.cleaned_data['model_order_query'].model_order_query}. "
                                         f"Открыт доступ в папке сервера: file://svr-003/draws/"
                                         f"{query_answer_form.cleaned_data['model_order_query'].model_order_query}/. "
                                         f"Передал КД: {request.user.first_name} {request.user.last_name}. "
                                         f"Загружено файлов: {i}.")
                asyncio.run(terminal_message_to_id(to_id=group_id, text_message_to_id=success_group_message))

            context = {'filter': f, 'query_answer_form': query_answer_form, 'alert': alert}
            return render(request, r"constructor/constructor.html", context=context)
        else:
            print('INVALID FORM!')
            alert = 'invalid form'
            context = {'filter': f, 'query_answer_form': query_answer_form, 'alert': alert}
            return render(request, r"constructor/constructor.html", context=context)

    context = {'query_answer_form': query_answer_form, 'filter': f}
    # TODO ЗАКОНСЕРВИРОВАНО Функционал простоев
    # downtimes = Downtime.objects.filter(
    #     status='подтверждено', reason='Вызов конструктора').select_related('shift_task')
    # context['downtimes'] = downtimes
    return render(request, r"constructor/constructor.html", context=context)


def show_instruction(request):
    try:
        path_to_file = r"M:\Xranenie\ПТО\1 Екименко М.А\Инструкции\Инструкция ТЕРМИНАЛА.pdf"
        response = FileResponse(open(fr'{path_to_file}', 'rb'))
        response['X-Frame-Options'] = 'SAMEORIGIN'
        return response
    except FileNotFoundError as e:
        print(e)


def draw_folder_redirect(request):
    NotImplemented

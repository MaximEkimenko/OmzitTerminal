import asyncio
import datetime
import os

from django.http import HttpResponseRedirect
from django.urls import reverse
from tehnolog.services.service_handlers import handle_uploaded_file
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from scheduler.models import WorkshopSchedule
from .forms import QueryAnswer
from worker.services.master_call_function import terminal_message_to_id


@login_required(login_url="../scheduler/login/")
def constructor(request):
    group_id = -908012934  # тг группа
    td_queries = (WorkshopSchedule.objects.values('model_order_query', 'query_prior', 'td_status', 'td_remarks')
                  .exclude(td_status='завершено'))

    query_answer_form = QueryAnswer()
    if request.method == 'POST':
        alert = ''
        query_answer_form = QueryAnswer(request.POST, request.FILES)
        if query_answer_form.is_valid():
            print(query_answer_form.cleaned_data)
            filenames = dict(request.FILES)["draw_files"]  # имя файла
            print(filenames)
            for file in filenames:
                print('-----', str(file))
                # TODO убрать проверку pdf
                # if '.pdf' not in str(file):
                #     alert = f'{str(file)} файл должен быть .pdf!'
                #     print(alert)
                #     query_answer_form.add_error(None, alert)
                #     # Перезагрузка с alert
                #     return render(request, r"constructor/constructor.html",
                #                   {'query_answer_form': query_answer_form, 'alert': alert})

                order_path = query_answer_form.cleaned_data['model_order_query'].model_order_query
                file_save_path = rf"C:\draws\{order_path}\\"
                print(file_save_path)
                # обработчик загрузки файла
                try:
                    handle_uploaded_file(f=file, filename=str(file),
                                         path=file_save_path)
                    print('!!!!req====', file)
                    alert = 'Все файлы успешно загружены.'
                except Exception as e:
                    print(f'Ошибка загрузки {str(file)}', e)
                    alert = f'Ошибка загрузки {str(file)}.'

                # обновление данных в БД
                WorkshopSchedule.objects.filter(model_order_query=query_answer_form.
                                                cleaned_data['model_order_query'].model_order_query).update(
                    td_status='передано',  # статус СЗ
                    td_const_done_datetime=datetime.datetime.now(),  # время загрузки
                    constructor_query_td_fio=f'{request.user.first_name} {request.user.last_name}',  # ФИО констр
                    td_remarks='')
                success_message = True

            if success_message:
                success_group_message = (f"Передано КД. Заказ-модель "
                                         f"{query_answer_form.cleaned_data['model_order_query'].model_order_query}. "
                                         f"Открыт доступ в папке сервера: file://svr-003/draws/"
                                         f"{query_answer_form.cleaned_data['model_order_query'].model_order_query}/."
                                         f"Передал КД: {request.user.first_name} {request.user.last_name}."
                                         )
                asyncio.run(terminal_message_to_id(to_id=group_id, text_message_to_id=success_group_message))

            context = {'td_queries': td_queries, 'query_answer_form': query_answer_form, 'alert': alert}
            return render(request, r"constructor/constructor.html", context=context)
        else:
            print('INVALID FORM!')
            alert = 'invalid form'
            context = {'td_queries': td_queries, 'query_answer_form': query_answer_form, 'alert': alert}
            return render(request, r"constructor/constructor.html", context=context)
    context = {'td_queries': td_queries, 'query_answer_form': query_answer_form}

    return render(request, r"constructor/constructor.html", context=context)


def draw_folder_redirect(request):
    NotImplemented

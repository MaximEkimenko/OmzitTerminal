import datetime
import os
import asyncio

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from .services.service_handlers import handle_uploaded_file
from .services.tech_data_get import tech_data_get
from .forms import GetTehDataForm, ChangeOrderModel, SendDrawBack
from scheduler.models import WorkshopSchedule
from worker.services.master_call_function import terminal_message_to_id
from django.core.exceptions import PermissionDenied


@login_required(login_url="../scheduler/login/")
def tehnolog_wp(request):
    """
    Загрузка технологических данных
    :param request:
    :return:
    """
    group_id = -908012934  # тг группа
    td_queries = (WorkshopSchedule.objects.values('model_order_query', 'query_prior', 'td_status')
                  .exclude(td_status='завершено'))
    change_model_query_form = ChangeOrderModel()
    send_draw_back_form = SendDrawBack()
    alert = ''
    print(request.user.username[:8], 'tehnolog')
    if str(request.user.username).strip() != "admin" and str(request.user.username[:8]).strip() != "tehnolog":
        raise PermissionDenied

    if request.method == 'POST':
        get_teh_data_form = GetTehDataForm(request.POST, request.FILES)  # класс форм с частично заполненными данными
        if get_teh_data_form.is_valid():
            # ключ excel_file в словаре request.FILES должен быть равен имени формы созданной в классе
            # GetTehDataForm
            filename = str(dict(request.FILES)["excel_file"][0])  # имя файла
            # обработка выбора не excel файла
            if '.xlsx' not in filename:
                get_teh_data_form.add_error(None, 'Файл должен быть .xlsx!')
                context = {'get_teh_data_form': get_teh_data_form, 'td_queries': td_queries, 'alert': alert,
                           'change_model_query_form': change_model_query_form,
                           'send_draw_back_form': send_draw_back_form}
                return render(request, r"tehnolog/tehnolog.html", context=context)
            file_save_path = os.getcwd() + r'\xlsx'
            # обработчик загрузки файла
            xlsx_file = handle_uploaded_file(f=request.FILES["excel_file"], filename=filename,
                                             path=file_save_path)
            print('filename=', filename, 'path=', file_save_path, 'xlsx=', xlsx_file)
            list_names = get_teh_data_form.cleaned_data['list_names'].split(',')
            exception_names = get_teh_data_form.cleaned_data['exception_names']
            # вызов сервиса получения данных из xlsx
            try:
                tech_data_get(exel_file=xlsx_file, excel_lists=list_names,
                              exclusion_list=exception_names,
                              model_order_query=get_teh_data_form.cleaned_data['model_order_query'].model_order_query)
                alert = 'Загружено успешно!'
                (WorkshopSchedule.objects.filter(model_order_query=get_teh_data_form.
                                                 cleaned_data['model_order_query'].model_order_query)
                 .update(tehnolog_query_td_fio=f'{request.user.first_name} {request.user.last_name}',
                         td_status="утверждено",
                         td_tehnolog_done_datetime=datetime.datetime.now()
                         ))
                # сообщение в группу
                success_message = True
            except Exception as e:
                print(f'Ошибка загрузки {filename}', e)
                alert = f'Ошибка загрузки {filename}'
                success_message = False
            if success_message:
                success_group_message = (f"Загружен технологический процесс. Заказ-модель: "
                                         f"{get_teh_data_form.cleaned_data['model_order_query'].model_order_query} "
                                         f"доступен для планирования. "
                                         f"Данные загрузил: {request.user.first_name} {request.user.last_name}."
                                         )
                asyncio.run(terminal_message_to_id(to_id=group_id, text_message_to_id=success_group_message))
            else:
                print('Ошибка загрузки')
            print(get_teh_data_form.cleaned_data)
    else:
        get_teh_data_form = GetTehDataForm()  # чистая форма для первого запуска
    context = {'get_teh_data_form': get_teh_data_form, 'td_queries': td_queries, 'alert': alert,
               'change_model_query_form': change_model_query_form,
               'send_draw_back_form': send_draw_back_form}
    return render(request, r"tehnolog/tehnolog.html", context=context)


@login_required(login_url="../scheduler/login/")
def send_draw_back(request):
    """
    Отправка КД на доработку с замечаниями
    :param request:
    :return:
    """
    group_id = -908012934  # тг группа
    if request.method == 'POST':
        send_draw_back_form = SendDrawBack(request.POST)
        if send_draw_back_form.is_valid():
            # заполнение данных замечания
            (WorkshopSchedule.objects.filter(model_order_query=send_draw_back_form.
                                             cleaned_data['model_order_query'].model_order_query)
             .update(tehnolog_remark_fio=f'{request.user.first_name} {request.user.last_name}',
                     is_remark=True,
                     remark_datetime=datetime.datetime.now(),
                     td_remarks=send_draw_back_form.cleaned_data['td_remarks'],
                     td_status='замечание'
                     )
             )
            # сообщение в группу
            success_group_message = (f"КД на заказ-модель: "
                                     f"{send_draw_back_form.cleaned_data['model_order_query'].model_order_query} "
                                     f"возвращено с замечанием: {send_draw_back_form.cleaned_data['td_remarks']}. "
                                     f"КД вернул: {request.user.first_name} {request.user.last_name}."
                                     )
            asyncio.run(terminal_message_to_id(to_id=group_id, text_message_to_id=success_group_message))
        else:
            pass

    return redirect('tehnolog')  # обновление страницы при успехе


@login_required(login_url="../scheduler/login/")
def new_model_query(request):
    """
    Корректировка заказ-модели
    :param request:
    :return:
    """
    group_id = -908012934  # тг группа
    # TODO переименовать папку
    if request.method == 'POST':
        change_model_query_form = ChangeOrderModel(request.POST)
        if change_model_query_form.is_valid():
            # модель_заказ
            new_model_order_query = (f"{change_model_query_form.cleaned_data['order_query'].strip()}_"
                                     f"{change_model_query_form.cleaned_data['model_query'].strip()}")

            (WorkshopSchedule.objects.filter(model_order_query=change_model_query_form.
                                             cleaned_data['model_order_query'].model_order_query)
             .update(order=change_model_query_form.cleaned_data['order_query'].strip(),
                     model_name=change_model_query_form.cleaned_data['order_query'].strip(),
                     model_order_query=new_model_order_query))
            # сообщение в группу
            success_group_message = (f"Заказ-модель переименован технологической службой в: "
                                     f"{new_model_order_query}. "
                                     f"Откорректировал: {request.user.first_name} {request.user.last_name}."
                                     )
            asyncio.run(terminal_message_to_id(to_id=group_id, text_message_to_id=success_group_message))
        else:
            pass
    return redirect('tehnolog')  # обновление страницы при успехе

import datetime
import os

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from .services.service_handlers import handle_uploaded_file
from .services.tech_data_get import tech_data_get
from .forms import GetTehDataForm, ChangeOrderModel, SendDrawBack
from scheduler.models import WorkshopSchedule


@login_required(login_url="../scheduler/login/")
def tehnolog_wp(request):
    """
    Загрузка технологических данных
    :param request:
    :return:
    """
    td_queries = (WorkshopSchedule.objects.values('model_order_query', 'query_prior', 'td_status')
                  .exclude(td_status='завершено'))
    change_model_query_form = ChangeOrderModel()
    send_draw_back_form = SendDrawBack()
    alert = ''
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
            file_save_path = os.getcwd() + r'\xlsx\\'
            # обработчик загрузки файла
            xlsx_file = handle_uploaded_file(f=request.FILES["excel_file"], filename=filename,
                                             path=file_save_path)
            list_names = get_teh_data_form.cleaned_data['list_names'].split(',')
            exception_names = get_teh_data_form.cleaned_data['exception_names']
            # вызов сервиса получения данных из xlsx
            try:
                tech_data_get(exel_file=xlsx_file, excel_lists=list_names,
                              exclusion_list=exception_names,
                              model_order_query=get_teh_data_form.cleaned_data['model_order_query'].model_order_query)
                alert = 'Загружено успешно!'
                # TODO форму возврата чертежа на доработку
                (WorkshopSchedule.objects.filter(model_order_query=get_teh_data_form.
                                                 cleaned_data['model_order_query'].model_order_query)
                 .update(tehnolog_query_td_fio=f'{request.user.first_name} {request.user.last_name}',
                         td_status="утверждено",
                         td_tehnolog_done_datetime=datetime.datetime.now()
                         ))
            except Exception as e:
                print(f'Ошибка загрузки {filename}', e)
                alert = f'Ошибка загрузки {filename}'
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
        else:
            pass
    return redirect('tehnolog')  # обновление страницы при успехе

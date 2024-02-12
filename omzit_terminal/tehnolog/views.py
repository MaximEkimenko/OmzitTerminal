import datetime
import os
import asyncio
import json

from typing import Optional

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect

from .services.service_handlers import handle_uploaded_file
from .services.tech_data_get import tech_data_get
from .forms import GetTehDataForm, ChangeOrderModel, SendDrawBack
from scheduler.models import WorkshopSchedule, Downtime
from constructor.forms import QueryAnswer
from worker.services.master_call_function import terminal_message_to_id
from django.core.exceptions import PermissionDenied
from scheduler.filters import get_filterset
from .services.service_handlers import handle_uploaded_draw_file

# TODO ФУНКЦИОНАЛ ЗАЯВИТЕЛЯ ПЛАЗМЫ И НОВОГО РАБОЧЕГО МЕСТА ТЕХНОЛОГА законсервировано

# import re
# import socket
# from django.http import FileResponse, HttpResponse, JsonResponse
# from django.middleware.csrf import get_token
# from django.views.decorators.csrf import csrf_exempt
# from .services.plasma_utils import create_part_name, read_plasma_layout, create_layout_xlsx, read_plasma_layout_db
# from scheduler.filters import filterset_plasma
# from .forms import TehnologChoice, DoerChoice, LayoutUpload, WorkshopPlasmaChoice
# from scheduler.models import ShiftTask, Doers

# ADMIN_TELEGRAM_ID
TERMINAL_GROUP_ID = os.getenv('TERMINAL_GROUP_ID')


@login_required(login_url="../scheduler/login/")
def tehnolog_wp(request):
    """
    Загрузка технологических данных
    :param request:
    :return:
    """
    group_id = TERMINAL_GROUP_ID  # тг группа
    td_queries_fields = ('model_order_query', 'query_prior', 'td_status', 'td_remarks', 'order_status')  # поля таблицы
    td_queries = (WorkshopSchedule.objects.values(*td_queries_fields).exclude(td_status='завершено'))
    f = get_filterset(data=request.GET, queryset=td_queries, fields=td_queries_fields)  # фильтры в колонки
    print(f)
    change_model_query_form = ChangeOrderModel()
    send_draw_back_form = SendDrawBack()
    alert = ''
    if str(request.user.username).strip()[:5] != "admin" and str(request.user.username[:8]).strip() != "tehnolog":
        raise PermissionDenied

    context = {}
    context.update(upload_draws(
        request=request,
        draws_path=os.path.join('C:/', 'draws'),
        group_id=group_id
    ))
    if request.method == 'POST' and context['upload_alert'] == '':
        get_teh_data_form = GetTehDataForm(request.POST, request.FILES)  # класс форм с частично заполненными данными
        if get_teh_data_form.is_valid():
            filename = str(dict(request.FILES)["excel_file"][0])  # имя файла
            # обработка выбора не excel файла
            if '.xlsx' not in filename:
                get_teh_data_form.add_error(None, 'Файл должен быть .xlsx!')
                context.update({
                    'get_teh_data_form': get_teh_data_form, 'alert': alert,
                    'change_model_query_form': change_model_query_form,
                    'send_draw_back_form': send_draw_back_form,
                    'filter': f
                })
                return render(request, r"tehnolog/tehnolog.html", context=context)
            file_save_path = os.getcwd() + r'\xlsx'
            # обработчик загрузки файла
            xlsx_file = handle_uploaded_file(f=request.FILES["excel_file"], filename=filename,
                                             path=file_save_path)
            print('filename=', filename, 'path=', file_save_path, 'xlsx=', xlsx_file)
            list_name = get_teh_data_form.cleaned_data['list_names']
            print(list_name)
            # вызов сервиса получения данных из xlsx
            try:
                is_uploaded = tech_data_get(exel_file=xlsx_file, excel_list=list_name,
                                            model_order_query=get_teh_data_form.cleaned_data[
                                                'model_order_query'].model_order_query)
                if is_uploaded:
                    alert = 'Загружено успешно!'
                    (WorkshopSchedule.objects.filter(model_order_query=get_teh_data_form.
                                                     cleaned_data['model_order_query'].model_order_query)
                     .update(tehnolog_query_td_fio=f'{request.user.first_name} {request.user.last_name}',
                             td_status="утверждено",
                             td_tehnolog_done_datetime=datetime.datetime.now()
                             ))
                    # сообщение в группу
                    success_message = True
                else:
                    alert = (f'Ошибка загрузки {filename}! '
                             f'Изменены недопустимые поля, добавлены, удалены или перемещены строки!')
                    success_message = False
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
    downtimes = Downtime.objects.filter(
        status='подтверждено',
        reason__in=['Вызов конструктора', 'Вызов технолога']
    ).select_related('shift_task').values(
        'shift_task__ws_number', 'shift_task__ws_number', 'shift_task__order', 'shift_task__model_name',
        'shift_task__op_name', 'shift_task__fio_doer', 'reason', 'description', 'datetime_start', 'master_decision_fio'
    )
    context.update({
        'get_teh_data_form': get_teh_data_form, 'alert': alert,
        'change_model_query_form': change_model_query_form,
        'send_draw_back_form': send_draw_back_form,
        'filter': f,
        'td_queries': td_queries,
        'downtimes': downtimes
    })
    return render(request, r"tehnolog/tehnolog.html", context=context)


@login_required(login_url="../scheduler/login/")
def send_draw_back(request):
    """
    Отправка КД на доработку с замечаниями
    :param request:
    :return:
    """
    group_id = TERMINAL_GROUP_ID  # тг группа
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
    if request.method == 'POST':
        change_model_query_form = ChangeOrderModel(request.POST)
        if change_model_query_form.is_valid():
            old_model_order_query = change_model_query_form.cleaned_data['model_order_query'].model_order_query

            new_order = change_model_query_form.cleaned_data['order_query'].strip()
            new_model = change_model_query_form.cleaned_data['model_query'].strip()

            change_order_model(
                old_order_model=old_model_order_query,
                new_order=new_order,
                new_model=new_model,
                user=f'{request.user.first_name} {request.user.last_name}'
            )
        else:
            pass
    return redirect('tehnolog')  # обновление страницы при успехе


def change_order_model(old_order_model: str, new_model: str, user: str, new_order: Optional[str] = None) -> str:
    if new_order is None:
        new_order = old_order_model.split('_')[0]

    new_model_order_query = f"{new_order}_{new_model}"

    if new_model_order_query == old_order_model:
        return new_model_order_query

    (WorkshopSchedule.objects.filter(model_order_query=old_order_model)
     .update(order=new_order,
             model_name=new_model,
             model_order_query=new_model_order_query))

    # переименование папки
    old_folder = os.path.join("C:/", "draws", old_order_model)
    new_folder = os.path.join("C:/", "draws", new_model_order_query)
    try:
        os.rename(old_folder, new_folder)

        # сообщение в группу
        success_group_message = (f"Заказ-модель переименован технологической службой в: "
                                 f"{new_model_order_query}. "
                                 f"Откорректировал: {user}."
                                 )
        asyncio.run(terminal_message_to_id(to_id=TERMINAL_GROUP_ID, text_message_to_id=success_group_message))
    except Exception as ex:
        print(f'При переименовании папки возникло исключение: {ex}')

    return new_model_order_query


def upload_draws(request, draws_path, group_id):
    """
    Загрузка чертежей технологом к имеющемуся комплекту КД. Обработка доступа к повторной загрузку через
    json файл permissions.json
    :param request:
    :param draws_path: Путь чертежей
    :param group_id: id тг группы для отправки сообщения
    :return:
    """
    alert = ''
    files = dict(request.FILES).get("draw_files")
    if request.method == 'POST' and files is not None:
        draw_files_upload_form = QueryAnswer(request.POST, request.FILES)
        if draw_files_upload_form.is_valid():
            model_order_query = draw_files_upload_form.cleaned_data['model_order_query'].model_order_query
            file_save_path = os.path.join(draws_path, model_order_query)
            # создаем файл с доступами, если не существует
            permissions_json_path = os.path.join(file_save_path, 'permissions.json')
            if not os.path.exists(permissions_json_path):
                try:
                    with open(permissions_json_path, 'w') as json_file:
                        json.dump({}, json_file)
                except Exception as e:
                    print(f'При попытке создания файла доступов {permissions_json_path} вызвано исключение: {e}')
            success = True
            for file in files:
                filename = str(file)
                # обработчик загрузки файла
                uploaded_file = handle_uploaded_draw_file(
                    username=request.user.username,
                    f=file,
                    filename=filename,
                    path=file_save_path
                )
                if not os.path.exists(uploaded_file):
                    alert = f'Ошибка загрузки {filename}.'
                    success = False
                    break
            if success:
                # Сообщение об успехе
                alert = 'Все файлы успешно загружены.'
                success_group_message = (f"Обновлён комплект КД чертежами ТД. Заказ-модель "
                                         f"{model_order_query}. "
                                         f"Обновил: {request.user.first_name} {request.user.last_name}. "
                                         f"Загружено файлов: {len(files)}.")
                asyncio.run(terminal_message_to_id(to_id=group_id, text_message_to_id=success_group_message))
                print(success_group_message, group_id)
        else:
            print('INVALID FORM!')
            alert = 'Ошибка! Форма не валидна!'
    else:
        draw_files_upload_form = QueryAnswer()
    context = {'draw_files_upload_form': draw_files_upload_form, 'upload_alert': alert}
    return context

# TODO ФУНКЦИОНАЛ ЗАЯВИТЕЛЯ ПЛАЗМЫ И НОВОГО РАБОЧЕГО МЕСТА ТЕХНОЛОГА законсервировано
# def plasma_tehnolog_distribution(request):
#     """
#     Распределение сменных заданий по технологам для выполнения раскладок для плазмы
#     """
#
#     if str(request.user.username).strip()[:5] != "admin" and str(request.user.username[:8]).strip() != "tehnolog":
#         raise PermissionDenied
#
#     queryset = ShiftTask.objects.values(
#         'id', 'model_order_query', 'workpiece', 'fio_doer',
#         'fio_tehnolog', 'plasma_layout', 'datetime_done', 'ws_number',
#     ).filter(ws_name='Плазма').exclude(st_status='завершено').order_by("id")
#
#     filter_set = filterset_plasma(request=request, queryset=queryset)
#     pk = 0  # id СЗ, для которого выполнены изменения
#
#     if request.method == "POST":
#         form_submit = request.POST.get("form", "")
#         if "tehnolog" in form_submit:  # действие по select.onchange для выбора технолога
#             tehnolog_choice_form = TehnologChoice(request.POST)
#             if tehnolog_choice_form.is_valid():
#                 tehnolog = tehnolog_choice_form.cleaned_data.get('fio')
#                 if not tehnolog:
#                     tehnolog = "Не распределено"
#                     ws_plasma = ""
#                 else:
#                     # выбираем номер плазмы по умолчанию для технолога
#                     ws_plasma = Doers.objects.get(doers=str(tehnolog)).ws_plasma * 100 + 2
#                 # переназначить технолога можно только до распределения СЗ в цех
#                 shift_tasks = filter_set.qs.filter(fio_doer='не распределено')
#                 if "id" in form_submit:  # если выбран технолог в строке конкретного СЗ
#                     pk = int(form_submit.split("_")[2])
#                     shift_tasks = shift_tasks.filter(pk=pk)
#                 shift_tasks.update(fio_tehnolog=str(tehnolog), ws_number=ws_plasma)
#
#         elif 'workshop' in form_submit:  # действие по select.onchange для выбора цеха плазмы
#             ws_plasma_choice_form = WorkshopPlasmaChoice(request.POST)
#             if ws_plasma_choice_form.is_valid():
#                 ws_plasma = ws_plasma_choice_form.cleaned_data.get('ws')
#                 if not ws_plasma:
#                     ws_plasma = ""
#                 # переназначить цех можно только до распределения СЗ в цех
#                 shift_tasks = filter_set.qs.filter(fio_doer='не распределено')
#                 if "id" in form_submit:  # если выбран цех в строке конкретного СЗ
#                     pk = int(form_submit.split("_")[2])
#                     shift_tasks = shift_tasks.filter(pk=pk)
#                 shift_tasks.update(ws_number=ws_plasma)
#
#         filter_set = filterset_plasma(request=request, queryset=queryset)
#
#     tehnolog_choice_form = TehnologChoice()
#     ws_plasma_choice_form = WorkshopPlasmaChoice()
#
#     context = {
#         "filter": filter_set,
#         "tehnolog_form": tehnolog_choice_form,
#         "ws_plasma_form": ws_plasma_choice_form,
#         "focus_id": pk,
#     }
#
#     return render(request, template_name='tehnolog/plasma_tehnolog_distribution.html', context=context)
#
#
# def plasma_tehnolog(request):
#     """
#     Рабочее место технолога плазмы
#     """
#
#     if str(request.user.username).strip()[:5] != "admin" and str(request.user.username[:8]).strip() != "tehnolog":
#         raise PermissionDenied
#
#     user_name = request.user.first_name
#     queryset = ShiftTask.objects.values(
#         'id', 'model_order_query', 'workpiece', 'fio_doer',
#         'fio_tehnolog', 'plasma_layout', 'datetime_done', 'ws_number',
#     ).filter(ws_name='Плазма', fio_tehnolog=user_name).exclude(st_status='завершено').order_by("id")
#
#     # если в СЗ нет имени dxf (layout_name) то создаем
#     for st in queryset:
#         workpiece = st['workpiece']
#         if not workpiece.get('layout_name'):
#             workpiece['layout_name'] = create_part_name(st)
#             workpiece['layouts_total'] = 0
#             workpiece['layouts'] = {}
#             workpiece['layouts_done'] = {}
#             queryset.filter(pk=st['id']).update(workpiece=workpiece)
#
#     focus_id = 0
#     layout = None  # имя раскладки
#     action = None  # текущее действие
#     alert = ""
#
#     filter_set = filterset_plasma(request=request, queryset=queryset)
#
#     if request.method == "POST":
#         form_submit = request.POST.get("form", "")
#         if "download" in form_submit:  # скачать xlsx файл с СЗ для выполнения раскладок
#             shift_tasks = filter_set.qs.filter(plasma_layout__in=("Не выполнена", "В работе"))
#             shift_tasks.update(plasma_layout="В работе")
#             file_xlsx = create_layout_xlsx(shift_tasks)
#
#             return FileResponse(open(file_xlsx, 'rb'))
#
#         if "upload" in form_submit:  # загрузить файлы раскладок
#             layout_upload_form = LayoutUpload(request.POST, request.FILES)
#             if layout_upload_form.is_valid():
#                 files = dict(request.FILES).get("file")
#                 unknown_parts = []  # детали на раскладках, отсутствующие в сменных заданиях
#                 for file in files:
#                     parts_layouts = read_plasma_layout(file)
#                     for part, layouts in parts_layouts.items():
#                         part_st = filter_set.qs.filter(workpiece__layout_name=part, fio_doer='не распределено')
#                         if part_st:
#                             workpiece = part_st[0]['workpiece']
#                             workpiece['layouts'].update(layouts)
#                             layouts_total = 0
#                             for workpiece_layouts in (workpiece['layouts'], workpiece['layouts_done']):
#                                 layouts_total += sum(map(
#                                     lambda x: sum(x.get('count', [0])),
#                                     workpiece_layouts.values()
#                                 ))
#                             workpiece['layouts_total'] = layouts_total
#                             part_st.update(workpiece=workpiece)
#                         else:
#                             unknown_parts.append(part)
#                 if unknown_parts:
#                     alert = f'На следующие детали с раскладок отсутствуют заявки: {", ".join(unknown_parts)}'
#
#         if 'workshop' in form_submit:
#             ws_plasma_choice_form = WorkshopPlasmaChoice(request.POST)
#             if ws_plasma_choice_form.is_valid():
#                 ws_plasma = ws_plasma_choice_form.cleaned_data.get('ws')
#                 if not ws_plasma:
#                     ws_plasma = ""
#                 shift_tasks = filter_set.qs.filter(fio_doer='не распределено')
#                 if "id" in form_submit:
#                     pk = focus_id = int(form_submit.split("_")[2])
#                     shift_tasks = shift_tasks.filter(pk=pk)
#                 shift_tasks.update(ws_number=ws_plasma)
#                 for st in shift_tasks:
#                     workpiece = st['workpiece']
#                     workpiece['layout_name'] = create_part_name(st)
#                     shift_tasks.filter(pk=st['id']).update(workpiece=workpiece)
#
#         if "confirm_delete" in form_submit:
#             _, layout = form_submit.split("|")
#             queryset = queryset.filter(workpiece__icontains=layout)
#             for st in queryset:
#                 workpiece = st['workpiece']
#                 layout_counts = workpiece['layouts'][layout]['count']
#                 workpiece['layouts'].pop(layout)
#                 workpiece['layouts_total'] -= sum(layout_counts)
#                 queryset.filter(pk=st['id']).update(workpiece=workpiece)
#
#             return redirect('plasma_tehnolog')
#
#         elif 'delete' in form_submit:
#             _, pk, layout = form_submit.split("|")
#             queryset = queryset.filter(workpiece__icontains=layout)
#             action = 'confirm_delete'
#
#         if "confirm_done" in form_submit:
#             _, layout = form_submit.split("|")
#             queryset = queryset.filter(workpiece__icontains=layout)
#             ws_number = queryset[0]['ws_number']
#             if ws_number != '' and len(queryset) == len(queryset.filter(ws_number=ws_number)):
#                 for st in queryset:
#                     workpiece = st['workpiece']
#                     layout_done = workpiece['layouts'].pop(layout)
#                     workpiece['layouts_done'].update({layout: layout_done})
#                     count = workpiece['layouts_done'][layout]['count']
#                     layout_time = workpiece['layouts_done'][layout]['time']
#                     workpiece['layouts_done'][layout]['total_time'] = sum(count) * layout_time
#                     queryset.filter(pk=st['id']).update(workpiece=workpiece, st_status='запланировано')
#
#                 return redirect('plasma_tehnolog')
#
#             alert = "Необходимо выбрать один цех для данной раскладки!"
#         elif "done" in form_submit:
#             _, pk, layout = form_submit.split("|")
#             queryset = queryset.filter(workpiece__icontains=layout)
#             action = 'confirm_done'
#
#         if "confirm_return" in form_submit:
#             _, layout = form_submit.split("|")
#             queryset = queryset.filter(workpiece__icontains=layout)
#             for st in queryset:
#                 workpiece = st['workpiece']
#                 layout_return = workpiece['layouts_done'].pop(layout)
#                 layout_return.pop('total_time')
#                 layout_data = workpiece['layouts'].get(layout)
#                 if layout_data:
#                     layout_data['count'].extend(layout_return['count'])
#                     workpiece['layouts'][layout] = layout_data
#                 else:
#                     workpiece['layouts'][layout] = layout_return
#                 queryset.filter(pk=st['id']).update(workpiece=workpiece, st_status='раскладка')
#             return redirect('plasma_tehnolog')
#
#         elif "return" in form_submit:
#             _, pk, layout = form_submit.split("|")
#             queryset = queryset.filter(workpiece__icontains=layout)
#             action = 'confirm_return'
#
#         if 'data_base' in form_submit:  # загрузить раскладки из БД Sigma
#             dxf = []
#             for shift_task in queryset:
#                 match = re.match(r'^№([^\s]+?)\s(.*)', shift_task['workpiece']['layout_name'])
#                 if match:
#                     dxf.append(match.group(1, 2))
#             parts_layouts = read_plasma_layout_db(dxf)
#             for part, layouts in parts_layouts.items():
#                 part_st = filter_set.qs.filter(workpiece__layout_name=part, fio_doer='не распределено')
#                 if part_st:
#                     workpiece = part_st[0]['workpiece']
#                     workpiece['layouts'].update(layouts)
#                     layouts_total = 0
#                     for workpiece_layouts in (workpiece['layouts'], workpiece['layouts_done']):
#                         layouts_total += sum(map(
#                             lambda x: sum(x.get('count', [0])),
#                             workpiece_layouts.values()
#                         ))
#                     workpiece['layouts_total'] = layouts_total
#                     part_st.update(workpiece=workpiece)
#
#         filter_set = filterset_plasma(request=request, queryset=queryset)
#
#     ws_plasma_choice_form = WorkshopPlasmaChoice()
#     layout_upload_form = LayoutUpload()
#
#     context = {
#         "filter": filter_set,
#         "form": layout_upload_form,
#         "ws_plasma_form": ws_plasma_choice_form,
#         "focus_id": focus_id,
#         "layout": layout,
#         "action": action,
#         "alert": alert,
#     }
#     return render(request, template_name='tehnolog/plasma_tehnolog.html', context=context)
#
#
# @csrf_exempt
# def shift_task_from_tech_data(request):
#     allowed_host_names = {
#         'kubernetes.docker.internal': 'Чекаловец А.В.',
#     }
#     if request.method == 'POST':
#         host_name = socket.gethostbyaddr(request.META['REMOTE_ADDR'])[0]
#         if host_name in allowed_host_names:
#             json_data = request.body
#             data = json.loads(json_data)
#
#             order_model = data.get('model_order_query')
#             tech_ids = [st['tech_id'] for st in data['shift_tasks']]
#
#             new_order_model = change_order_model(
#                 old_order_model=order_model,
#                 new_model=data.get('model_name'),
#                 user=allowed_host_names[host_name]
#             )
#             ws = WorkshopSchedule.objects.get(model_order_query=new_order_model)
#             ws.td_status = 'утверждено'
#             ws.save()
#
#             ShiftTask.objects.filter(
#                 model_order_query=order_model).exclude(tech_id=None).exclude(tech_id__in=tech_ids).delete()
#
#             for shift_task in data['shift_tasks']:
#                 shift_task.pop('next_ids')
#                 shift_task.pop('prev_ids')
#                 shift_task['model_order_query'] = new_order_model
#                 shift_task['workshop'] = ws.workshop
#                 shift_task['datetime_done'] = ws.datetime_done
#                 shift_task['product_category'] = ws.product_category
#                 ShiftTask.objects.filter(
#                     model_order_query=order_model,
#                     st_status='корректировка'
#                 ).update(st_status='не запланировано')
#                 updated_count = ShiftTask.objects.filter(
#                     model_order_query=order_model,
#                     tech_id=shift_task.get('tech_id')
#                 ).update(**shift_task)
#                 if updated_count == 0:
#                     ShiftTask.objects.create(**shift_task)
#
#             return JsonResponse(status=200, data={'message': '✔️Данные успешно добавлены!'})
#         else:
#             return JsonResponse(status=403, data={'message': f'⛔Доступ для АРМ "{host_name}" запрещен!'})
#
#
# def get_orders_models(request):
#     if request.method == 'GET':
#         orders_models_queryset = WorkshopSchedule.objects.exclude(td_status__in=('завершено', 'запрошено'))
#         orders_models = []
#         st_with_doers = ShiftTask.objects.exclude(fio_doer='не распределено').values_list('tech_id', flat=True)
#         st_without_doers = ShiftTask.objects.filter(
#             fio_doer='не распределено',
#         ).values_list('tech_id', flat=True)
#         for order_model in orders_models_queryset:
#             orders_models.append(
#                 {
#                     "order_model": order_model.model_order_query,
#                     "model": order_model.model_name,
#                     "order_status": order_model.order_status,
#                     "td_status": order_model.td_status,
#                     "has_fio_doers": list(st_with_doers.filter(model_order_query=order_model.model_order_query)),
#                     "on_change": len(st_without_doers.filter(
#                         model_order_query=order_model.model_order_query,
#                         st_status='корректировка'
#                     )) > 0,
#                     "st_without_doers": list(st_without_doers.filter(
#                         model_order_query=order_model.model_order_query
#                     ))
#                 }
#             )
#         return JsonResponse(status=200, data=orders_models, safe=False)
#
#
# @csrf_exempt
# def set_shift_task_status(request):
#     allowed_host_names = {
#         'kubernetes.docker.internal': 'Чекаловец А.В.',
#     }
#     if request.method == 'POST':
#         host_name = socket.gethostbyaddr(request.META['REMOTE_ADDR'])[0]
#         if host_name in allowed_host_names:
#             json_data = request.body
#             data = json.loads(json_data)
#
#             order_model = data.get('model_order_query')
#             tech_ids = data.get('tech_ids')
#             status = data.get('status')
#
#             ShiftTask.objects.filter(
#                 model_order_query=order_model,
#                 tech_id__in=tech_ids
#             ).update(st_status=status)
#
#             return JsonResponse(status=200, data={'message': '✔️Данные успешно добавлены!'})
#         else:
#             return JsonResponse(status=403, data={'message': f'⛔Доступ для АРМ "{host_name}" запрещен!'})

import csv
import datetime
import json
import os
import asyncio
import re
import shutil
import io
from zipfile import ZipFile

import openpyxl
from django.contrib.auth.decorators import login_required
from django.forms import formset_factory
from django.http import FileResponse
from django.shortcuts import render, redirect
from django.utils.timezone import make_naive
from odf import text, teletype
from odf.opendocument import load
from transliterate import translit

from constructor.forms import QueryAnswer
from omzit_terminal.settings import BASE_DIR
from .services.plasma_utils import STEELS
from .services.service_handlers import handle_uploaded_file, handle_uploaded_draw_file
from .services.tech_data_get import tech_data_get
from .forms import GetTehDataForm, ChangeOrderModel, SendDrawBack, TehnologChoice, DoerChoice, LayoutUpload, \
    WorkshopPlasmaChoice
from scheduler.models import WorkshopSchedule, ShiftTask, Doers
from worker.services.master_call_function import terminal_message_to_id
from django.core.exceptions import PermissionDenied
from scheduler.filters import get_filterset, filterset_plasma

# ADMIN_TELEGRAM_ID
TERMINAL_GROUP_ID = os.getenv('ADMIN_TELEGRAM_ID')


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
    context.update({
        'get_teh_data_form': get_teh_data_form, 'alert': alert,
        'change_model_query_form': change_model_query_form,
        'send_draw_back_form': send_draw_back_form,
        'filter': f,
        'td_queries': td_queries
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
    group_id = TERMINAL_GROUP_ID  # тг группа
    if request.method == 'POST':
        change_model_query_form = ChangeOrderModel(request.POST)
        if change_model_query_form.is_valid():
            old_model_order_query = change_model_query_form.cleaned_data['model_order_query'].model_order_query

            new_order = change_model_query_form.cleaned_data['order_query'].strip()
            new_model = change_model_query_form.cleaned_data['model_query'].strip()
            new_model_order_query = f"{new_order}_{new_model}"

            (WorkshopSchedule.objects.filter(model_order_query=old_model_order_query)
             .update(order=new_order,
                     model_name=new_model,
                     model_order_query=new_model_order_query))

            # переименование папки
            old_folder = os.path.join("C:/", "draws", old_model_order_query)
            new_folder = os.path.join("C:/", "draws", new_model_order_query)
            os.rename(old_folder, new_folder)

            # сообщение в группу
            success_group_message = (f"Заказ-модель переименован технологической службой в: "
                                     f"{new_model_order_query}. "
                                     f"Откорректировал: {request.user.first_name} {request.user.last_name}."
                                     )
            asyncio.run(terminal_message_to_id(to_id=group_id, text_message_to_id=success_group_message))
        else:
            pass
    return redirect('tehnolog')  # обновление страницы при успехе


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


def plasma_tehnolog_distribution(request):
    queryset = ShiftTask.objects.values(
        'id', 'model_order_query', 'workpiece', 'fio_doer',
        'fio_tehnolog', 'plasma_layout', 'datetime_done', 'workshop_plasma',
    ).filter(ws_name='Плазма').exclude(st_status='завершено').order_by("id")

    filter_set = filterset_plasma(request=request, queryset=queryset)
    pk = 0

    if request.method == "POST":
        form_submit = request.POST.get("form", "")
        if "tehnolog" in form_submit:
            tehnolog_choice_form = TehnologChoice(request.POST)
            if tehnolog_choice_form.is_valid():
                tehnolog = tehnolog_choice_form.cleaned_data.get('fio')
                if not tehnolog:
                    tehnolog = "Не распределено"
                    ws_plasma = None
                else:
                    ws_plasma = Doers.objects.get(doers=str(tehnolog)).ws_plasma
                if "id" in form_submit:
                    pk = int(form_submit.split("_")[2])
                    filter_set.qs.filter(pk=pk).update(fio_tehnolog=str(tehnolog), workshop_plasma=ws_plasma)
                else:
                    filter_set.qs.update(fio_tehnolog=str(tehnolog), workshop_plasma=ws_plasma)

        elif "doer" in form_submit:
            doer_choice_form = DoerChoice(request.POST)
            if doer_choice_form.is_valid():
                doer = doer_choice_form.cleaned_data.get('fio')
                if not doer:
                    doer = "Не распределено"
                if "id" in form_submit:
                    pk = int(form_submit.split("_")[2])
                    filter_set.qs.filter(pk=pk).update(fio_doer=str(doer))
                else:
                    filter_set.qs.update(fio_doer=str(doer))

        elif 'workshop' in form_submit:
            ws_plasma_choice_form = WorkshopPlasmaChoice(request.POST)
            if ws_plasma_choice_form.is_valid():
                ws_plasma = ws_plasma_choice_form.cleaned_data.get('ws')
                if not ws_plasma:
                    ws_plasma = None
                if "id" in form_submit:
                    pk = int(form_submit.split("_")[2])
                    filter_set.qs.filter(pk=pk).update(workshop_plasma=ws_plasma)
                else:
                    filter_set.qs.update(workshop_plasma=ws_plasma)

    tehnolog_choice_form = TehnologChoice()
    doer_choice_form = DoerChoice()
    ws_plasma_choice_form = WorkshopPlasmaChoice()

    filter_set = filterset_plasma(request=request, queryset=queryset)
    context = {
        "filter": filter_set,
        "tehnolog_form": tehnolog_choice_form,
        "doer_form": doer_choice_form,
        "ws_plasma_form": ws_plasma_choice_form,
        "focus_id": pk,
    }

    return render(request, template_name='tehnolog/plasma_tehnolog_distribution.html', context=context)


def plasma_tehnolog(request):
    user_name = request.user.first_name
    queryset = ShiftTask.objects.values(
        'id', 'model_order_query', 'workpiece', 'fio_doer',
        'fio_tehnolog', 'plasma_layout', 'datetime_done', 'workshop_plasma',
    ).filter(ws_name='Плазма', fio_tehnolog=user_name).exclude(st_status='завершено').order_by("id")

    for st in queryset:
        workpiece = st['workpiece']
        if not workpiece.get('layout_name'):
            workpiece['layout_name'] = create_part_name(
                workpiece,
                workpiece['name'],
                workpiece['material'],
                workpiece['count'],
                st['model_order_query'],
            )
            workpiece['layouts_total'] = 0
            workpiece['layouts'] = {}
            queryset.filter(pk=st['id']).update(workpiece=workpiece)
    pk = 0
    filter_set = filterset_plasma(request=request, queryset=queryset)

    if request.method == "POST":
        form_submit = request.POST.get("form", "")
        if "download" in form_submit:
            filter_set.qs.update(plasma_layout="В работе")
            file_xlsx = create_layout_xlsx(filter_set.qs)
            return FileResponse(open(file_xlsx, 'rb'))

        if "upload" in form_submit:
            layout_upload_form = LayoutUpload(request.POST, request.FILES)
            if layout_upload_form.is_valid():
                files = dict(request.FILES).get("file")
                for file in files:
                    counter = read_plasma_layout(file)
                    for part, value in counter.items():
                        part_st = filter_set.qs.filter(workpiece__layout_name=part)
                        if part_st:
                            workpiece = part_st[0]['workpiece']
                            workpiece['layouts'].update(value)
                            workpiece['layouts_total'] = sum(workpiece['layouts'].values())
                            part_st.update(workpiece=workpiece)

        if 'workshop' in form_submit:
            ws_plasma_choice_form = WorkshopPlasmaChoice(request.POST)
            if ws_plasma_choice_form.is_valid():
                ws_plasma = ws_plasma_choice_form.cleaned_data.get('ws')
                if not ws_plasma:
                    ws_plasma = None
                if "id" in form_submit:
                    pk = int(form_submit.split("_")[2])
                    filter_set.qs.filter(pk=pk).update(workshop_plasma=ws_plasma)
                else:
                    filter_set.qs.update(workshop_plasma=ws_plasma)

        if 'delete' in form_submit:
            _, pk, layout = form_submit.split("_")
            workpiece = filter_set.qs.filter(pk=int(pk))[0]['workpiece']
            layout_count = workpiece['layouts'].pop(layout)
            workpiece['layouts_total'] -= layout_count
            filter_set.qs.filter(pk=int(pk)).update(workpiece=workpiece)

    ws_plasma_choice_form = WorkshopPlasmaChoice()
    layout_upload_form = LayoutUpload()

    filter_set = filterset_plasma(request=request, queryset=queryset)

    context = {
        "filter": filter_set,
        "form": layout_upload_form,
        "ws_plasma_form": ws_plasma_choice_form,
        "focus_id": pk,
    }
    return render(request, template_name='tehnolog/plasma_tehnolog.html', context=context)


def create_layout_xlsx(queryset):  # TODO перенести в service
    """
    Создает excel-файл по выбранным заготовкам для выполнения раскладки
    :param queryset: выбранные заготовки
    :return:
    """
    exel_file_src = BASE_DIR / "LayoutPlasmaTemplate.xlsx"
    new_file_name = f"{datetime.datetime.now().strftime('%Y.%m.%d %H-%M-%S')} layout.xlsx"
    # Создаем папку для хранения отчетов
    if not os.path.exists(BASE_DIR / "xlsx"):
        os.mkdir(BASE_DIR / "xlsx")
    # Формируем путь к новому файлу
    exel_file_dst = BASE_DIR / "xlsx" / new_file_name
    # Копируем шаблон в новый файл отчета
    shutil.copy(exel_file_src, exel_file_dst)

    ex_wb = openpyxl.load_workbook(exel_file_src, data_only=True)
    ex_sh = ex_wb["Раскладка"]
    # Данные
    for i, row in enumerate(queryset):
        row.update(row.pop('workpiece'))
        # Пропускаем столбцы
        for field in ('text', 'length', 'fio_doer'):
            row.pop(field)
        for j, key in enumerate(row):
            cell = ex_sh.cell(row=i + 2, column=j + 1)
            cell.value = str(row[key])
    ex_wb.save(exel_file_dst)
    return exel_file_dst


def read_plasma_layout(layout_file):
    file = layout_file.read().decode('Windows-1251')
    reader = io.StringIO(file)
    counter = {}
    if layout_file.name.lower().endswith(".csv"):
        for row in reader:
            dxf = re.match(r"^.*[,]+(.*(SS |SP |GS )[^,]*)[\s,]+([\d]+)", row)
            if dxf:
                part = dxf.group(1).strip()
                counter[part] = {layout_file.name: int(dxf.group(3))}
    elif layout_file.name.lower().endswith(".cnc"):
        for row in reader:
            dxf = re.match(r"^\"PART (.*)\s([\d]+)\s[\d]+\s[\d.]+\s[\d.]+", row)
            if dxf and "$REST_CUT" not in dxf.group(1):
                part = dxf.group(1).strip()
                counter[part] = counter.get(part, {layout_file.name: set()})
                counter[part][layout_file.name].add(dxf.group(2))
        for part, part_value in counter.items():
            for key, value in part_value.items():
                part_value[key] = len(value)
    elif layout_file.name.lower().endswith(".odt"):
        pass
    return counter


def create_part_name(workshop, name, material, count, order_model):
    order, model = order_model.split("_")

    # Толщина
    match = re.match(r"^.*?([\d]+).*", material)
    if match:
        thickness = match.group(1)
    else:
        thickness = ""

    # Наименование
    match = re.match(r"(^.+?)\s\d+х\d+.*", name)
    if match:
        name = match.group(1)

    # Сталь
    steel = ""
    for key, value in STEELS.items():
        if key in material:
            steel = value

    if workshop == 1:
        part_name = f"{thickness}{steel} №{order} {name.strip()} {count}"
    else:
        part_name = f"№{order} {thickness}{steel} {name.strip()} {count}"

    part_name = translit(part_name, language_code='ru', reversed=True)
    return part_name

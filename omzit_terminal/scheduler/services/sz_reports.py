import datetime
import os
import shutil
from typing import Tuple

import openpyxl
import pandas
from openpyxl.styles import Font
from django.core.mail import EmailMessage
from django.db.models import Sum
from django.utils.timezone import make_aware, make_naive

from omzit_terminal.settings import BASE_DIR
from scheduler.models import ShiftTask, Doers


def shift_tasks_auto_report():  # TODO перенести в service
    """
    Отправляет отчет по сменным заданиям на электронную почту и в папку O:/Расчет эффективности/Отчёты по СЗ
    """
    start = make_aware(datetime.datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0))
    end = make_aware(datetime.datetime.now())
    exel_file = create_shift_task_report(start, end)
    shutil.copy(exel_file, os.path.join(r"O:\Расчет эффективности\Отчёты по СЗ", os.path.basename(exel_file)))
    email = EmailMessage(
        f"Отчет {start.strftime('%d.%m.%Y')}-{end.strftime('%d.%m.%Y')}",
        f"Отчет {start.strftime('%d.%m.%Y')}-{end.strftime('%d.%m.%Y')}",
        "omzit-report@yandex.ru",
        [
            "alex4ekalovets@gmail.com",
            "pdo02@omzit.ru",
            "pdo06@omzit.ru",
            "pdo09@omzit.ru",
            "e.savchenko@omzit.ru",
            "PVB@omzit.ru",
            "m.ekimenko@omzit.ru"
        ],
        [],
    )
    email.attach_file(exel_file)
    email.send()


def create_shift_task_report(start: datetime, end: datetime) -> str:  # TODO перенести в service
    """
    Создает excel-файл отчета по сменным заданиям в папке xslx в корне проекта
    :param start: с даты (дата распределения)
    :param end: по дату (дата распределения)
    :return:
    """
    # Формируем имена столбцов для полного отчета из аттрибута модели verbose_name

    verbose_names = dict()
    for field in ShiftTask._meta.get_fields():
        if hasattr(field, "verbose_name"):
            verbose_names[field.name] = field.verbose_name
        else:
            verbose_names[field.name] = field.name

    queryset = ShiftTask.objects.exclude(
        fio_doer="не распределено"
    ).order_by("datetime_assign_wp")

    fields_1C_report = (
        "pk",  # №
        "model_name",  # модель
        "order",  # заказ
        "op_number",  # № Операции
        "op_name_full",  # Операция
        "fio_doer",  # Исполнители
        "decision_time",  # Дата готовности
        "st_status",  # статус СЗ
    )
    fields_disp_report = (
        "pk",  # №
        "model_name",  # модель
        "order",  # заказ
        "ws_number",  # РЦ
        "op_number",  # № Операции
        "op_name_full",  # Операция
        "fio_doer",  # Исполнители
        "datetime_assign_wp",  # Дата распределения
        "datetime_job_start",  # Дата начала
        "decision_time",  # Дата окончания
        "job_duration",  # Длительность работы
        "norm_tech",  # Технологическая норма
        "doers_tech",  # Количество исполнителей по ТД
        "norm_calc",  # Расчетная норма
        "st_status",  # Статус СЗ
        "master_finish_wp",  # Мастер
        "otk_decision",  # Контролер
    )

    # Определяем путь к excel файлу шаблона
    exel_file_src = BASE_DIR / "ReportTemplate.xlsx"
    # Формируем название нового файла
    new_file_name = (f"{datetime.datetime.now().strftime('%Y.%m.%d')} report "
                     f"{start.strftime('%d.%m.%Y')}-{end.strftime('%d.%m.%Y')}.xlsx")
    # Создаем папку для хранения отчетов
    if not os.path.exists(BASE_DIR / "xlsx"):
        os.mkdir(BASE_DIR / "xlsx")
    # Формируем путь к новому файлу
    exel_file_dst = BASE_DIR / "xlsx" / new_file_name
    # Копируем шаблон в новый файл отчета
    shutil.copy(exel_file_src, exel_file_dst)

    # Формируем отчет
    ex_wb = openpyxl.load_workbook(exel_file_src, data_only=True)
    sheets_reports = {
        "Отчет для 1С": queryset.values(*fields_1C_report).filter(
            datetime_assign_wp__gte=start,
            datetime_assign_wp__lte=end
        ),
        "Отчет для диспетчера": queryset.values(*fields_disp_report).filter(
            datetime_assign_wp__gte=start,
            datetime_assign_wp__lte=end
        ),
        "Полный отчет": queryset.values(*verbose_names),
        "Отчет по выполненной норме": fio_st_time_counter(start, end),
    }
    for sheet_name in sheets_reports:
        ex_sh = ex_wb[sheet_name]
        report = sheets_reports[sheet_name]
        font = Font(name='Arial', size=12)
        if report:
            # Для полного отчета создаем шапку из verbose_name
            if sheet_name == "Полный отчет":
                for i, key in enumerate(report[0]):
                    ex_sh.cell(row=1, column=i + 1).value = verbose_names[key]
            # Заполняем строки данными
            for i, row in enumerate(report):
                for j, key in enumerate(row):
                    cell = ex_sh.cell(row=i + 2, column=j + 1)
                    try:
                        row[key] = make_naive(row[key])
                    except Exception:
                        pass
                    cell.value = row[key]
                    cell.font = font
            ex_wb.save(exel_file_dst)
    return exel_file_dst


def fio_st_time_counter(start: datetime, end: datetime):
    """
    Отчет по количеству часов по сменным заданиям по исполнителям
    """
    months = ['', 'Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь', 'Июль', 'Август', 'Сентябрь', 'Октябрь',
              'Ноябрь', 'Декабрь']
    month = months[int(start.strftime('%m'))]
    year = int(start.strftime('%Y'))
    doer_job_duration = []
    doers = Doers.objects.values_list('doers', flat=True).order_by('doers').all()
    shift_tasks = ShiftTask.objects.filter(decision_time__gte=start, decision_time__lte=end)
    main_path = fr"M:\Xranenie\Расчет эффективности"
    cex_1_timesheets = os.path.join(main_path, 'Табель цеха №1.xlsx')
    cex_2_timesheets = os.path.join(main_path, 'Табель цеха №2.xlsx')
    cex_1 = None
    cex_2 = None
    try:
        cex_1 = pandas.read_excel(cex_1_timesheets, sheet_name=f'{month} {year}')
        cex_2 = pandas.read_excel(cex_2_timesheets, sheet_name=f'{month} {year}')
    except Exception as ex:
        print(ex)
    for i, doer in enumerate(doers):
        sum_job_duration = shift_tasks.filter(
            fio_doer__contains=doer, st_status='принято'
        ).aggregate(duration=Sum('norm_calc'))
        data = {
            "fio": doer,
            "duration": sum_job_duration['duration']
        }
        if cex_1 is not None:
            try:
                data["cex1"] = int(cex_1[cex_1.iloc[:, 1] == doer].iloc[:, 37].iloc[0])
            except Exception as ex:
                print(ex)
                data["cex1"] = 'Нет в табеле'
        else:
            data["cex1"] = f'Файл {cex_1_timesheets} или вкладка {month} {year} недоступны'
        if cex_2 is not None:
            try:
                data["cex2"] = int(cex_2[cex_2.iloc[:, 1] == doer].iloc[:, 37].iloc[0])
            except Exception as ex:
                print(ex)
                data["cex2"] = 'Нет в табеле'
        else:
            data["cex2"] = f'Файл {cex_2_timesheets} или вкладка {month} {year} недоступны'
        doer_job_duration.append(data)
    return doer_job_duration


def get_start_end_st_report(start: str, end: str) -> Tuple:  # TODO перенести в service
    """
    Преобразует полученные от пользователя строки с датами или null в дату и время
    :param start: с даты (Дата распределения)
    :param end: по дату (Дата распределения)
    :return: дату начала, дату окончания формирования отчета
    """
    if start == "null":
        start = make_aware(datetime.datetime(year=1990, month=1, day=1, hour=0, minute=0, second=0, microsecond=0))
    else:
        start = make_aware(datetime.datetime.strptime(start, "%d.%m.%Y"))
    if end == "null":
        end = make_aware(datetime.datetime.now())
    else:
        end = make_aware(datetime.datetime.strptime(end, "%d.%m.%Y").replace(hour=23, minute=59, second=59))
    return start, end

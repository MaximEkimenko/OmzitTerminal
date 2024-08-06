from datetime import datetime
from pathlib import Path
from django.db.models import Model, Subquery
from controller.apps import ControllerConfig as App
from m_logger_settings import logger
from scheduler.models import ShiftTask
from controller.models import DefectAct
from django.db.models import QuerySet


def format_act_number(date: datetime, number: int) -> str:
    """
    Форматирует номер акта о браке.
    @param date: , дата, месяц и год которой будут использоваться при создании номера
    @param number: порядковый номер акта
    @return: строка вида 07.2024-01
    """
    return f"{date.month:02}.{date.year}-{number:02}"


def insert_shifttask_records(qs: QuerySet, number: int):
    """

    @param qs: QuerySet сменных заданий, отчеченных как "брак"
    @param number: номер, начиная с которого нужно нумеровать все обрабатываемые сменные задания
    @return:
    """
    act_number = number
    for task in qs:
        date_fail = task.datetime_fail
        fix_time = None
        if nst := task.next_shift_task:
            fix_time = nst.decision_time - nst.datetime_job_start
        obj_dict = {
            "datetime_fail": task.datetime_fail,
            "tech_number": act_number,
            "act_number": format_act_number(date_fail, act_number),
            "workshop": task.workshop,
            "operation": task.op_number + " " + task.op_name_full,
            "fixing_time": fix_time,
            "shift_task": task,
            "fio_failer": task.fio_failer,
            "master_finish_wp": task.master_finish_wp,
        }
        DefectAct.objects.create(**obj_dict)
        act_number += 1


def add_defect_acts(first_number=1):
    """
    При первом запуске надо указать номер, с которого начинается нумерация актов.
    Периодически запускается и формиует акты, на основе сменных заданий,
    на которые еще нет ссылок в таблице DefectAct.
    Отдельно запускается при запуске приложения, чтобы импортировать все подходящие записи из ShiftTask
    # @return:
    # """
    # выбираем в таблице актов ссылки на сменные задания, которые уже добавлены
    shifttask_fers = DefectAct.objects.exclude(shift_task__isnull=True).values("shift_task")
    # выбираем из сменных заданий записи с маркировкой "брак", которые еще не добавлены в акты о браке
    ts = (
          ShiftTask.objects
          .filter(st_status__icontains="брак")
          .exclude(pk__in=Subquery(shifttask_fers))
          .order_by("datetime_fail").all()
          )
    act_number = first_number
    # если в таблице уже есть акты о браке, то берем номер последнего и увеличиваем на единицу
    last_act_number = DefectAct.last_act_number()
    if last_act_number is not None:
        act_number = last_act_number + 1
    insert_shifttask_records(ts, act_number)




def get_model_verbose_names(model: Model) -> dict[str, str]:
    """
    Возвращает словарь подписей к полям таблицы (переданной модели)
    Ключ: название поля (имя переменной, ссылающейся на поле)
    Значение: русское название поля, взятое из атрибута verbose_names поля
    """
    verbose_names = dict()
    # можно использовать такой подход
    for field in model._meta.get_fields():
        if hasattr(field, "verbose_name"):
            verbose_names[field.name] = field.verbose_name
        else:
            verbose_names[field.name] = field.name
    return verbose_names


def check_media_ref(act: DefectAct):
    """
    Определяет как должна формироваться папка с файлами для акта о браке.
    Она может быть ключом id или номер акта, главное ее вид определить в одном месте
    @param act:
    @return:
    """
    if not act.media_ref:
        act.media_ref = act.act_number
        act.save()
    return act

def check_directory(act:DefectAct) -> Path:
    """
    Проверяет, существует ли директория. Если нет, то создает ее и возвращает абсолютный путь к директории
    @param path: строка с названием директории (одно словоБ может быть даже id записи об актах)
    @return: абсолютный путь к директории
    """
    dest_dir = App.DEFECTS_BASE_PATH.joinpath(act.media_ref)
    if not dest_dir.exists():
        try:
            dest_dir.mkdir()
        except Exception as e:
            logger.error(f"Ошибка при создании каталога '{act.media_ref}' для акта о браке")
            logger.exception(e)
            return None
    return dest_dir


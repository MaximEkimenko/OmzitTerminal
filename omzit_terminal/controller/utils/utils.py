from pathlib import Path
from django.db.models import Model, Subquery
from controller.apps import ControllerConfig as App
from m_logger_settings import logger
from scheduler.models import ShiftTask
from controller.models import DefectAct
from django.db.models import QuerySet


def format_act_number(date, number):
    return f"{date.month:02}.{date.year}-{number:02}"


def insert_shifttask_records(qs:QuerySet, number: int):
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
            "shift_task": task
        }
        DefectAct.objects.create(**obj_dict)
        act_number += 1


def import_acts_from_shift_task(first_number):
    """
    Выбирает все записи из ShiftTask, которые отмечены как "брак" и на их основе создает акты о браке.
    Это делает ся в начале на этапе первоначального заполнения таблицы, когда в ней еще ничего нет.
    Номера актов взять неоткуда, поэтому передается параметр, с какого числа будут формироваться акты.
    @param first_number:
    """
    # TODO: try-except
    ts = ShiftTask.objects.filter(st_status__icontains="брак").order_by("datetime_fail").all()
    insert_shifttask_records(ts, first_number)


def add_defect_acts():
    """
    # Периодически запускается и форирует акты, на основе сменных заданий,
    # на которые еще нет ссылок в таблице DefectAct
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
    act_number = DefectAct.last_act_number() + 1
    #TODO: try-except
    insert_shifttask_records(ts, act_number)




def get_model_verbose_names(model: Model) -> dict[str, str]:
    """
    Возвращает словарь подписей к полям таблицы заявок на ремонт (Orders)
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


def check_directory(path: str) -> Path:
    """
    Проверяет, существует ли директория. Если нет, то создает ее и возвращает абсолютный путь к директории
    @param path: строка с названием директории (одно словоБ может быть даже id записи об актах)
    @return: абсолютный путь к директории
    """
    dest_dir = App.DEFECTS_BASE_PATH.joinpath(path)
    if not dest_dir.exists():
        try:
            dest_dir.mkdir()
        except Exception as e:
            logger.error(f"Ошибка при создании каталога '{path}' для акта о браке")
            logger.exception(e)
            return None
    return dest_dir


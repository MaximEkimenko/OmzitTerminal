from pathlib import Path
from django.db.models import Model
from controller.apps import ControllerConfig as App
from m_logger_settings import logger
from scheduler.models import ShiftTask
from controller.models import DefectAct
from django.db.models import QuerySet

def import_acts_from_shift_task(first_number)-> QuerySet:
    """
    Выбирает все записи из ShiftTask, которые отмечены как "брак" и на их основе создает акты о браке
    @param first_number:
    @return:
    """
    act_count = first_number
    ts = ShiftTask.objects.filter(st_status__icontains="брак").order_by("-datetime_fail").all()
    for task in ts:
        df = task.datetime_fail
        fix_time = None
        if nst := task.next_shift_task:
            fix_time = nst.decision_time - nst.datetime_job_start
        obj_dict = {
            "datetime_fail": task.datetime_fail,
            "act_number": f"{df.month}.{df.year}/{act_count}",
            "workshop": task.workshop,
            "operation": task.op_number + " " + task.op_name_full,
            "fixing_time": fix_time,
            "from_shift_task": True,
        }
        DefectAct.objects.create(**obj_dict)
        act_count += 1
    return DefectAct.objects.all()



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


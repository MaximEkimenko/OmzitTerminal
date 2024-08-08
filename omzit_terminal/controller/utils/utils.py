import json
from datetime import datetime
from pathlib import Path
from django.db.models import Model, Subquery
from controller.apps import ControllerConfig as App  # noqa
from m_logger_settings import logger  # noqa
from scheduler.models import ShiftTask  # noqa
from controller.models import DefectAct  # noqa
from django.db.models import QuerySet
from omzit_terminal.settings import BASE_DIR  # noqa
from django.db.models import Q, F


# from django.db.models import F, Value

def format_act_number(date: datetime, number: int) -> str:
    """
    Форматирует номер акта о браке.
    @param date: , дата, месяц и год которой будут использоваться при создании номера
    @param number: порядковый номер акта
    @return: строка вида 07.2024-01
    """
    return f"{date.month:02}.{date.year}-{number:02}"


def insert_shift_task_records(qs: QuerySet, number: int):
    """
    @param qs: QuerySet сменных заданий, отмеченных как "брак"
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
            'processing_object': task.model_order_query
        }
        DefectAct.objects.create(**obj_dict)
        act_number += 1


def add_defect_acts(first_number=1):
    """
    При первом запуске надо указать номер, с которого начинается нумерация актов.
    Периодически запускается и формирует акты, на основе сменных заданий,
    на которые еще нет ссылок в таблице DefectAct.
    Отдельно запускается при запуске приложения, чтобы импортировать все подходящие записи из ShiftTask
    # @return:
    # """
    # выбираем в таблице актов ссылки на сменные задания, которые уже добавлены
    shift_task_exist = DefectAct.objects.exclude(shift_task__isnull=True).values("shift_task")
    # выбираем из сменных заданий записи с маркировкой "брак", которые еще не добавлены в акты о браке
    shift_tasks = (
        ShiftTask.objects
        .filter(st_status__icontains="брак")
        .exclude(pk__in=Subquery(shift_task_exist))
        .order_by("datetime_fail").all()
    )
    act_number = first_number
    # перевод telegram_id в ФИО
    for shift_task in shift_tasks:
        shift_task.master_finish_wp = telegram_id_to_fio(shift_task.master_finish_wp)
    # если в таблице уже есть акты о браке, то берем номер последнего и увеличиваем на единицу
    last_act_number = DefectAct.last_act_number()
    if last_act_number is not None:
        act_number = last_act_number + 1
    insert_shift_task_records(shift_tasks, act_number)


def update_defect_acts() -> None:
    """
    Функция обновления актов о браке
    :return:
    """
    acts_to_update = (
        DefectAct.objects.select_related()
        .filter(
            Q(fixing_time__isnull=True) |
            Q(master_finish_wp='Неизвестный ID') |
            Q(master_finish_wp='Ошибка чтения json') |
            Q(master_finish_wp=None)
            ).annotate(
                act_master_finish_wp=F('master_finish_wp'),
                shift_task_master_finish_wp=F('shift_task__master_finish_wp'),
                act_next_shift_task_id=F('shift_task__next_shift_task'),
                ))
    next_shift_tasks = ((
        ShiftTask.objects
        .filter(pk__in=Subquery(acts_to_update.values('shift_task')))
    ).select_related(
        ).annotate(
            next_shift_task_start=F('next_shift_task__datetime_job_start'),
            next_shift_task_end=F('next_shift_task__decision_time'),
            st_next_shift_task_id=F('next_shift_task__id'),
        ).values())
    for act in acts_to_update:
        for task in next_shift_tasks:
            if task.get('st_next_shift_task_id'):
                if task.get('st_next_shift_task_id') == act.act_next_shift_task_id:
                    act.fixing_time = task['next_shift_task_end'] - task['next_shift_task_start']
                    break
        # перевод telegram_id
        act.master_finish_wp = telegram_id_to_fio(act.shift_task_master_finish_wp)
    DefectAct.objects.bulk_update(acts_to_update, ('master_finish_wp', 'fixing_time'))


def get_model_verbose_names(model: Model) -> dict[str, str]:
    """
    Возвращает словарь подписей к полям таблицы (переданной модели)
    Ключ: название поля (имя переменной, ссылающейся на поле)
    Значение: русское название поля, взятое из атрибута verbose_names поля
    """
    verbose_names = dict()
    # можно использовать такой подход
    for field in model._meta.get_fields():  # noqa
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


def check_directory(act: DefectAct) -> Path | None:
    """
    Проверяет, существует ли директория. Если нет, то создает ее и возвращает абсолютный путь к директории
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


def telegram_id_to_fio(telegram_id: str) -> str:
    """
    Функция возвращает ФИО из json файла по telegram_id
    :param telegram_id:
    :return:
    файл id_fios.json помещён в .gitignore форма файла для тестирования:
    {"ФИО": telegram_id, ...}
    """
    json_path = BASE_DIR / 'id_fios.json'
    try:
        with open(json_path, 'r', encoding='utf-8') as json_file:
            json_id_fios = json.load(json_file)
    except Exception as e:
        logger.error(f"Ошибка при чтении json файла '{json_path}'")
        logger.exception(e)
        return 'Ошибка чтения json'
    return next((key for key, val in json_id_fios.items() if val == int(telegram_id)), 'Неизвестный ID')

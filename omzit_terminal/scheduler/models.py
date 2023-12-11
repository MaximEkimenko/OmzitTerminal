import datetime

from django.core.validators import RegexValidator
from django.db import models
from django.db.models import Avg
from django.forms import ModelChoiceField
from django.utils import timezone

from tehnolog.models import ProductCategory

model_pattern = r"^[\-A-Za-z0-9]+$"
model_error_text = "Имя модели может содержать только цифры и буквы латинского алфавита и знак '-' тире"

order_pattern = r"^[А-Яа-яA-Za-z0-9\(\)\-]+$"
order_error_text = 'Имя заказа может содержать только цифры, буквы, знаки тире "-" и скобки "()"'

model_regex = RegexValidator(
    regex=model_pattern,
    message=model_error_text,
)

order_regex = RegexValidator(
    regex=order_pattern,
    message=order_error_text,
)


class WorkshopSchedule(models.Model):
    """
    Данные для планирования цеха, статусы заказов, статусы чертежей
    """
    objects = models.Manager()  # явное указание метода для pycharm
    workshop = models.PositiveSmallIntegerField(verbose_name='Цех', null=True)
    model_name = models.CharField(max_length=30, verbose_name='Модель изделия', validators=[model_regex])
    datetime_done = models.DateField(null=True, verbose_name='Планируемая дата готовности')
    order = models.CharField(max_length=100, verbose_name='Номер заказа', validators=[order_regex])
    order_status = models.CharField(max_length=20, default='не запланировано', verbose_name='Статус заказа')

    model_order_query = models.CharField(max_length=60, null=True, verbose_name='заказ и модель', unique=True)

    query_prior = models.PositiveSmallIntegerField(verbose_name='Приоритет заявки чертежей', default=1)
    done_rate = models.DecimalField(null=True, max_digits=10, decimal_places=2, default=0,
                                    verbose_name='процент готовности')
    td_status = models.CharField(max_length=20, default='запрошено', verbose_name='Статус технической документации')
    td_query_datetime = models.DateTimeField(auto_now_add=True, null=True,
                                             verbose_name='дата/время запроса документации')
    td_remarks = models.TextField(blank=True, verbose_name='замечания к КД')
    tehnolog_remark_fio = models.CharField(max_length=30, null=True, verbose_name='Замечание от')
    is_remark = models.BooleanField(null=True, default=False, verbose_name='Факт наличия замечания к КД')
    remark_datetime = models.DateTimeField(null=True, verbose_name='дата/время замечания к КД')
    td_const_done_datetime = models.DateTimeField(null=True, verbose_name='дата/время ответа конструктора по КД')
    td_tehnolog_done_datetime = models.DateTimeField(null=True, verbose_name='дата/время ответа технолога по КД')

    plan_datetime = models.DateTimeField(null=True, verbose_name='дата/время выполнения планирования заказа')
    dispatcher_query_td_fio = models.CharField(max_length=30, null=True, verbose_name='Запросил КД')
    dispatcher_plan_ws_fio = models.CharField(max_length=30, null=True, verbose_name='Запланировал')
    constructor_query_td_fio = models.CharField(max_length=30, null=True, verbose_name='Передал КД')
    tehnolog_query_td_fio = models.CharField(max_length=30, null=True, verbose_name='Утвердил / загрузил')
    product_category = models.CharField(max_length=30, null=True, verbose_name='Категория изделия')

    # Пример структуры {
    # "author": "admin",
    # "sz_text": "Прошу изготовить",
    # "need_date": "22.12.2023",
    # "sz_number": "СЗ1",
    # "product_name": "Блок Б57"
    # }
    sz = models.JSONField(null=True, blank=True, verbose_name='Данные служебной записки')

    # tehnolog_excel_load_fio = models.CharField(max_length=30, null=True, verbose_name='Загрузил')

    class Meta:
        db_table = "workshop_schedule"
        verbose_name = 'График цеха'
        verbose_name_plural = 'График цеха'

    # def __str__(self):
    #     return str(self.datetime_done)


class Doers(models.Model):
    # TODO синхронизация с 1С
    """
    Таблица исполнителей
    """
    objects = models.Manager()  # явное указание метода для pycharm
    doers = models.CharField(max_length=255, unique=True, verbose_name='ФИО исполнителей')
    job_title = models.CharField(max_length=255, null=True, blank=True, verbose_name='Должность')
    ws_plasma = models.PositiveSmallIntegerField(verbose_name='Цех плазмы (по умолчанию)', null=True, blank=True)

    class Meta:
        db_table = "doers"
        verbose_name = 'Исполнитель'
        verbose_name_plural = 'Исполнители'

    def __str__(self):
        return self.doers


# class DocQuery(models.Model):
#     pass


class ShiftTask(models.Model):
    """
    Модель данных сменного задания основная модель всего терминала
    """
    objects = models.Manager()  # явное указание метода для pycharm
    workshop = models.PositiveSmallIntegerField(verbose_name='Цех', null=True)
    model_name = models.CharField(max_length=30, db_index=True, verbose_name='Модель изделия', validators=[model_regex])
    datetime_done = models.DateField(verbose_name='Ожидаемая дата готовности', null=True)
    order = models.CharField(max_length=100, verbose_name='Номер заказа', null=True, validators=[order_regex])
    model_order_query = models.CharField(max_length=60, null=True, verbose_name='заказ и модель')
    op_number = models.CharField(max_length=20, verbose_name='Номер операции')
    op_name = models.CharField(max_length=200, verbose_name='Имя операции')
    ws_name = models.CharField(max_length=100, verbose_name='Имя рабочего центра')
    op_name_full = models.CharField(max_length=255, verbose_name='Полное имея операции')
    ws_number = models.CharField(max_length=10, verbose_name='Номер рабочего центра')
    norm_tech = models.DecimalField(null=True, max_digits=10, decimal_places=2,
                                    verbose_name='Технологическая норма времени')
    datetime_techdata_create = models.DateTimeField(verbose_name='дата/время занесения технологических данных',
                                                    auto_now_add=True)
    datetime_techdata_update = models.DateTimeField(verbose_name='дата/время корректировки технологических данных',
                                                    auto_now=True)
    datetime_plan_ws = models.DateTimeField(auto_now=True, verbose_name='время планирования в цех')
    datetime_plan_wp = models.DateTimeField(null=True, verbose_name='время планирования РЦ')
    fio_doer = models.CharField(max_length=255, null=True, default='не распределено', verbose_name='ФИО исполнителей')
    datetime_assign_wp = models.DateTimeField(null=True, verbose_name='время распределения')
    datetime_job_start = models.DateTimeField(null=True, verbose_name='время начала работ')
    datetime_master_call = models.DateTimeField(null=True, verbose_name='время вызова мастера')
    master_finish_wp = models.CharField(max_length=30, null=True, verbose_name='ФИО мастера вызова ОТК')
    datetime_otk_call = models.DateTimeField(null=True, verbose_name='время вызова ОТК')
    datetime_otk_answer = models.DateTimeField(null=True, verbose_name='время ответа ОТК')
    master_calls = models.IntegerField(null=True, default=0, verbose_name='количество вызовов мастера')
    master_called = models.CharField(max_length=10, null=True, default='не было', verbose_name='статус вызова мастера')
    norm_fact = models.DecimalField(null=True, max_digits=10, decimal_places=2,
                                    verbose_name='Фактическая норма времени')
    otk_answer = models.CharField(max_length=30, null=True, verbose_name='ФИО контролёра ответа ОТК')
    otk_decision = models.CharField(max_length=30, null=True, verbose_name='ФИО контролёра решения ОТК')
    decision_time = models.DateTimeField(null=True, verbose_name='Время приёмки ОТК')
    st_status = models.CharField(max_length=20, default='не запланировано', verbose_name='Статус СЗ')
    is_fail = models.BooleanField(null=True, default=False, verbose_name='Факт наличия брака')
    datetime_fail = models.DateTimeField(null=True, verbose_name='Время регистрации брака')
    fio_failer = models.CharField(max_length=255, null=True, verbose_name='ФИО бракоделов')
    master_assign_wp_fio = models.CharField(max_length=30, null=True, verbose_name='Распределил')
    excel_list_name = models.CharField(max_length=100, null=True, verbose_name='Лист excel технологического процесса')
    draw_path = models.CharField(max_length=255, null=True, blank=True, verbose_name='путь к связанным чертежам')
    draw_filename = models.TextField(null=True, blank=True, verbose_name='имя чертежа')
    product_category = models.CharField(null=True, verbose_name='Категория изделия')
    job_duration = models.DurationField(null=True, blank=True, verbose_name='Длительность работы')
    datetime_job_resume = models.DateTimeField(null=True, blank=True, verbose_name='Время возобновления работы')
    next_shift_task = models.ForeignKey(
        'ShiftTask',
        on_delete=models.PROTECT,
        related_name="previous_shift_task",
        verbose_name='Новое СЗ',
        null=True,
        blank=True
    )

    # Пример структуры {
    # "draw": "AGCC.287-6400-PB-01-KM1.DW-0037 - Блок Б57-1-Тип10_V18",
    # "name": "Б1-1",
    # "text": "Б1-1 Швеллер 30П ГОСТ 8240-97 С255-4 ГОСТ 27772-2015 L=7500 (2 шт.)",
    # "count": "2",
    # "layout_name": "4SP №order1 B-26 Balka №26 2", имя детали
    # "layouts": {'12ГС-43.CNC': 1}
    # "layouts_done": {'12ГС-44.CNC': 1}
    # "layouts_total": 2 количество на всех раскладках
    # "length": "7500",
    # "material": "Швеллер 30П ГОСТ 8240-97 С255-4 ГОСТ 27772-2015"
    # }
    workpiece = models.JSONField(null=True, blank=True, verbose_name='Заготовка')
    fio_tehnolog = models.CharField(max_length=255, null=True, blank=True,
                                    default='не распределено', verbose_name='ФИО технолога')
    plasma_layout = models.CharField(max_length=255, null=True, blank=True,
                                     default='Не выполнена', verbose_name='Раскладка')
    workshop_plasma = models.PositiveSmallIntegerField(verbose_name='Цех плазмы', null=True, blank=True)

    class Meta:
        db_table = "shift_task"
        verbose_name = 'Сменное задание'
        verbose_name_plural = 'Сменные задания'


class DailyReport(models.Model):
    """
    Данные для ежедневных отчётов
    """
    objects = models.Manager()
    calendar_day = models.DateField(verbose_name="Дата отчёта")
    day_plan = models.DecimalField(decimal_places=1, max_digits=10, verbose_name="План на день", default=0)
    day_fact = models.DecimalField(decimal_places=1, max_digits=10, verbose_name="Факт за день", default=0)

    aver_fact = models.DecimalField(decimal_places=2, max_digits=10, verbose_name="Отставание/опережение плана",
                                    default=0)

    day_plan_rate = models.DecimalField(decimal_places=2, max_digits=10, verbose_name="% выполнения плана за день",
                                        default=0)

    plan_sum = models.DecimalField(decimal_places=1, max_digits=10, verbose_name="Всего план на дату", default=0)
    fact_sum = models.DecimalField(decimal_places=1, max_digits=10, verbose_name="Всего факт на дату", default=0)

    plan_done_rate = models.DecimalField(decimal_places=2, max_digits=10, verbose_name="% выполнения плана",
                                         default=0)
    fact_done_rate = models.DecimalField(decimal_places=2, max_digits=10, verbose_name="Фактический % выполнения плана",
                                         default=0)
    plan_loos_rate = models.DecimalField(decimal_places=2, max_digits=10, verbose_name="Отставание/опережение плана",
                                         default=0)
    day_fails = models.PositiveSmallIntegerField(verbose_name="Случаев брака за день", default=0)
    day_save_violations = models.PositiveSmallIntegerField(verbose_name="Случаев нарушений ОТПБ за день", default=0)
    month_plan_data = models.ForeignKey(to='MonthPlans', on_delete=models.PROTECT,
                                        related_name="month_plan_table",
                                        null=True, blank=True,
                                        verbose_name="Месяц планирования")
    workshop = models.PositiveSmallIntegerField(verbose_name="Цех", default=0)
    # работники
    personal_total = models.PositiveSmallIntegerField(verbose_name='Всего персонала в цехе', default=0)
    personal_shift = models.PositiveSmallIntegerField(verbose_name='Выход в дату персонала', default=0)

    personal_total_welders = models.PositiveSmallIntegerField(verbose_name='Всего сварщиков', default=0)
    personal_shift_welders = models.PositiveSmallIntegerField(verbose_name='Выход в дату сварщиков', default=0)
    personal_night_welders = models.PositiveSmallIntegerField(verbose_name='Выход ночь сварщики', default=0)

    personal_total_locksmiths = models.PositiveSmallIntegerField(verbose_name='Всего слесарей', default=0)
    personal_shift_locksmiths = models.PositiveSmallIntegerField(verbose_name='Выход в дату слесарей', default=0)
    personal_night_locksmiths = models.PositiveSmallIntegerField(verbose_name='Выход ночь слесаря', default=0)

    personal_total_painters = models.PositiveSmallIntegerField(verbose_name='Всего маляров', default=0)
    personal_shift_painters = models.PositiveSmallIntegerField(verbose_name='Выход маляров', default=0)
    personal_night_painters = models.PositiveSmallIntegerField(verbose_name='Выход ночь маляры', default=0)

    personal_total_turners = models.PositiveSmallIntegerField(verbose_name='Всего токарей', default=0)
    personal_shift_turners = models.PositiveSmallIntegerField(verbose_name='Выход токарей', default=0)
    personal_night_turners = models.PositiveSmallIntegerField(verbose_name='Выход ночь токаря', default=0)

    class Meta:
        db_table = "report"
        verbose_name = 'Ежедневный отчёт'
        verbose_name_plural = 'Ежедневные отчёты'


class MonthPlans(models.Model):
    """
    Ежемесячные значения плана
    """
    objects = models.Manager()
    month_plan = models.DateField(verbose_name="Месяц планирования")
    month_plan_amount = models.DecimalField(decimal_places=1, max_digits=10, verbose_name="План на месяц в н/ч")
    workshop = models.PositiveSmallIntegerField(verbose_name="Цех", default=0)

    class Meta:
        db_table = "month_plan_table"
        verbose_name = 'План на месяц в н/ч'
        verbose_name_plural = 'Планы на месяц в н/ч'

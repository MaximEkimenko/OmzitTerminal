from django.core.validators import RegexValidator
from django.db import models
from django.contrib.postgres.fields import ArrayField
import datetime
from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.utils.timezone import now
# TODO ФУНКЦИОНАЛ ЗАЯВИТЕЛЯ ПЛАЗМЫ И НОВОГО РАБОЧЕГО МЕСТА ТЕХНОЛОГА законсервировано
# import datetime
# from django.db.models import Avg
# from django.forms import ModelChoiceField
# from django.utils import timezone

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
    td_status = models.CharField(max_length=20, default='запрошено', null=True,
                                 verbose_name='Статус технической документации')
    td_query_datetime = models.DateTimeField(auto_now_add=True, null=True,
                                             verbose_name='дата/время запроса документации')
    td_remarks = models.TextField(blank=True, verbose_name='замечания к КД')
    tehnolog_remark_fio = models.CharField(max_length=30, null=True, verbose_name='Замечание от')
    is_remark = models.BooleanField(null=True, default=False, verbose_name='Факт наличия замечания к КД')
    remark_datetime = models.DateTimeField(null=True, verbose_name='дата/время замечания к КД')
    td_const_done_datetime = models.DateTimeField(null=True, verbose_name='дата/время ответа конструктора по КД')
    td_tehnolog_done_datetime = models.DateTimeField(null=True, verbose_name='дата/время ответа технолога по КД')
    dispatcher_query_td_fio = models.CharField(max_length=30, null=True, verbose_name='Запросил КД')
    dispatcher_plan_ws_fio = models.CharField(max_length=31, null=True, verbose_name='Запланировал')
    constructor_query_td_fio = models.CharField(max_length=30, null=True, verbose_name='Передал КД')
    tehnolog_query_td_fio = models.CharField(max_length=30, null=True, verbose_name='Утвердил / загрузил')
    product_category = models.CharField(max_length=30, null=True, verbose_name='Категория изделия')

    # TODO добавлено для функционала strat моделей без параметров
    #  при глобальном рефакторинге: models.ForeignKey(ModelParameters, ...)
    #  либо работа только с таблицей ModelParameters
    produce_cycle = models.DecimalField(null=True, max_digits=10, decimal_places=2, default=1,
                                        verbose_name='Производственный цикл')

    plan_datetime = models.DateTimeField(null=True, verbose_name='дата/время выполнения планирования заказа',
                                         # # TODO убрать после переноса
                                         default=datetime.datetime.now(tz=datetime.timezone.utc))

    contract_start_date = models.DateField(null=True, verbose_name='Дата начала по договору',
                                           # # TODO убрать после переноса
                                           default=datetime.datetime.now(tz=datetime.timezone.utc))
    contract_end_date = models.DateField(null=True, verbose_name='Дата готовности по договору',
                                         # # TODO убрать после переноса
                                         default=datetime.datetime.now(tz=datetime.timezone.utc))
    calculated_datetime_done = models.DateField(null=True, verbose_name='Расчётная дата готовности',
                                                # # TODO убрать после переноса
                                                default=datetime.datetime.now(tz=datetime.timezone.utc))
    calculated_datetime_start = models.DateField(null=True, verbose_name='Расчётная дата запуска',
                                                 # # TODO убрать после переноса
                                                 default=datetime.datetime.now(tz=datetime.timezone.utc))

    is_fixed = models.BooleanField(verbose_name='фиксация в план', default=False)
    late_days = models.IntegerField(null=True, verbose_name='отставание дней', default=0)

    # def __str__(self):
    #     fields = [f"{field.name}: {getattr(self, field.name)}" for field in self._meta.fields]
    #     return "\n".join(fields)
    def __str__(self):
        return self.model_order_query

    def save(self, *args, **kwargs):
        """
        Копирование значения datetime_done в calculated_datetime_done
        при создании новой записи
        """
        if not self.calculated_datetime_done:
            self.calculated_datetime_done = self.datetime_done
        super().save(*args, **kwargs)

    class Meta:
        db_table = "workshop_schedule"
        verbose_name = 'График цеха'
        verbose_name_plural = 'График цеха'


class SeriesParameters(models.Model):
    """
    Модель параметров серии изделий (линейка котлов)
    """
    objects = models.Manager()  # явное указание метода для pycharm
    series_name = models.CharField(verbose_name='Название серии изделий')
    cycle_polynom_koef = ArrayField(models.DecimalField(null=True, max_digits=12, decimal_places=10), null=True,
                                    verbose_name='Коэффициенты формулы расчёта критической цепи по массе')
    """Коэффициенты формулы расчёта критической цепи по массе (коэффициенты полинома): 
    k4*x^4+k3*x^3+k2*x^2+k1*x^1+k0*x^0  
    Хранятся в иде списка cycle_formula = [k0, k1, k2, k3, k4]
    для получение полинома в цикле: cycle_formula += cycle_polynom_koef[index] * X ** index
    """
    difficulty_koef = models.DecimalField(max_digits=10, decimal_places=2, default=1,
                                          verbose_name='Коэффициент сложности изделия', null=True)

    class Meta:
        db_table = "series_parameters"
        verbose_name = 'Параметры серии'
        verbose_name_plural = 'Параметры серии'

    def __str__(self):
        return self.series_name


class ModelParameters(models.Model):
    """
    Модель ТТХ изделий
    """
    objects = models.Manager()  # явное указание метода для pycharm
    model_name = models.CharField(verbose_name='Модель изделия')
    model_weight = models.DecimalField(max_digits=10, decimal_places=2,  # обязательное поле для начала расчёта
                                       verbose_name='масса изделия')
    full_norm_tech = models.DecimalField(null=True, max_digits=10, decimal_places=2, default=0,
                                         verbose_name='Полная трудоёмкость изделия')
    critical_chain_cycle_koef = models.DecimalField(null=True, max_digits=10, decimal_places=2, default=0.6,
                                                    verbose_name='Коэффициент расчёта критической цепи')
    series_parameters = models.ForeignKey(SeriesParameters, on_delete=models.DO_NOTHING,
                                          null=True, verbose_name="Параметры серии")
    # расчётное поле по сигналу перед сохранением данных
    produce_cycle = models.DecimalField(null=True, max_digits=10, decimal_places=2, default=0,
                                        verbose_name='Производственный цикл')
    # расчётное поле по сигналу перед сохранением данных
    day_hours_amount = models.DecimalField(null=True, max_digits=10, decimal_places=2, default=0,
                                           verbose_name='Часов в день на изделие')

    class Meta:
        db_table = "model_parameters"
        verbose_name = 'Параметры модели'
        verbose_name_plural = 'Параметры модели'

    def __str__(self):
        return self.model_name


class Doers(models.Model):
    # TODO Прочитать (отсортировать, отфильтровать, скопировать?) данные
    #  из personal.Employee после запуска Personal на сервере
    """
    Таблица исполнителей
    """
    objects = models.Manager()  # явное указание метода для pycharm
    doers = models.CharField(max_length=255, unique=True, verbose_name='ФИО исполнителей')
    telegram_id = models.BigIntegerField(null=True, default=0, verbose_name='telegram_id исполнителя')
    is_approved = models.BooleanField(default=False, verbose_name='Одобрен')

    # TODO ФУНКЦИОНАЛ ЗАЯВИТЕЛЯ ПЛАЗМЫ И НОВОГО РАБОЧЕГО МЕСТА ТЕХНОЛОГА законсервировано
    # job_title = models.CharField(max_length=255, null=True, blank=True, verbose_name='Должность')
    # ws_plasma = models.PositiveSmallIntegerField(verbose_name='Цех плазмы (по умолчанию)', null=True, blank=True)

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
    op_name = models.TextField(verbose_name='Имя операции')
    ws_name = models.CharField(max_length=100, verbose_name='Имя рабочего центра')
    op_name_full = models.TextField(verbose_name='Полное имея операции')
    ws_number = models.CharField(max_length=10, verbose_name='Номер рабочего центра')
    norm_tech = models.DecimalField(null=True, max_digits=13, decimal_places=5,
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
    draw_path = models.CharField(max_length=254, null=True, blank=True, verbose_name='путь к связанным чертежам')
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
    doers_tech = models.IntegerField(null=True, blank=True, default=1, verbose_name='Количество исполнителей по ТД')
    norm_calc = models.DecimalField(null=True, blank=True, max_digits=13, decimal_places=5,
                                    verbose_name='Расчетная норма времени')

    # TODO ФУНКЦИОНАЛ ЗАЯВИТЕЛЯ ПЛАЗМЫ И НОВОГО РАБОЧЕГО МЕСТА ТЕХНОЛОГА законсервировано
    # # Пример структуры workpiece {
    # # "draw": "AGCC.287-6400-PB-01-KM1.DW-0037 - Блок Б57-1-Тип10_V18",
    # # "name": "Б1-1",
    # # "text": "Б1-1 Швеллер 30П ГОСТ 8240-97 С255-4 ГОСТ 27772-2015 L=7500 (2 шт.)",
    # # "count": "2",
    # # "layout_name": "4SP №order1 B-26 Balka №26 2", имя детали
    # # "layouts": {'12ГС-43.CNC': 1}
    # # "layouts_done": {'12ГС-44.CNC': 1}
    # # "layouts_total": 2 количество на всех раскладках
    # # "length": "7500",
    # # "material": "Швеллер 30П ГОСТ 8240-97 С255-4 ГОСТ 27772-2015",
    # # "fio_percentages": ['50', '50', '0', '0'],
    # # }
    # workpiece = models.JSONField(null=True, blank=True, verbose_name='Заготовка')
    # fio_tehnolog = models.CharField(max_length=255, null=True, blank=True,
    #                                 default='не распределено', verbose_name='ФИО технолога')
    # plasma_layout = models.CharField(max_length=255, null=True, blank=True,
    #                                  default='Не выполнена', verbose_name='Раскладка')
    # workshop_plasma = models.PositiveSmallIntegerField(verbose_name='Цех плазмы', null=True, blank=True)
    # tech_id = models.PositiveIntegerField(verbose_name='id в техпроцессе', null=True, blank=True)

    class Meta:
        db_table = "shift_task"
        verbose_name = 'Сменное задание'
        verbose_name_plural = 'Сменные задания'

    # TODO ФУНКЦИОНАЛ ЗАЯВИТЕЛЯ ПЛАЗМЫ И НОВОГО РАБОЧЕГО МЕСТА ТЕХНОЛОГА законсервировано
    # def add_next(self, new_shift_task: 'ShiftTask'):
    #     Task2Task.objects.create(previous=self, next=new_shift_task)

# TODO ЗАКОНСЕРВИРОВАНО Функционал простоев
# class Downtime(models.Model):
#     objects = models.Manager()
#     shift_task = models.ForeignKey(
#         'ShiftTask', on_delete=models.CASCADE, related_name='downtimes', verbose_name='СЗ'
#     )
#     status = models.CharField(max_length=254, default='не подтверждено', verbose_name='Статус')
#     reason = models.CharField(max_length=50, verbose_name='Причина')
#     description = models.CharField(max_length=254, default='', verbose_name='Описание')
#     datetime_creation = models.DateTimeField(auto_now_add=True, verbose_name='Время создания записи')
#     datetime_start = models.DateTimeField(null=True, blank=True, verbose_name='Время начала простоя')
#     datetime_end = models.DateTimeField(null=True, blank=True, verbose_name='Время окончания простоя')
#     datetime_decision = models.DateTimeField(null=True, blank=True, verbose_name='Время решения')
#     master_decision_fio = models.CharField(max_length=30, null=True, blank=True, verbose_name='ФИО мастера')
#
#     class Meta:
#         db_table = "downtime"
#         verbose_name = 'Простой'
#         verbose_name_plural = 'Простои'

# TODO ФУНКЦИОНАЛ ЗАЯВИТЕЛЯ ПЛАЗМЫ И НОВОГО РАБОЧЕГО МЕСТА ТЕХНОЛОГА законсервировано
# class Task2Task(models.Model):
#     previous = models.ForeignKey('ShiftTask', on_delete=models.CASCADE, related_name="next")
#     next = models.ForeignKey('ShiftTask', on_delete=models.CASCADE, related_name="previous")

# class DailyReport(models.Model): # TODO ФУНКЦИОНАЛ ОТЧЁТОВ ЗАКОНСЕРВИРОВАНО не используется.
#     """
#     Данные для ежедневных отчётов
#     """
#     objects = models.Manager()
#     calendar_day = models.DateField(verbose_name="Дата отчёта")
#     day_plan = models.DecimalField(decimal_places=1, max_digits=10, verbose_name="План на день", default=0)
#     day_fact = models.DecimalField(decimal_places=1, max_digits=10, verbose_name="Факт за день", default=0)
#
#     aver_fact = models.DecimalField(decimal_places=2, max_digits=10, verbose_name="Отставание/опережение плана",
#                                          default=0)
#
#     day_plan_rate = models.DecimalField(decimal_places=2, max_digits=10, verbose_name="% выполнения плана за день",
#                                         default=0)
#
#     plan_sum = models.DecimalField(decimal_places=1, max_digits=10, verbose_name="Всего план на дату", default=0)
#     fact_sum = models.DecimalField(decimal_places=1, max_digits=10, verbose_name="Всего факт на дату", default=0)
#
#     plan_done_rate = models.DecimalField(decimal_places=2, max_digits=10, verbose_name="% выполнения плана",
#                                          default=0)
#     fact_done_rate = models.DecimalField(decimal_places=2, max_digits=10, verbose_name="Фактический % выполнения плана",
#                                          default=0)
#     plan_loos_rate = models.DecimalField(decimal_places=2, max_digits=10, verbose_name="Отставание/опережение плана",
#                                          default=0)
#     day_fails = models.PositiveSmallIntegerField(verbose_name="Случаев брака за день", default=0)
#     day_save_violations = models.PositiveSmallIntegerField(verbose_name="Случаев нарушений ОТПБ за день", default=0)
#     month_plan_data = models.ForeignKey(to='MonthPlans', on_delete=models.PROTECT,
#                                         related_name="month_plan_table",
#                                         null=True, blank=True,
#                                         verbose_name="Месяц планирования")
#     workshop = models.PositiveSmallIntegerField(verbose_name="Цех", default=0)
#     # работники
#     personal_total = models.PositiveSmallIntegerField(verbose_name='Всего персонала в цехе', default=0)
#     personal_shift = models.PositiveSmallIntegerField(verbose_name='Выход в дату персонала', default=0)
#
#     personal_total_welders = models.PositiveSmallIntegerField(verbose_name='Всего сварщиков', default=0)
#     personal_shift_welders = models.PositiveSmallIntegerField(verbose_name='Выход в дату сварщиков', default=0)
#     personal_night_welders = models.PositiveSmallIntegerField(verbose_name='Выход ночь сварщики', default=0)
#
#     personal_total_locksmiths = models.PositiveSmallIntegerField(verbose_name='Всего слесарей', default=0)
#     personal_shift_locksmiths = models.PositiveSmallIntegerField(verbose_name='Выход в дату слесарей', default=0)
#     personal_night_locksmiths = models.PositiveSmallIntegerField(verbose_name='Выход ночь слесаря', default=0)
#
#     personal_total_painters = models.PositiveSmallIntegerField(verbose_name='Всего маляров', default=0)
#     personal_shift_painters = models.PositiveSmallIntegerField(verbose_name='Выход маляров', default=0)
#     personal_night_painters = models.PositiveSmallIntegerField(verbose_name='Выход ночь маляры', default=0)
#
#     personal_total_turners = models.PositiveSmallIntegerField(verbose_name='Всего токарей', default=0)
#     personal_shift_turners = models.PositiveSmallIntegerField(verbose_name='Выход токарей', default=0)
#     personal_night_turners = models.PositiveSmallIntegerField(verbose_name='Выход ночь токаря', default=0)
#
#     class Meta:
#         db_table = "report"
#         verbose_name = 'Ежедневный отчёт'
#         verbose_name_plural = 'Ежедневные отчёты'


# class MonthPlans(models.Model):  # TODO ФУНКЦИОНАЛ ОТЧЁТОВ ЗАКОНСЕРВИРОВАНО не используется.
#     """
#     Ежемесячные значения плана
#     """
#     objects = models.Manager()
#     month_plan = models.DateField(verbose_name="Месяц планирования")
#     month_plan_amount = models.DecimalField(decimal_places=1, max_digits=10, verbose_name="План на месяц в н/ч",
#                                             default=0)
#     workshop = models.PositiveSmallIntegerField(verbose_name="Цех", default=0)
#
#     class Meta:
#         db_table = "month_plan_table"
#         verbose_name = 'План на месяц в н/ч'
#         verbose_name_plural = 'Планы на месяц в н/ч'

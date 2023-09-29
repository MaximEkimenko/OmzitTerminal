from django.db import models
from django.forms import ModelChoiceField
from tehnolog.models import ProductCategory


class WorkshopSchedule(models.Model):
    """
    Данные для планирования цеха, статусы заказов, статусы чертежей
    """
    objects = models.Manager()  # явное указание метода для pycharm
    workshop = models.PositiveSmallIntegerField(verbose_name='Цех')
    model_name = models.CharField(max_length=30, verbose_name='Модель изделия')
    datetime_done = models.DateField(null=True, verbose_name='Планируемая дата готовности')
    order = models.CharField(max_length=100, verbose_name='Номер заказа')
    order_status = models.CharField(max_length=20, default='не запланировано', verbose_name='Статус заказа')
    model_query = models.CharField(max_length=60, null=True, verbose_name='заказ и модель')
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
    tehnolog_query_td_fio = models.CharField(max_length=30, null=True, verbose_name='Утвердил')
    tehnolog_excel_load_fio = models.CharField(max_length=30, null=True, verbose_name='Загрузил')



    class Meta:
        db_table = "workshop_schedule"
        verbose_name = 'График цеха'
        verbose_name_plural = 'График цеха'

    def __str__(self):
        return str(self.datetime_done)


class Doers(models.Model):
    # TODO синхронизация с 1С
    """
    Таблица исполнителей
    """
    objects = models.Manager()  # явное указание метода для pycharm
    doers = models.CharField(max_length=255, unique=True, verbose_name='ФИО исполнителей')

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
    # поля
    workshop = models.PositiveSmallIntegerField(verbose_name='Цех')
    model_name = models.CharField(max_length=30, db_index=True, verbose_name='Модель изделия')
    datetime_done = models.DateField(verbose_name='Ожидаемая дата готовности')
    order = models.CharField(max_length=100, verbose_name='Номер заказа')
    op_number = models.CharField(max_length=20, verbose_name='Номер операции')
    op_name = models.CharField(max_length=200, verbose_name='Имя операции')
    ws_name = models.CharField(max_length=100, verbose_name='Имя рабочего центра')
    op_name_full = models.CharField(max_length=255, verbose_name='Полное имея операции')
    ws_number = models.CharField(max_length=10, verbose_name='Номер рабочего центра')
    norm_tech = models.DecimalField(null=True, max_digits=10, decimal_places=2,
                                    verbose_name='Технологическая норма времени')
    datetime_techdata_create = models.DateTimeField(verbose_name='дата/время создания технологических данных')
    datetime_techdata_update = models.DateTimeField(verbose_name='дата/время технологических данных')
    ###
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

    # технологические данные (унаследовано из TechData)
    datetime_create = models.DateTimeField(auto_now_add=True, verbose_name='дата/время добавления данных в таблицу',
                                           null=True)
    datetime_update = models.DateTimeField(auto_now=True, verbose_name='дата/время обновления данных таблицы',
                                           null=True)
    # TODO после очистки базы убрать null=True
    draw_path = models.CharField(max_length=255, null=True, blank=True, verbose_name='путь к связанным чертежам')
    draw_filename = models.TextField(null=True, blank=True, verbose_name='имя чертежа')
    product_category = models.ForeignKey(to=ProductCategory, on_delete=models.DO_NOTHING, null=True,
                                         verbose_name='Категория изделия')

    class Meta:
        db_table = "shift_task"
        verbose_name = 'Сменное задание'
        verbose_name_plural = 'Сменные задание'


from django.db import models
from django.forms import ModelChoiceField


class WorkshopSchedule(models.Model):
    """
    Таблица графика цеха
    """
    objects = models.Manager()  # явное указание метода для pycharm

    workshop = models.PositiveSmallIntegerField()  # номер цеха
    model_name = models.CharField(max_length=30)  # имя модели (заказа) изделия
    datetime_done = models.DateField()  # планируемая дата готовности
    order = models.CharField(max_length=100)  # номер заказа
    order_status = models.CharField(max_length=20, default='запланировано')

    class Meta:
        db_table = "workshop_schedule"
        verbose_name = 'График цеха'
        verbose_name_plural = 'График цеха'

    def __str__(self):
        return str(self.datetime_done)


class Doers(models.Model):
    """
    Таблица исполнителей
    """
    objects = models.Manager()  # явное указание метода для pycharm
    doers = models.CharField(max_length=255, unique=True)


    class Meta:
        db_table = "doers"
        verbose_name = 'Исполнитель'
        verbose_name_plural = 'Исполнители'

    def __str__(self):
        return self.doers



class ShiftTask(models.Model):
    """
    Модель данных сменного задания основная модель всего терминала
    """
    objects = models.Manager()  # явное указание метода для pycharm
    # поля
    workshop = models.PositiveSmallIntegerField()  # номер цеха
    model_name = models.CharField(max_length=30, db_index=True)  # имя модели (заказа) изделия
    datetime_done = models.DateField()  # ожидаемая дата готовности
    order = models.CharField(max_length=100)  # номер заказа
    op_number = models.CharField(max_length=20)  # номер операции
    op_name = models.CharField(max_length=200)  # имя операции
    ws_name = models.CharField(max_length=100)  # имя рабочего центра
    op_name_full = models.CharField(max_length=255)  # полное имея операции (имя операции + имя рабочего центра)
    ws_number = models.CharField(max_length=10)  # номер рабочего центра
    norm_tech = models.DecimalField(null=True, max_digits=10, decimal_places=2)  # норма времени рабочего центра
    datetime_techdata_create = models.DateTimeField()  # дата/время создания технологических данных
    datetime_techdata_update = models.DateTimeField()  # дата/время технологических данных
    ###
    datetime_plan_ws = models.DateTimeField(auto_now=True)  # время планирования в цех
    datetime_plan_wp = models.DateTimeField(null=True)  # время планирования РЦ
    fio_doer = models.CharField(max_length=255, null=True, default='не распределено')  # ФИО исполнителя
    datetime_assign_wp = models.DateTimeField(null=True)  # время распределения
    datetime_job_start = models.DateTimeField(null=True)  # время начала работ
    datetime_master_call = models.DateTimeField(null=True)  # время вызова мастера
    master_finish_wp = models.CharField(max_length=30, null=True)  # ФИО мастера вызова ОТК
    datetime_otk_call = models.DateTimeField(null=True)  # время вызова ОТК
    datetime_otk_answer = models.DateTimeField(null=True)  # время ответа ОТК
    master_calls = models.IntegerField(null=True, default=0)  # количество вызовов мастера
    master_called = models.CharField(max_length=10, null=True, default='не было')  # статус вызова мастера
    # фактическая норма времени рабочего центра
    norm_fact = models.DecimalField(null=True, max_digits=10, decimal_places=2)
    otk_answer = models.CharField(max_length=30, null=True)  # ФИО контролёра ответа ОТК
    otk_decision = models.CharField(max_length=30, null=True)  # ФИО контролёра решения ОТК
    decision_time = models.DateTimeField(null=True)  # время приёмки ОТК
    st_status = models.CharField(max_length=20, default='не запланировано')
    is_fail = models.BooleanField(null=True, default=False)  # факт наличия брака
    datetime_fail = models.DateTimeField(null=True)  # время фиксации брака
    fio_failer = models.CharField(max_length=255, null=True)  # ФИО бракоделов
    ###

    dispatcher_plan_ws = models.CharField(max_length=30, null=True)  # ФИО диспетчера планирования цеха TODO реализовать
    dispatcher_plan_wp = models.CharField(max_length=30, null=True)  # ФИО диспетчера планирования РЦ TODO реализовать
    master_assign_wp = models.CharField(max_length=30, null=True)  # ФИО мастера распределения РЦ TODO реализовать

    class Meta:
        db_table = "shift_task"
        verbose_name = 'Технологические данные'
        verbose_name_plural = 'Технологические данные'


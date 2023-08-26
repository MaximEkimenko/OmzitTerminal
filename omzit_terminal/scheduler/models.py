from django.db import models


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




class ShiftTask(models.Model):
    """
    Модель данных сменного задания основная модель всего терминала
    """
    objects = models.Manager()  # явное указание метода для pycharm
    # поля
    workshop = models.PositiveSmallIntegerField()  # номер цеха
    model_name = models.CharField(max_length=30, db_index=True)  # имя модели (заказа) изделия
    datetime_done = models.DateField()  # время ответа ОТК
    order = models.CharField(max_length=100)  # номер заказа
    op_number = models.CharField(max_length=20)  # номер операции
    op_name = models.CharField(max_length=200)  # имя операции
    ws_name = models.CharField(max_length=100)  # имя рабочего центра
    op_name_full = models.CharField(max_length=255)  # полное имея операции (имя операции + имя рабочего центра)
    ws_number = models.CharField(max_length=10)  # номер рабочего центра
    norm_tech = models.FloatField(null=True, blank=True)  # норма времени рабочего центра
    datetime_techdata_create = models.DateTimeField()  # дата/время создания технологических данных
    datetime_techdata_update = models.DateTimeField()  # дата/время технологических данных

    datetime_plan_ws = models.DateTimeField(auto_now=True)  # время планирования в цех
    datetime_plan_wp = models.DateTimeField(null=True)  # время планирования РЦ
    datetime_assign_wp = models.DateTimeField(null=True)  # время распределения
    datetime_job_start = models.DateTimeField(null=True)  # время начала работ
    datetime_master_call = models.DateTimeField(null=True)  # время вызова мастера
    datetime_otk_call = models.DateTimeField(null=True)  # время вызова ОТК
    datetime_otk_answer = models.DateTimeField(null=True)  # время ответа ОТК
    master_calls = models.IntegerField(null=True)  # Количество вызовов мастера
    norm_fact = models.FloatField(null=True)  # фактическая норма времени рабочего центра
    otk_decision = models.CharField(max_length=30, null=True)  # Решение ОТК
    decision_time = models.DateTimeField(null=True)  # длительность приёмки
    st_status = models.CharField(max_length=20, default='не запланировано')
    ###
    otk_answer = models.CharField(max_length=30, null=True)  # ФИО контролёра ответа ОТК TODO реализовать
    master_finish_wp = models.CharField(max_length=30, null=True)  # ФИО мастера вызова ОТК TODO реализовать
    dispatcher_plan_ws = models.CharField(max_length=30, null=True)  # ФИО диспетчера планирования цеха TODO реализовать
    dispatcher_plan_wp = models.CharField(max_length=30, null=True)  # ФИО диспетчера планирования РЦ TODO реализовать
    master_assign_wp = models.CharField(max_length=30, null=True)  # ФИО мастера распределения РЦ TODO реализовать

    class Meta:
        db_table = "shift_task"
        verbose_name = 'Технологические данные'
        verbose_name_plural = 'Технологические данные'

    def __str__(self):
        return self.ws_number

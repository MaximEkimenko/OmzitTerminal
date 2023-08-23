from django.db import models


class ProductCategory(models.Model):
    """
    Таблица категории изделия
    """
    category_name = models.CharField(max_length=20, db_index=True)  # имя категории
    objects = models.Manager()  # явное указание метода для pycharm

    class Meta:
        db_table = "product_category"
        verbose_name = 'Категория изделия'
        verbose_name_plural = 'Категории изделий'

    def __str__(self):
        return self.category_name


class TechData(models.Model):
    """
    Таблица технологических данных
    """
    objects = models.Manager()  # явное указание метода для pycharm
    model_name = models.CharField(max_length=30, db_index=True)  # имя модели (заказа) изделия
    op_number = models.CharField(max_length=20)  # номер операции
    op_name = models.CharField(max_length=200)  # имя операции
    ws_name = models.CharField(max_length=100)  # имя рабочего центра
    op_name_full = models.CharField(max_length=255)  # полное имея операции (имя операции + имя рабочего центра)
    ws_number = models.CharField(max_length=10)  # номер рабочего центра
    norm_tech = models.FloatField(null=True)  # норма времени рабочего центра
    datetime_create = models.DateTimeField(auto_now_add=True)  # дата/время добавления данных в таблицу
    datetime_update = models.DateTimeField(auto_now=True)  # дата/время обновления данных таблицы
    is_planned = models.BooleanField(default=False)  # было ли изделие хотя бы раз запланировано
    product_category = models.ForeignKey(to=ProductCategory, on_delete=models.DO_NOTHING)

    class Meta:
        db_table = "tech_data"
        verbose_name = 'Технологические данные'
        verbose_name_plural = 'Технологические данные'






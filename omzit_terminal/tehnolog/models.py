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


# TODO удалить после замены на модель в scheduler
# class ProductModel(models.Model):
#     """
#     Таблица моделей изделий
#     """
#     objects = models.Manager()  # явное указание метода для pycharm
#     model_name = models.CharField(max_length=20, db_index=True)  # имя модели
#
#     class Meta:
#         db_table = "model_name"
#         verbose_name = 'Модель изделия'
#         verbose_name_plural = 'Модель изделий'
#
#     def __str__(self):
#         return self.model_name


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
    norm_tech = models.FloatField(null=True, blank=True)  # норма времени рабочего центра
    datetime_create = models.DateTimeField(auto_now_add=True)  # дата/время добавления данных в таблицу
    datetime_update = models.DateTimeField(auto_now=True)  # дата/время обновления данных таблицы
    # TODO после очистки базы убрать null=True
    draw_path = models.CharField(max_length=255, null=True, blank=True)  # путь к связанным чертежам
    draw_filename = models.TextField(null=True, blank=True)  # имя чертежа в формате pdf

    product_category = models.ForeignKey(to=ProductCategory, on_delete=models.DO_NOTHING)  # категория изделия

    class Meta:
        db_table = "tech_data"
        verbose_name = 'Технологические данные'
        verbose_name_plural = 'Технологические данные'

# TODO ФУНКЦИОНАЛ ЗАЯВИТЕЛЯ ПЛАЗМЫ И НОВОГО РАБОЧЕГО МЕСТА ТЕХНОЛОГА законсервировано
# # Модели базы данных SIGMA
#
# class Pip(models.Model):
#     wo_number = models.CharField(db_column='WONumber', primary_key=True, max_length=50)
#     part_name = models.CharField(db_column='PartName', max_length=100)
#     program_name = models.CharField(db_column='ProgramName', max_length=50)
#     repeat_id = models.IntegerField(db_column='RepeatID')
#     qty_in_process = models.IntegerField(db_column='QtyInProcess', blank=True, null=True)
#     cutting_time = models.FloatField(db_column='CuttingTime', blank=True, null=True)
#     cutting_length = models.FloatField(db_column='CuttingLength', blank=True, null=True)
#     pierce_qty = models.IntegerField(db_column='PierceQty', blank=True, null=True)
#     total_cutting_time = models.FloatField(db_column='TotalCuttingTime', blank=True, null=True)
#     master_part_qty = models.IntegerField(db_column='MasterPartQty', blank=True, null=True)
#     wo_state = models.IntegerField(db_column='WOState', blank=True, null=True)
#     pk_pip = models.CharField(db_column='PK_PIP', max_length=36)
#
#     class Meta:
#         managed = False
#         db_table = 'pip'
#
#
# class Program(models.Model):
#     program_name = models.CharField(db_column='ProgramName', primary_key=True, max_length=50)
#     repeat_id = models.IntegerField(db_column='RepeatID')
#     qty_in_process = models.IntegerField(db_column='QtyInProcess', blank=True, null=True)
#     cutting_time = models.FloatField(db_column='CuttingTime', blank=True, null=True)
#     pierce_qty = models.IntegerField(db_column='PierceQty', blank=True, null=True)
#     post_datetime = models.DateTimeField(db_column='PostDateTime', blank=True, null=True)
#     material = models.CharField(db_column='Material', max_length=150, blank=True, null=True)
#     thickness = models.FloatField(db_column='Thickness', blank=True, null=True)
#     posted_by_user_id = models.IntegerField(db_column='PostedByUserID', blank=True, null=True)
#     pk_program = models.CharField(db_column='PK_PROGRAM', max_length=36)
#
#     class Meta:
#         managed = False
#         db_table = 'program'

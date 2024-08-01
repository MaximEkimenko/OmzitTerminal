from datetime import date, datetime

from django.db import models
from django.db.models import OuterRef, Subquery, QuerySet, Max
from django.urls import reverse_lazy
from django.utils.timezone import now, make_aware
from scheduler.models import ShiftTask


class DefectAct(models.Model):
    CHOICES = (
        ('EXC', 'ошибка исполнителя'),
        ('TEC', 'ошибка технолога'),
        ('CON', 'ошибка конструктора'),
        ('MAT', 'брак материала')
    )

    shift_task = models.ForeignKey(ShiftTask, on_delete=models.CASCADE,
                                   null=True, verbose_name="Ссылка на сменное задание")
    datetime_fail = models.DateTimeField(null=False, verbose_name='Дата')
    # для отслеживания, какой номер акта актуальный
    tech_number = models.IntegerField(verbose_name="Технический номер акта", db_index=True)
    act_number = models.CharField(max_length=60, null=False, verbose_name='№ Акта', unique=True)
    workshop = models.PositiveSmallIntegerField(verbose_name='Цех', null=True, blank=True)
    operation = models.CharField(max_length=255, null=False, blank=True, verbose_name='Операция')
    processing_object = models.CharField(max_length=255, null=True, blank=True,  verbose_name='Объект')
    control_object = models.CharField(max_length=255, null=True, blank=True, verbose_name='Объект контроля')
    quantity = models.IntegerField(verbose_name='количество', null=True, blank=True )
    inconsistencies = models.CharField(max_length=1000, null=True, blank=True, verbose_name="Выявленные несоответствия")
    remark = models.CharField(max_length=1000, null=True, blank=True, verbose_name="Примечание")
    tech_service = models.CharField(max_length=255, null=True, blank=True, verbose_name='Тех. служба')
    tech_solution = models.CharField(max_length=1000, null=True, blank=True, verbose_name='Тех. решение')
    fixable = models.BooleanField(verbose_name="брак исправимый", null=True, blank=True)
    fio_failer = models.CharField(max_length=255, null=True, blank=True,  verbose_name='Исполнитель')
    fixing_time = models.DurationField(null=True, blank=True, verbose_name="Время исправления")
    cause = models.CharField(max_length=4, choices=CHOICES, null=True, blank=True, verbose_name='Причина')
    master_finish_wp = models.CharField(max_length=30, null=True, blank=True, verbose_name='Ответственный мастер')
    completed = models.BooleanField(default=False, verbose_name="Заполнены все необходимые поля")
    media_ref = models.CharField(max_length=255, null=True,  verbose_name="Папка с файлами")
    media_count = models.IntegerField(default=0, verbose_name="количество файлов в папке")

    class Meta:
        ordering = ['tech_number']
        verbose_name = "Акт о браке"
        verbose_name_plural = "Акты о браке"

    def str(self):
        return self.abv

    def get_absolute_url(self):
        return reverse_lazy("controller:edit", kwargs={'pk': self.pk})

    @classmethod
    def last_act_number(cls) -> int:
        query = cls.objects.aggregate(last_num=Max("tech_number"))
        return query["last_num"]

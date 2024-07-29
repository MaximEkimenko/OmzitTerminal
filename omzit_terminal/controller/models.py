from datetime import date, datetime

from django.db import models
from django.db.models import OuterRef, Subquery, QuerySet
from django.urls import reverse_lazy
from django.utils.timezone import now, make_aware


class DefectAct(models.Model):
    CHOICES = (
        ('EXC', 'ошибка исполнителя'),
        ('TEC', 'ошибка технолога'),
        ('CON', 'ошибка конструктора'),
        ('MAT', 'брак материала')
    )

    datetime_fail = models.DateTimeField(null=False, verbose_name='Дата')
    act_number = models.CharField(max_length=60, null=False, verbose_name='№ Акта')
    workshop = models.PositiveSmallIntegerField(verbose_name='Цех', null=True)
    operation = models.CharField(max_length=255, null=False, verbose_name='Операция')
    processing_object = models.CharField(max_length=255, null=True, verbose_name='Объект')
    control_object = models.CharField(max_length=255, null=True, verbose_name='Объект контроля')
    quantity = models.IntegerField(verbose_name='количество', null=True)
    inconsistencies = models.CharField(max_length=1000, null=True, verbose_name="Выявленные несоответствия")
    remark = models.CharField(max_length=1000, null=True, verbose_name="Примечание")
    tech_service = models.CharField(max_length=255, null=True, verbose_name='Тех. служба')
    tech_solution = models.CharField(max_length=1000, null=True, verbose_name='Тех. решение')
    fixable = models.BooleanField(verbose_name="брак исправимый", null=True)
    media = models.CharField(max_length=255, null=True, blank=True,  verbose_name='Ссылка на файлы')
    fio_failer = models.CharField(max_length=255, null=True, verbose_name='Виновник')
    fixing_time = models.DurationField(null=True, verbose_name="Время исправления")
    cause = models.CharField(max_length=4, choices=CHOICES, null=True, verbose_name='Причина')
    master_finish_wp = models.CharField(max_length=30, null=True, verbose_name='Ответственный мастер')
    completed = models.BooleanField(default=False, blank=True, verbose_name="Форма заполнена")

    class Meta:
        ordering=['-datetime_fail']

    def str(self):
        return self.abv

    def get_absolute_url(self):
        return reverse_lazy("controller:edit", kwargs={'pk': self.pk})

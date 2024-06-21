from django.db.models.signals import pre_save
from django.dispatch import receiver
from .models import ModelParameters


@receiver(pre_save, sender=ModelParameters)
def auto_fill_produce_cycle_and_day_hours_amount(sender, instance, **kwargs) -> None:
    """
    Заполнение расчётных параметров модели перед сохранением
    :param sender:
    :param instance:
    :param kwargs:
    :return: None
    """
    # TODO!
    instance.produce_cycle = instance.difficulty_koef * instance.model_weight
    instance.day_hours_amount = 222.22
    #



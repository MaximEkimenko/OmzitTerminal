from django.db.models.signals import pre_save
from django.dispatch import receiver
from .models import ModelParameters, SeriesParameters
from decimal import Decimal


@receiver(pre_save, sender=ModelParameters)
def auto_fill_produce_cycle_and_day_hours_amount(sender, instance, **kwargs) -> None:
    """
    Заполнение расчётных параметров модели перед сохранением
    :param sender:
    :param instance:
    :param kwargs:
    :return: None
    """
    series_data = SeriesParameters.objects.get(id=instance.series_parameters_id)
    # расчёт цикла производства
    polynom = 0
    x = Decimal(instance.model_weight)  # масса изделия для полинома
    print(f"{x=}")
    print(f"{series_data.cycle_polynom_koef=}")
    for power in range(len(series_data.cycle_polynom_koef)):  # заполнение полинома

        print(f"{power=}")
        polynom_part = series_data.cycle_polynom_koef[power] * x ** power
        print(f"{polynom_part=}")
        polynom += polynom_part
        print(f"{polynom=}")

    # print(f"resulting_polynom = {polynom}")
    instance.produce_cycle = (polynom * series_data.difficulty_koef + 7)  # условно добавлено 7 дней на заготовку
    # заполнение трудочасов в смену в зависимости от серии
    if series_data.series_name == 'ML':
        instance.day_hours_amount = 20
    elif series_data.series_name == 'DMH':
        instance.day_hours_amount = 20
    elif series_data.series_name == 'OV':
        instance.day_hours_amount = 20
    elif series_data.series_name == 'SV':
        instance.day_hours_amount = 20
    elif series_data.series_name == 'R':
        instance.day_hours_amount = 17
    elif series_data.series_name == 'P':
        instance.day_hours_amount = 17
    elif series_data.series_name == 'M':
        instance.day_hours_amount = 17








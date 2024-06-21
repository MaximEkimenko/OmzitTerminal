"""
TODO создать рабочее место технолога для занесения и корректировки
Занесение исходных данных для стратегического планирования
"""
from decimal import Decimal

from scheduler.models import SeriesParameters # noqa
from m_logger_settings import logger  # noqa


def series_parameters_set() -> None:
    """
    Первоначальное заполнение параметров серий
    :return: None
    """
    # полный по сериям массив данных
    new_series_parameters = [
        {
            'series_name': 'ML',
            'cycle_polynom_koef': list(reversed([Decimal('0.0003'), Decimal('-0.0150'), Decimal('0.2010'),
                                                 Decimal('1.0065'), Decimal('16.2077')])),
            'difficulty_koef': Decimal('1.3')
        },
        {
            'series_name': 'DMH',
            'cycle_polynom_koef': list(reversed([Decimal('-0.0001'), Decimal('0.0118'), Decimal('-0.3481'),
                                                 Decimal('5.2202'), Decimal('3.6799')])),
            'difficulty_koef': Decimal('1.5')

        },
        {
            'series_name': 'OV',
            'cycle_polynom_koef': list(reversed([Decimal('-0.0001'), Decimal('0.0118'), Decimal('-0.3481'),
                                                 Decimal('5.2202'), Decimal('3.6799')])),
            'difficulty_koef': Decimal('1.3')
        },
        {
            'series_name': 'SV',
            'cycle_polynom_koef': list(reversed([Decimal('-0.0001'), Decimal('0.0118'), Decimal('-0.3481'),
                                                 Decimal('5.2202'), Decimal('3.6799')])),
            'difficulty_koef': Decimal('1')
        },
        {
            'series_name': 'R',
            'cycle_polynom_koef': list(reversed([Decimal('0.2145'), Decimal('-2.0039'), Decimal('6.0821'),
                                                 Decimal('-3.8229'), Decimal('6.1299')])),
            'difficulty_koef': Decimal('1')
        },
        {
            'series_name': 'P',
            'cycle_polynom_koef': list(reversed([Decimal('-0.0001'), Decimal('0.0062'), Decimal('-0.1649'),
                                                 Decimal('3.1292'), Decimal('12.6241')])),
            'difficulty_koef': Decimal('1')
        },
        {
            'series_name': 'M',
            'cycle_polynom_koef': list(reversed([Decimal('0.0003'), Decimal('-0.0150'), Decimal('0.2010'),
                                                 Decimal('1.0065'), Decimal('16.2077')])),
            'difficulty_koef': Decimal('1')
        },
    ]
    # добавление/обновление БД
    for data in new_series_parameters:
        try:
            parameters = SeriesParameters.objects.get(series_name=data['series_name'])
            if (parameters.cycle_polynom_koef != data['cycle_polynom_koef']
                    or parameters.difficulty_koef != data['difficulty_koef']):
                parameters.cycle_polynom_koef = data['cycle_polynom_koef']
                parameters.difficulty_koef = data['difficulty_koef']
                parameters.save()
                logger.info(f'{parameters} был обновлён')
            else:
                logger.debug(f'{parameters} изменений не обнаружено.')
        except SeriesParameters.DoesNotExist():
            SeriesParameters.objects.create(series_name=data['series_name'],
                                            cycle_polynom_koef=data['cycle_polynom_koef'],
                                            difficulty_koef=data['difficulty_koef'])
            logger.info(f'Параметры новой серии {data["series_name"]} были добавлены.')




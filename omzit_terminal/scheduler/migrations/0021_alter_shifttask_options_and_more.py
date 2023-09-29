# Generated by Django 4.2.4 on 2023-09-27 05:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('scheduler', '0020_alter_workshopschedule_done_rate'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='shifttask',
            options={'verbose_name': 'Сменное задание', 'verbose_name_plural': 'Сменные задание'},
        ),
        migrations.RemoveField(
            model_name='shifttask',
            name='dispatcher_plan_wp',
        ),
        migrations.RemoveField(
            model_name='shifttask',
            name='dispatcher_plan_ws',
        ),
        migrations.RemoveField(
            model_name='shifttask',
            name='master_assign_wp',
        ),
        migrations.AddField(
            model_name='shifttask',
            name='master_assign_wp_fio',
            field=models.CharField(max_length=30, null=True, verbose_name='Распределил'),
        ),
        migrations.AddField(
            model_name='workshopschedule',
            name='dispatcher_plan_ws_fio',
            field=models.CharField(max_length=30, null=True, verbose_name='Запланировал'),
        ),
        migrations.AddField(
            model_name='workshopschedule',
            name='dispatcher_query_td_fio',
            field=models.CharField(max_length=30, null=True, verbose_name='Запросил КД'),
        ),
        migrations.AlterField(
            model_name='doers',
            name='doers',
            field=models.CharField(max_length=255, unique=True, verbose_name='ФИО исполнителей'),
        ),
        migrations.AlterField(
            model_name='shifttask',
            name='datetime_assign_wp',
            field=models.DateTimeField(null=True, verbose_name='время распределения'),
        ),
        migrations.AlterField(
            model_name='shifttask',
            name='datetime_done',
            field=models.DateField(verbose_name='Ожидаемая дата готовности'),
        ),
        migrations.AlterField(
            model_name='shifttask',
            name='datetime_fail',
            field=models.DateTimeField(null=True, verbose_name='Время регистрации брака'),
        ),
        migrations.AlterField(
            model_name='shifttask',
            name='datetime_job_start',
            field=models.DateTimeField(null=True, verbose_name='время начала работ'),
        ),
        migrations.AlterField(
            model_name='shifttask',
            name='datetime_master_call',
            field=models.DateTimeField(null=True, verbose_name='время вызова мастера'),
        ),
        migrations.AlterField(
            model_name='shifttask',
            name='datetime_otk_answer',
            field=models.DateTimeField(null=True, verbose_name='время ответа ОТК'),
        ),
        migrations.AlterField(
            model_name='shifttask',
            name='datetime_otk_call',
            field=models.DateTimeField(null=True, verbose_name='время вызова ОТК'),
        ),
        migrations.AlterField(
            model_name='shifttask',
            name='datetime_plan_wp',
            field=models.DateTimeField(null=True, verbose_name='время планирования РЦ'),
        ),
        migrations.AlterField(
            model_name='shifttask',
            name='datetime_plan_ws',
            field=models.DateTimeField(auto_now=True, verbose_name='время планирования в цех'),
        ),
        migrations.AlterField(
            model_name='shifttask',
            name='datetime_techdata_create',
            field=models.DateTimeField(verbose_name='дата/время создания технологических данных'),
        ),
        migrations.AlterField(
            model_name='shifttask',
            name='datetime_techdata_update',
            field=models.DateTimeField(verbose_name='дата/время технологических данных'),
        ),
        migrations.AlterField(
            model_name='shifttask',
            name='decision_time',
            field=models.DateTimeField(null=True, verbose_name='Время приёмки ОТК'),
        ),
        migrations.AlterField(
            model_name='shifttask',
            name='fio_doer',
            field=models.CharField(default='не распределено', max_length=255, null=True, verbose_name='ФИО исполнителей'),
        ),
        migrations.AlterField(
            model_name='shifttask',
            name='fio_failer',
            field=models.CharField(max_length=255, null=True, verbose_name='ФИО бракоделов'),
        ),
        migrations.AlterField(
            model_name='shifttask',
            name='is_fail',
            field=models.BooleanField(default=False, null=True, verbose_name='Факт наличия брака'),
        ),
        migrations.AlterField(
            model_name='shifttask',
            name='master_called',
            field=models.CharField(default='не было', max_length=10, null=True, verbose_name='статус вызова мастера'),
        ),
        migrations.AlterField(
            model_name='shifttask',
            name='master_calls',
            field=models.IntegerField(default=0, null=True, verbose_name='количество вызовов мастера'),
        ),
        migrations.AlterField(
            model_name='shifttask',
            name='master_finish_wp',
            field=models.CharField(max_length=30, null=True, verbose_name='ФИО мастера вызова ОТК'),
        ),
        migrations.AlterField(
            model_name='shifttask',
            name='model_name',
            field=models.CharField(db_index=True, max_length=30, verbose_name='Модель изделия'),
        ),
        migrations.AlterField(
            model_name='shifttask',
            name='norm_fact',
            field=models.DecimalField(decimal_places=2, max_digits=10, null=True, verbose_name='Фактическая норма времени'),
        ),
        migrations.AlterField(
            model_name='shifttask',
            name='norm_tech',
            field=models.DecimalField(decimal_places=2, max_digits=10, null=True, verbose_name='Технологическая норма времени'),
        ),
        migrations.AlterField(
            model_name='shifttask',
            name='op_name',
            field=models.CharField(max_length=200, verbose_name='Имя операции'),
        ),
        migrations.AlterField(
            model_name='shifttask',
            name='op_name_full',
            field=models.CharField(max_length=255, verbose_name='Полное имея операции'),
        ),
        migrations.AlterField(
            model_name='shifttask',
            name='op_number',
            field=models.CharField(max_length=20, verbose_name='Номер операции'),
        ),
        migrations.AlterField(
            model_name='shifttask',
            name='order',
            field=models.CharField(max_length=100, verbose_name='Номер заказа'),
        ),
        migrations.AlterField(
            model_name='shifttask',
            name='otk_answer',
            field=models.CharField(max_length=30, null=True, verbose_name='ФИО контролёра ответа ОТК'),
        ),
        migrations.AlterField(
            model_name='shifttask',
            name='otk_decision',
            field=models.CharField(max_length=30, null=True, verbose_name='ФИО контролёра решения ОТК'),
        ),
        migrations.AlterField(
            model_name='shifttask',
            name='st_status',
            field=models.CharField(default='не запланировано', max_length=20, verbose_name='Статус СЗ'),
        ),
        migrations.AlterField(
            model_name='shifttask',
            name='workshop',
            field=models.PositiveSmallIntegerField(verbose_name='Цех'),
        ),
        migrations.AlterField(
            model_name='shifttask',
            name='ws_name',
            field=models.CharField(max_length=100, verbose_name='Имя рабочего центра'),
        ),
        migrations.AlterField(
            model_name='shifttask',
            name='ws_number',
            field=models.CharField(max_length=10, verbose_name='Номер рабочего центра'),
        ),
        migrations.AlterField(
            model_name='workshopschedule',
            name='datetime_done',
            field=models.DateField(null=True, verbose_name='Планируемая дата готовности'),
        ),
        migrations.AlterField(
            model_name='workshopschedule',
            name='done_rate',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=10, null=True, verbose_name='процент готовности'),
        ),
        migrations.AlterField(
            model_name='workshopschedule',
            name='model_name',
            field=models.CharField(max_length=30, verbose_name='Модель изделия'),
        ),
        migrations.AlterField(
            model_name='workshopschedule',
            name='model_query',
            field=models.CharField(max_length=30, null=True, verbose_name='Имя модели заказа при запросе КД'),
        ),
        migrations.AlterField(
            model_name='workshopschedule',
            name='order',
            field=models.CharField(max_length=100, verbose_name='Номер заказа'),
        ),
        migrations.AlterField(
            model_name='workshopschedule',
            name='order_status',
            field=models.CharField(default='не запланировано', max_length=20, verbose_name='Статус заказа'),
        ),
        migrations.AlterField(
            model_name='workshopschedule',
            name='plan_datetime',
            field=models.DateTimeField(null=True, verbose_name='дата/время выполнения планирования заказа'),
        ),
        migrations.AlterField(
            model_name='workshopschedule',
            name='td_const_done_datetime',
            field=models.DateTimeField(null=True, verbose_name='дата/время ответа конструктора по КД'),
        ),
        migrations.AlterField(
            model_name='workshopschedule',
            name='td_query_datetime',
            field=models.DateTimeField(auto_now_add=True, null=True, verbose_name='дата/время запроса документации'),
        ),
        migrations.AlterField(
            model_name='workshopschedule',
            name='td_status',
            field=models.CharField(default='запрошено', max_length=20, verbose_name='Статус технической документации'),
        ),
        migrations.AlterField(
            model_name='workshopschedule',
            name='td_tehnolog_done_datetime',
            field=models.DateTimeField(null=True, verbose_name='дата/время ответа технолога по КД'),
        ),
        migrations.AlterField(
            model_name='workshopschedule',
            name='workshop',
            field=models.PositiveSmallIntegerField(verbose_name='Цех'),
        ),
    ]

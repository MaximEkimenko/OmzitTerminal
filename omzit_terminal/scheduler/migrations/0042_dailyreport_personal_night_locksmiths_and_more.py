# Generated by Django 4.2.4 on 2023-11-30 02:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('scheduler', '0041_dailyreport_aver_fact'),
    ]

    operations = [
        migrations.AddField(
            model_name='dailyreport',
            name='personal_night_locksmiths',
            field=models.PositiveSmallIntegerField(default=0, verbose_name='Выход ночь слесаря'),
        ),
        migrations.AddField(
            model_name='dailyreport',
            name='personal_night_painters',
            field=models.PositiveSmallIntegerField(default=0, verbose_name='Выход ночь маляры'),
        ),
        migrations.AddField(
            model_name='dailyreport',
            name='personal_night_turners',
            field=models.PositiveSmallIntegerField(default=0, verbose_name='Выход ночь токаря'),
        ),
        migrations.AddField(
            model_name='dailyreport',
            name='personal_night_welders',
            field=models.PositiveSmallIntegerField(default=0, verbose_name='Выход ночь сварщики'),
        ),
        migrations.AddField(
            model_name='dailyreport',
            name='personal_shift_painters',
            field=models.PositiveSmallIntegerField(default=0, verbose_name='Выход маляров'),
        ),
        migrations.AddField(
            model_name='dailyreport',
            name='personal_shift_turners',
            field=models.PositiveSmallIntegerField(default=0, verbose_name='Выход токарей'),
        ),
        migrations.AddField(
            model_name='dailyreport',
            name='personal_total_painters',
            field=models.PositiveSmallIntegerField(default=0, verbose_name='Всего маляров'),
        ),
        migrations.AddField(
            model_name='dailyreport',
            name='personal_total_turners',
            field=models.PositiveSmallIntegerField(default=0, verbose_name='Всего токарей'),
        ),
        migrations.AlterField(
            model_name='dailyreport',
            name='personal_shift',
            field=models.PositiveSmallIntegerField(default=0, verbose_name='Выход в дату персонала'),
        ),
        migrations.AlterField(
            model_name='dailyreport',
            name='personal_shift_locksmiths',
            field=models.PositiveSmallIntegerField(default=0, verbose_name='Выход в дату слесарей'),
        ),
        migrations.AlterField(
            model_name='dailyreport',
            name='personal_shift_welders',
            field=models.PositiveSmallIntegerField(default=0, verbose_name='Выход в дату сварщиков'),
        ),
        migrations.AlterField(
            model_name='dailyreport',
            name='personal_total',
            field=models.PositiveSmallIntegerField(default=0, verbose_name='Всего персонала в цехе'),
        ),
        migrations.AlterField(
            model_name='dailyreport',
            name='personal_total_locksmiths',
            field=models.PositiveSmallIntegerField(default=0, verbose_name='Всего слесарей'),
        ),
        migrations.AlterField(
            model_name='dailyreport',
            name='personal_total_welders',
            field=models.PositiveSmallIntegerField(default=0, verbose_name='Всего сварщиков'),
        ),
    ]

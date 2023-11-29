# Generated by Django 4.2.4 on 2023-11-29 06:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('scheduler', '0041_shifttask_workpiece_workshopschedule_datetime_sz_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='workshopschedule',
            name='sz_author',
            field=models.CharField(blank=True, null=True, verbose_name='Автор СЗ'),
        ),
        migrations.AlterField(
            model_name='workshopschedule',
            name='datetime_sz',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Дата СЗ'),
        ),
        migrations.AlterField(
            model_name='workshopschedule',
            name='product_name',
            field=models.CharField(blank=True, null=True, verbose_name='Изделие по СЗ'),
        ),
        migrations.AlterField(
            model_name='workshopschedule',
            name='sz_need_date',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Дата потребности по СЗ'),
        ),
        migrations.AlterField(
            model_name='workshopschedule',
            name='sz_number',
            field=models.CharField(blank=True, null=True, verbose_name='Номер СЗ'),
        ),
    ]

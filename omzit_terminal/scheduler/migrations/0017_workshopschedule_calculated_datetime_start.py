# Generated by Django 4.2.4 on 2024-08-02 05:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('scheduler', '0016_rename_fixed_in_plan_workshopschedule_is_fixed'),
    ]

    operations = [
        migrations.AddField(
            model_name='workshopschedule',
            name='calculated_datetime_start',
            field=models.DateField(null=True, verbose_name='Расчётная дата запуска'),
        ),
    ]
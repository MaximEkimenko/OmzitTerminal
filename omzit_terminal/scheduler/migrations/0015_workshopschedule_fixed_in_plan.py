# Generated by Django 4.2.4 on 2024-07-31 08:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('scheduler', '0014_workshopschedule_contract_end_date_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='workshopschedule',
            name='fixed_in_plan',
            field=models.BooleanField(default=False, verbose_name='фиксация в план'),
        ),
    ]

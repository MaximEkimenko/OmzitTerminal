# Generated by Django 4.2.4 on 2024-07-22 09:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('scheduler', '0012_alter_workshopschedule_td_status'),
    ]

    operations = [
        migrations.AddField(
            model_name='workshopschedule',
            name='produce_cycle',
            field=models.DecimalField(decimal_places=2, default=1, max_digits=10, null=True, verbose_name='Производственный цикл'),
        ),
    ]

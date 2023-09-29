# Generated by Django 4.2.4 on 2023-09-25 03:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('scheduler', '0019_workshopschedule_done_rate'),
    ]

    operations = [
        migrations.AlterField(
            model_name='workshopschedule',
            name='done_rate',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=10, null=True),
        ),
    ]
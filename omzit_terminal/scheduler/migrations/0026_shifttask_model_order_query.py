# Generated by Django 4.2.4 on 2023-10-03 11:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('scheduler', '0025_alter_workshopschedule_model_order_query'),
    ]

    operations = [
        migrations.AddField(
            model_name='shifttask',
            name='model_order_query',
            field=models.CharField(max_length=60, null=True, unique=True, verbose_name='заказ и модель'),
        ),
    ]

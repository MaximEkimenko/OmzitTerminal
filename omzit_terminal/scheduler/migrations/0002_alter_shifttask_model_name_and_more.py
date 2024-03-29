# Generated by Django 4.2.4 on 2024-02-09 09:33

import django.core.validators
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('scheduler', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='shifttask',
            name='model_name',
            field=models.CharField(db_index=True, max_length=30, validators=[django.core.validators.RegexValidator(message="Имя модели может содержать только цифры и буквы латинского алфавита и знак '-' тире", regex='^[\\-A-Za-z0-9]+$')], verbose_name='Модель изделия'),
        ),
        migrations.AlterField(
            model_name='shifttask',
            name='next_shift_task',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='previous_shift_task', to='scheduler.shifttask', verbose_name='Новое СЗ'),
        ),
        migrations.AlterField(
            model_name='shifttask',
            name='norm_tech',
            field=models.DecimalField(decimal_places=5, max_digits=13, null=True, verbose_name='Технологическая норма времени'),
        ),
        migrations.AlterField(
            model_name='shifttask',
            name='order',
            field=models.CharField(max_length=100, null=True, validators=[django.core.validators.RegexValidator(message='Имя заказа может содержать только цифры, буквы, знаки тире "-" и скобки "()"', regex='^[А-Яа-яA-Za-z0-9\\(\\)\\-]+$')], verbose_name='Номер заказа'),
        ),
        migrations.AlterField(
            model_name='workshopschedule',
            name='model_name',
            field=models.CharField(max_length=30, validators=[django.core.validators.RegexValidator(message="Имя модели может содержать только цифры и буквы латинского алфавита и знак '-' тире", regex='^[\\-A-Za-z0-9]+$')], verbose_name='Модель изделия'),
        ),
        migrations.AlterField(
            model_name='workshopschedule',
            name='order',
            field=models.CharField(max_length=100, validators=[django.core.validators.RegexValidator(message='Имя заказа может содержать только цифры, буквы, знаки тире "-" и скобки "()"', regex='^[А-Яа-яA-Za-z0-9\\(\\)\\-]+$')], verbose_name='Номер заказа'),
        ),
    ]

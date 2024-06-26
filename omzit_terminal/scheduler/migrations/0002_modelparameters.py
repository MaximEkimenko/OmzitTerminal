# Generated by Django 4.2.4 on 2024-06-21 06:44

import django.contrib.postgres.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('scheduler', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='ModelParameters',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('model_name', models.CharField(verbose_name='Модель изделия')),
                ('model_weight', models.DecimalField(decimal_places=2, max_digits=10, verbose_name='масса изделия')),
                ('full_norm_tech', models.DecimalField(decimal_places=2, default=0, max_digits=10, null=True, verbose_name='Полная трудоёмкость изделия')),
                ('critical_chain_cycle_koef', models.DecimalField(decimal_places=2, default=0.6, max_digits=5, null=True, verbose_name='Коэффициент расчёта критической цепи')),
                ('difficulty_koef', models.DecimalField(decimal_places=2, default=1, max_digits=5, null=True, verbose_name='Коэффициент сложности изделия')),
                ('cycle_polynom_koef', django.contrib.postgres.fields.ArrayField(base_field=models.DecimalField(decimal_places=10, max_digits=12, null=True), null=True, size=None, verbose_name='Коэффициенты формулы расчёта критической цепи по массе')),
                ('produce_cycle', models.DecimalField(decimal_places=2, default=0, max_digits=5, null=True, verbose_name='Производственный цикл')),
                ('day_hours_amount', models.DecimalField(decimal_places=2, default=0, max_digits=5, null=True, verbose_name='Часов в день на изделие')),
            ],
            options={
                'verbose_name': 'Параметры модели',
                'verbose_name_plural': 'Параметры модели',
                'db_table': 'model_parameters',
            },
        ),
    ]

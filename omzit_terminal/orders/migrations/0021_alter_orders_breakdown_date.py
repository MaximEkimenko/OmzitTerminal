# Generated by Django 4.2.4 on 2024-07-11 07:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("orders", "0020_equipment_ppr_plan_day"),
    ]

    operations = [
        migrations.AlterField(
            model_name="orders",
            name="breakdown_date",
            field=models.DateTimeField(verbose_name="Дата поломки"),
        ),
    ]
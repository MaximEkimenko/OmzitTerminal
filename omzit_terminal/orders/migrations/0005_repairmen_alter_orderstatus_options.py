# Generated by Django 4.2.4 on 2024-06-18 09:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("orders", "0004_orders_worker_alter_orders_identified_employee_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="Repairmen",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("fio", models.CharField(max_length=255, verbose_name="ФИО")),
                (
                    "position",
                    models.CharField(
                        max_length=255, null=True, verbose_name="Должность"
                    ),
                ),
                (
                    "phone",
                    models.CharField(
                        blank=True, max_length=20, null=True, verbose_name="Телефон"
                    ),
                ),
                (
                    "telegram_id",
                    models.CharField(
                        max_length=20, null=True, verbose_name="telegram_id"
                    ),
                ),
                (
                    "active",
                    models.BooleanField(
                        default=True, null=True, verbose_name="Телефон"
                    ),
                ),
            ],
            options={
                "verbose_name": "Ремонтник",
                "verbose_name_plural": "Ремонтники",
            },
        ),
        migrations.AlterModelOptions(
            name="orderstatus",
            options={
                "ordering": ["pk"],
                "verbose_name": "Состояние ремонта",
                "verbose_name_plural": "Состояния ремонта",
            },
        ),
    ]

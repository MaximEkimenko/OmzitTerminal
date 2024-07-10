# Generated by Django 4.2.4 on 2024-07-08 10:39

from django.db import migrations, models
import orders.models


class Migration(migrations.Migration):

    dependencies = [
        ("orders", "0016_equipment_ppr_plan_day_orders_material_request_file"),
    ]

    operations = [
        migrations.AlterField(
            model_name="orders",
            name="material_request_file",
            field=models.FileField(
                null=True,
                upload_to=orders.models.order_directory_path,
                verbose_name="Pdf заявка на материалы",
            ),
        ),
    ]
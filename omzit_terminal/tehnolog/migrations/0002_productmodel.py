# Generated by Django 4.2.4 on 2023-08-25 05:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tehnolog', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='ProductModel',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('model_name', models.CharField(db_index=True, max_length=20)),
            ],
            options={
                'verbose_name': 'Модель изделия',
                'verbose_name_plural': 'Модель изделий',
                'db_table': 'model_name',
            },
        ),
    ]

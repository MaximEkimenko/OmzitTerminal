# Generated by Django 4.2.4 on 2023-09-11 07:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('scheduler', '0016_docquery_workshopschedule_plan_datetime_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='workshopschedule',
            name='model_query',
            field=models.CharField(max_length=30, null=True),
        ),
    ]
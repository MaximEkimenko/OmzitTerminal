# Generated by Django 4.2.4 on 2024-07-31 09:14

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('scheduler', '0015_workshopschedule_fixed_in_plan'),
    ]

    operations = [
        migrations.RenameField(
            model_name='workshopschedule',
            old_name='fixed_in_plan',
            new_name='is_fixed',
        ),
    ]
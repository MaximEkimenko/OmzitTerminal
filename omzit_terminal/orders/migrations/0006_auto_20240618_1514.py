# Generated by Django 4.2.4 on 2024-06-18 09:14

from django.db import migrations


def populate_repairmen(apps, schema_editor):
    Repairmen = apps.get_model("orders", "Repairmen")
    Repairmen.objects.create(
        fio="Новиков А.Н.",
        position="главный инженер",
        phone="8-923-678-82-50",
        telegram_id="",
    )
    Repairmen.objects.create(
        fio="Родионов А.С.",
        position="главный энергетик",
        phone="8-951-407-16-57",
        telegram_id="5092813369",
    )
    Repairmen.objects.create(
        fio="Величко М.В.",
        position="главный энергетик",
        phone="8-913-656-55-56",
        telegram_id="5226883305",
    )
    Repairmen.objects.create(
        fio="Викторов А.В.",
        position="инженер-энергетик",
        phone="8-926-328-46-90",
        telegram_id="5990089219",
    )
    Repairmen.objects.create(
        fio="Балашенко Д.А.",
        position="инженер - механик",
        phone="8-908-119-38-82",
        telegram_id="5377855473",
    )
    Repairmen.objects.create(
        fio="Пашко Л.С.",
        position="инженер наладчик сварочного оборудования",
        phone="8-960-980-81-30",
        telegram_id="5126990447",
    )
    Repairmen.objects.create(
        fio="Родионова М.Ю.",
        position="администратор",
        phone="8-908-800-56-73",
        telegram_id="5040154034",
    )
    Repairmen.objects.create(
        fio="Галюк Д.В.",
        position="электромонтер по ремонту и обслуживанию электрооборудования",
        phone="8-923-458-42-56",
        telegram_id="",
    )
    Repairmen.objects.create(
        fio="Андреев О.В.",
        position="электромонтер по ремонту и обслуживанию электрооборудования",
        phone="8-913-612-12-19",
        telegram_id="5038982760",
    )
    Repairmen.objects.create(
        fio="Борисенко В.В.", position="слесарь-ремонтник", phone="8-950-954-50-26", telegram_id=""
    )
    Repairmen.objects.create(
        fio="Лыскин Д.И.", position="слесарь-ремонтник", phone="8-983-623-01-31", telegram_id=""
    )
    Repairmen.objects.create(
        fio="Цыбульский С.В.",
        position="наладчик сварочного оборудования",
        phone="8-905-921-89-70",
        telegram_id="5162828251",
    )
    Repairmen.objects.create(
        fio="Овсянников В.А.",
        position="наладчик сварочного оборудования",
        phone="8-901-263-53-54",
        telegram_id="",
    )
    Repairmen.objects.create(
        fio="Охапкин И.С.",
        position="слесарь вентиляционщик-кондицеонерщик",
        phone="8-908-319-81-61",
        telegram_id="2081825294",
    )
    Repairmen.objects.create(
        fio="Бородин О.С.", position="слесарь-сантехник", phone="8-933-993-21-68", telegram_id=""
    )
    Repairmen.objects.create(
        fio="Шабанов А.А.",
        position="электромонтажник",
        phone="8-904-822-62-19",
        telegram_id="1696839319",
    )
    Repairmen.objects.create(
        fio="Попов В.В.",
        position="электромонтажник",
        phone="8-904-326-65-23",
        telegram_id="1245921313",
    )
    Repairmen.objects.create(
        fio="Посвистак П.А.",
        position="слесарь по ремонту газового оборудования",
        phone="8-913-606-53-24",
        telegram_id="1165221360",
    )


class Migration(migrations.Migration):

    dependencies = [
        ("orders", "0005_repairmen_alter_orderstatus_options"),
    ]

    operations = [
        migrations.RunPython(populate_repairmen),
    ]

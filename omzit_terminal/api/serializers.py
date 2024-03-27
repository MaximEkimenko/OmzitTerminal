from rest_framework import serializers

from scheduler.models import ShiftTask

import locale

locale.setlocale(locale.LC_ALL, "ru_RU.utf8")


class ShiftTaskSerializer(serializers.ModelSerializer):
    datetime_job_start = serializers.DateTimeField(
        format="%d %B %Y г. %H:%M"
    )
    decision_time = serializers.DateTimeField(
        format="%d %B %Y г. %H:%M"
    )

    class Meta:
        model = ShiftTask
        fields = (
            "id",
            "ws_number",
            "model_name",
            "order",
            "op_number",
            "op_name_full",
            "norm_tech",
            "fio_doer",
            "st_status",
            "datetime_job_start",
            "decision_time",
        )


class ShiftTaskIdSerializer(serializers.Serializer):
    st_number = serializers.IntegerField(min_value=0)

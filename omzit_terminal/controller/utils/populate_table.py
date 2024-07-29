from scheduler.models import ShiftTask
def populate_controller_table():
    ts = ShiftTask.objects.filter(st_status__icontains="брак").all().values()

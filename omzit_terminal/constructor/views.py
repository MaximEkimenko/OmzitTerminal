from django.shortcuts import render
from scheduler.models import WorkshopSchedule


def constructor(request):
    td_queries = WorkshopSchedule.objects.values('order', 'model_query', 'td_status').exclude(td_status='передано')

    context = {'td_queries': td_queries}

    return render(request, r"constructor/constructor.html", context=context)


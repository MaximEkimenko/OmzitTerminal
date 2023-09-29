from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from scheduler.models import WorkshopSchedule


@login_required(login_url="../scheduler/login/")
def constructor(request):
    td_queries = (WorkshopSchedule.objects.values('order', 'model_query', 'td_status')
                  .exclude(td_status='передано'))

    context = {'td_queries': td_queries}

    return render(request, r"constructor/constructor.html", context=context)


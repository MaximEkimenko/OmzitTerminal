from datetime import timedelta
from django.shortcuts import render
from django.views.generic import DetailView, UpdateView, ListView, TemplateView, CreateView
from django.urls import reverse_lazy, reverse
from django.http import HttpResponse, HttpResponseRedirect, FileResponse, JsonResponse
from django.forms.models import model_to_dict

from controller.forms import EditDefectForm
from scheduler.models import ShiftTask
from controller.models import DefectAct
from controller.utils.utils import get_model_verbose_names

def index(request):
    acts = DefectAct.objects.all()

    if len(acts) < 1:
        act_count = 1
        ts = ShiftTask.objects.filter(st_status__icontains="брак").order_by("-datetime_fail").all()
        for task in ts:
            df = task.datetime_fail
            fix_time = None
            if nst := task.next_shift_task:
                fix_time = nst.decision_time - nst.datetime_job_start
            obj_dict = {
                "datetime_fail": task.datetime_fail,
                "act_number": f"{df.month}.{df.year}/{act_count}",
                "workshop": task.workshop,
                "operation": task.op_number + " " + task.op_name_full,
                "fixing_time": fix_time,
                "from_shift_task": True,
            }
            DefectAct.objects.create(**obj_dict)
            act_count += 1
        acts = DefectAct.objects.all()



    context = {'object_list': acts}
    return render(request, "controller/index.html", context)

class CreateDefectAct(CreateView):
    model = DefectAct
    form_class = EditDefectForm
    
    template_name = "controller/create_defect.html"
    success_url = reverse_lazy("controller:index")

    def form_valid(self, form):
        form.instance.fixing_time = timedelta(hours=1) * form.cleaned_data["manual_fixing_time"]
        return super().form_valid(form)

class EditDefectAct(UpdateView):
    form_class = EditDefectForm
    model = DefectAct
    template_name = "controller/create_defect.html"
    success_url = reverse_lazy("controller:index")


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
        ts = ShiftTask.objects.filter(st_status__icontains="брак").oredr_by("-datetime_fail").all().values()
        print(len(ts))
        for task in ts:
            df = task["datetime_fail"]

            obj_dict = {
                "datetime_fail": task["datetime_fail"],
                "act_number": f"{df.month}.{df.year}/{act_count}",
                "workshop": task["workshop"],
                "operation": task["op_number"] + " " + task["op_name_full"],
            }
            print(task["datetime_fail"])
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

class EditDefectAct(UpdateView):
    form_class = EditDefectForm
    model = DefectAct
    template_name = "controller/create_defect.html"
    success_url = reverse_lazy("controller:index")


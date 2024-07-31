from datetime import timedelta
from pathlib import Path
from django.shortcuts import render, redirect
from django.views.generic import DetailView, UpdateView, ListView, TemplateView, CreateView
from django.urls import reverse_lazy, reverse
from django.http import HttpResponse, HttpResponseRedirect, FileResponse, JsonResponse
from django.forms.models import model_to_dict

from controller.forms import EditDefectForm, FilesUploadForm
from controller.apps import ControllerConfig as App
from scheduler.models import ShiftTask
from controller.models import DefectAct
from controller.utils.utils import get_model_verbose_names
from tehnolog.services.service_handlers import handle_uploaded_file

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
        if fix_time := form.cleaned_data["manual_fixing_time"]:
            form.instance.fixing_time = timedelta(hours=1) * fix_time
        return super().form_valid(form)

class EditDefectAct(UpdateView):
    form_class = EditDefectForm
    model = DefectAct
    template_name = "controller/create_defect.html"
    success_url = reverse_lazy("controller:index")

    def form_valid(self, form):
        if fix_time := form.cleaned_data["manual_fixing_time"]:
            form.instance.fixing_time = timedelta(hours=1) * fix_time
        return super().form_valid(form)


def upload_files(request, pk):
    act = DefectAct.objects.get(pk=pk)
    context = {"object": act}
    if request.method == "POST":
        form = FilesUploadForm(request.POST, request.FILES)
        if form.is_valid():
            directory = str(pk)
            dest_dir = App.DEFECTS_BASE_PATH.joinpath(directory)
            if not dest_dir.exists():
                dest_dir.mkdir()
            filecount = 0
            for file in form.cleaned_data["files"]:
                filename = handle_uploaded_file(file, str(file), dest_dir)
                if filename:
                    filecount += 1
            act.media_ref = directory
            act.media_count = filecount
            act.save()
            return redirect("controller:index")
        else:
            context.update({"form": form})
            return render(request, 'controller/upload_files.html', context)
    form = FilesUploadForm()
    context.update({"form": form})
    return render(request, 'controller/upload_files.html', context)


def file_list(request, pk):
    def_act = DefectAct.objects.get(pk=pk)
    directory = def_act.act_number
    dir_path = App.DEFECTS_BASE_PATH.joinpath(str(def_act.pk))
    files = {f: f.name for f in dir_path.iterdir() if f.is_file()}
    print(files)
    context = {"object": def_act, "files": files}
    return render(request, "controller/filelist.html", context)

def show_file(request, path):
    return FileResponse(open(path, "rb"))

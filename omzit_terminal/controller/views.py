from datetime import timedelta
from pathlib import Path
from django.shortcuts import render, redirect
from django.views.generic import DetailView, UpdateView, ListView, TemplateView, CreateView
from django.urls import reverse_lazy, reverse
from django.http import HttpResponse, HttpResponseRedirect, FileResponse, JsonResponse
from django.forms.models import model_to_dict

from controller.forms import EditDefectForm, FilesUploadForm
from controller.apps import ControllerConfig as App

from controller.models import DefectAct
from controller.utils.utils import check_directory
from controller.utils.utils import get_model_verbose_names, import_acts_from_shift_task
from tehnolog.services.service_handlers import handle_uploaded_file
from m_logger_settings import logger

def index(request):
    """
    Отображает список актов о браке
    """
    acts = DefectAct.objects.all()
    # импортируем записи из ShiftTask если таблица брака пустая
    if len(acts) < 1:
        import_acts_from_shift_task(1)

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
    """
    Функция в которой происходит добавление файлов в каталог, ассоциированный с актом о браке.
    Сначала проверяеся, существует ли каталог, при необходимости он сождается и в него копируются файлы.
    Так же происходит подсчет файлов, для отображения количества файлов в таблице.
    """
    act = DefectAct.objects.get(pk=pk)
    context = {"object": act}
    if request.method == "POST":
        form = FilesUploadForm(request.POST, request.FILES)
        if form.is_valid():
            directory = str(pk)
            dest_dir = check_directory(directory)
            if dest_dir:
                logger.info(f"Создан каталог '{dest_dir}' для акта о браке {act.act_number}")
                filecount = len([f for f in dest_dir.iterdir() if f.is_file()])
                for file in form.cleaned_data["files"]:
                    filename = handle_uploaded_file(file, str(file), dest_dir)
                    if filename:
                        logger.info(f"Файл '{filename}' добавлен к акту о браке '{act.act_number}'")
                        filecount += 1
                act.media_ref = directory
                act.media_count = filecount
                act.save()
            else:
                logger.info("Файлы не добавлялись из-за ошибка создания каталога")

            return redirect("controller:index")
        else:
            context.update({"form": form})
            return render(request, 'controller/upload_files.html', context)
    form = FilesUploadForm()
    context.update({"form": form})
    return render(request, 'controller/upload_files.html', context)


def file_list(request, pk):
    """
    Здесь отображается список файлов, прикрепленных к акту.
    Происходит сканирование файлов в каталоге, ассоциированном с актом и их отображение.
    На случай если каталог кто-то удалил, происходит его проверка и создание при необходимости,
    чтобы не возникала ошибка.
    А так жепроисходит пересчет количества файлов, потому что в этом представлении их можно удалять.
    """
    act = DefectAct.objects.get(pk=pk)
    check_directory(act.media_ref)
    dir_path = App.DEFECTS_BASE_PATH.joinpath(str(act.pk))
    files = {f: f.name for f in dir_path.iterdir() if f.is_file()}
    act.media_count = len(files)
    act.save()
    context = {"object": act, "files": files}
    return render(request, "controller/filelist.html", context)

def show_file(request, path: str):
    """
    Проказывает пользователю файл, на который он кликнул по ссылке.
    @param path: Абсолютный путь к файлу.
    """
    try:
        return FileResponse(open(path, "rb"))
    except Exception as e:
        logger.error(f"Ошибка при отправке файла '{path}'")
        logger.exception(e)

def delete_file_proc(request, pk: int, path: str):
    """
    Удаляет файл из каталога ассоциированного с актом о браке.
    После удаления перенаправляет на страницу со списком прикрепленных файлов.
    @param pk: Идентификатор конкретного акта о браке, к которому нужно вернуться после удаления.
    @param path: Абсолютный путь для удаления файла.
    """
    if path:
        file = Path(path).resolve()
        if file.exists():
            try:
                file.unlink()
            except Exception as e:
                logger.error(f"Ошибка при удалении файла '{file}'")
                logger.exception(e)
            else:
                logger.info(f"Файл  {file}, прикрепленный к заявке, удален.")
    return redirect(reverse_lazy("controller:file_list", args=(pk,)))

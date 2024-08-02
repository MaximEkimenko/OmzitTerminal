from datetime import timedelta
from pathlib import Path
from django.shortcuts import render, redirect
from django.views.generic import DetailView, UpdateView, ListView, TemplateView, CreateView
from django.urls import reverse_lazy, reverse
from django.http import HttpResponse, HttpResponseRedirect, FileResponse, JsonResponse
from django.db.models import Max
from django.forms.models import model_to_dict
from django.views.generic.edit import FormMixin, ContextMixin

from controller.forms import EditDefectForm, FilesUploadForm
from controller.apps import ControllerConfig as App

from controller.models import DefectAct
from controller.utils.utils import check_directory
from controller.utils.utils import (get_model_verbose_names,
                                    import_acts_from_shift_task,
                                    format_act_number,
                                    add_defect_acts, check_media_ref
                                    )
from orders.utils.roles import get_employee_position, Position, PERMITTED_USERS, menu_items, get_menu_context
from tehnolog.services.service_handlers import handle_uploaded_file
from m_logger_settings import logger
from controller.utils.edit_permissions import FIELD_EDIT_PERMISSIONS

def index(request):
    """
    Отображает список актов о браке
    """
    acts = DefectAct.objects.all()
    # импортируем записи из ShiftTask если таблица брака пустая
    if len(acts) < 1:
        import_acts_from_shift_task(1)
    add_defect_acts()
    context = {'object_list': acts,
               "create_act_role": [Position.Admin, Position.Controller],
               }
    context.update(get_menu_context(request))
    return render(request, "controller/index.html", context)


class DisableFieldsMixin(FormMixin):
    """
    Миксин, выполняющий две задачи:
    1) отключает отдельные поля формы в зависимости от роли пользователя.
    2) Переводит число во временной интервал при сохранении в базу срока исправления брака.
    """
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({"create_act_role": [Position.Admin, Position.Controller]})
        context.update(get_menu_context(self.request))
        form = context['form']
        for permission in FIELD_EDIT_PERMISSIONS:
            if context["role"] not in FIELD_EDIT_PERMISSIONS[permission]:
                form.fields[permission].disabled = True
        return context

    def form_valid(self, form):
        # нужно преобразовать время в часах(float), поступивший из формы, и в интервал времени и в таком виде сохранять
        if fix_time := form.cleaned_data["manual_fixing_time"]:
            form.instance.fixing_time = timedelta(hours=1) * fix_time
        return super().form_valid(form)


class CreateDefectAct(DisableFieldsMixin, CreateView):
    """
    Представление для ручного создания нового акта о браке
    """
    model = DefectAct
    form_class = EditDefectForm
    template_name = "controller/create_defect.html"
    success_url = reverse_lazy("controller:index")
    extra_context = {"permissions": FIELD_EDIT_PERMISSIONS}

    def form_valid(self, form):
        last_num = DefectAct.last_act_number()
        if last_num:
            current_num = last_num + 1
        else:
            current_num = 1
            logger.error("В базе DefectAct отсутствуют записи. Новой записи присвоен номер 1")
        form.instance.tech_number = current_num
        form.instance.act_number = format_act_number(form.cleaned_data["datetime_fail"], current_num)
        if fix_time := form.cleaned_data["manual_fixing_time"]:
            form.instance.fixing_time = timedelta(hours=1) * fix_time
        return super().form_valid(form)

class EditDefectAct(DisableFieldsMixin, UpdateView):
    """
    Представление для редактирования акта о браке
    """
    form_class = EditDefectForm
    model = DefectAct
    template_name = "controller/create_defect.html"
    success_url = reverse_lazy("controller:index")

    def form_valid(self, form):
        # Случай, когда поле "дата" было отключено в форме. Но в модели оно обязательно,
        # и записывать в нее данные нужно. Просто берем изначальные данные из формы и присваиваем модели.
        if form.cleaned_data.get("datetime_fail") is None:
            form.instance.datetime_fail = form.initial["datetime_fail"]
        return super().form_valid(form)


def upload_files(request, pk):
    """
    Функция в которой происходит добавление файлов в каталог, ассоциированный с актом о браке.
    Сначала проверяеся, существует ли каталог, при необходимости он создается и в него копируются файлы.
    Так же происходит подсчет файлов, для отображения количества файлов в таблице.
    """
    act = DefectAct.objects.get(pk=pk)
    context = {"object": act}
    if request.method == "POST":
        form = FilesUploadForm(request.POST, request.FILES)
        if form.is_valid():
            another_act = check_media_ref(act)
            print(another_act)
            print("указывают на один объект? ", another_act == act)
            dest_dir = check_directory(act)
            if dest_dir:
                logger.info(f"Создан каталог '{dest_dir}' для акта о браке {act.act_number}")
                filecount = len([f for f in dest_dir.iterdir() if f.is_file()])
                for file in form.cleaned_data["files"]:
                    filename = handle_uploaded_file(file, str(file), dest_dir)
                    if filename:
                        logger.info(f"Файл '{filename}' добавлен к акту о браке '{act.act_number}'")
                        filecount += 1
                act.media_count = filecount
                act.save()
            else:
                logger.info("Файлы не добавлялись из-за ошибка создания каталога")

            return redirect("controller:index")
        else:
            context.update({"form": form})
            context.update(get_menu_context(request))
            return render(request, 'controller/upload_files.html', context)
    form = FilesUploadForm()
    context.update({"form": form})
    context.update(get_menu_context(request))
    return render(request, 'controller/upload_files.html', context)


def file_list(request, pk):
    """
    Здесь отображается список файлов, прикрепленных к акту.
    Происходит сканирование файлов в каталоге, ассоциированном с актом и их отображение.
    На случай если каталог кто-то удалил, происходит его проверка и создание при необходимости,
    чтобы не возникала ошибка.
    А так же происходит пересчет количества файлов, потому что в этом представлении их можно удалять.
    """
    act = DefectAct.objects.get(pk=pk)
    check_directory(act)
    dir_path = App.DEFECTS_BASE_PATH.joinpath(act.media_ref)
    files = {f: f.name for f in dir_path.iterdir() if f.is_file()}
    act.media_count = len(files)
    act.save()
    context = {"object": act,
               "files": files,
               "allow_to_delete": [Position.Admin, Position.Controller],
               }
    context.update(get_menu_context(request))
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

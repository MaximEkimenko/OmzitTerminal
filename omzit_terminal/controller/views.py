from datetime import timedelta
from pathlib import Path
from django.shortcuts import render, redirect
from django.views.generic import UpdateView, ListView, CreateView, DetailView
from django.urls import reverse_lazy
from django.http import FileResponse
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages

from controller.forms import EditDefectForm, FilesUploadForm
from controller.apps import ControllerConfig as App
from django.forms.models import model_to_dict

from controller.models import DefectAct
from controller.utils.mixins import RoleMixin, DisableFieldsMixin
from controller.utils.report import create_report
from controller.utils.utils import check_directory, get_model_verbose_names
from controller.utils.utils import (format_act_number,
                                    check_media_ref
                                    )
from orders.utils.roles import Position, get_menu_context
from tehnolog.services.service_handlers import handle_uploaded_file
from m_logger_settings import logger
from controller.utils.edit_permissions import FIELD_EDIT_PERMISSIONS


class DefectsView(LoginRequiredMixin, RoleMixin, ListView):
    """
    Показывает таблицу с актами о браке
    """
    model = DefectAct
    template_name = "controller/index.html"
    login_url = "/scheduler/login/"
    extra_context = {"create_act_role": [Position.Admin, Position.Controller],}


class CreateDefectAct(LoginRequiredMixin, DisableFieldsMixin, RoleMixin, CreateView):
    """
    Представление для ручного создания нового акта о браке
    """
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


class EditDefectAct(LoginRequiredMixin, DisableFieldsMixin, RoleMixin, UpdateView):
    """
    Представление для редактирования акта о браке
    """
    def form_valid(self, form):
        # Случай, когда поле "дата" было отключено в форме. Но в модели оно обязательно,
        # и записывать в нее данные нужно. Просто берем изначальные данные из формы и присваиваем модели.
        if form.cleaned_data.get("datetime_fail") is None:
            form.instance.datetime_fail = form.initial["datetime_fail"]
        return super().form_valid(form)


class DefectCard(LoginRequiredMixin, RoleMixin, DetailView):
    model = DefectAct
    fields = [
        "datetime_fail", "act_number", "workshop", "operation", "processing_object",
        "control_object", "quantity", "inconsistencies", "remark", "tech_service",
        "tech_solution", "cause", "fixable", "fixing_time", "fio_failer", "master_finish_wp",
    ]
    template_name = "controller/defect_card.html"
    login_url = "/scheduler/login/"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["pk"] = context["object"].pk
        labels = get_model_verbose_names(DefectAct)
        instance_dict = model_to_dict(context["object"])
        context["object"] = {labels[label]: instance_dict[label] for label in labels if label in self.fields}
        return context


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
            check_media_ref(act)
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
                messages.add_message(request, messages.SUCCESS,
                                     f"К акту о браке № {act.act_number} добавлены файлы.")
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
    Показывает пользователю файл, на который он кликнул по ссылке.
    @param path: Абсолютный путь к файлу.
    """
    try:
        return FileResponse(open(path, "rb"))
    except Exception as e:
        alert_message = f"Ошибка при отправке файла '{path}'"
        messages.add_message(request, messages.ERROR, alert_message)
        logger.error(alert_message)
        logger.exception(e)
        return redirect("controller:index")


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


def defect_report(request):
    """
    Создает файл отчета по актам о браке
    """
    try:
        exel_file = create_report()
    except Exception as e:
        alert_message = "Ошибка при создании xls-отчета"
        logger.info(alert_message)
        messages.add_message(request, messages.ERROR, alert_message)
        logger.exception(e)
    else:
        alert_message = f"Пользователь {request.user} успешно загрузил отчёт в excel."
        messages.add_message(request, messages.SUCCESS, alert_message)
        logger.info(alert_message)
        return FileResponse(open(exel_file, "rb"))
    return redirect("controller:index")

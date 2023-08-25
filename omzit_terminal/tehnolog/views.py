import os
from django.http import HttpResponseRedirect
from django.shortcuts import render, redirect
from .services.service_handlers import handle_uploaded_file
from .services.tech_data_get import tech_data_get
from .forms import GetTehDataForm


def tehnolog_wp(request):
    if request.method == 'POST':
        form = GetTehDataForm(request.POST, request.FILES)  # класс форм с частично заполненными данными
        if form.is_valid():
            # ключ excel_file в словаре request.FILES должен быть равен имени формы созданной в классе
            # GetTehDataForm
            filename = str(dict(request.FILES)["excel_file"][0])  # имя файла
            # обработка выбора не excel файла
            if '.xlsx' not in filename:
                form.add_error(None, 'Файл должен быть .xlsx!')
                return render(request, r"tehnolog/tehnolog.html", {'form': form})
            file_save_path = os.getcwd() + r'\xlsx\\'
            # обработчик загрузки файла
            xlsx_file = handle_uploaded_file(f=request.FILES["excel_file"], filename=filename,
                                             path=file_save_path)
            list_names = form.cleaned_data['list_names'].split(',')
            exception_names = form.cleaned_data['exception_names']
            category = form.cleaned_data['category']
            # print(list_names, exception_names, category)
            # return redirect('tehnolog')  # обновление страницы при успехе TODO сделать сообщение об успехе!
            # вызов сервиса получения данных из xlsx
            try:
                tech_data_get(exel_file=xlsx_file, model_list=list_names,
                              exclusion_list=exception_names, category=category)
            except Exception as e:
                print(e)
            print(form.cleaned_data)
    else:
        form = GetTehDataForm()  # чистая форма для первого запуска
    return render(request, r"tehnolog/tehnolog.html", {'form': form})

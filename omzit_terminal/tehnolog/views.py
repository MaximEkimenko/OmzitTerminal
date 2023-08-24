import os
from django.http import HttpResponseRedirect
from django.shortcuts import render, redirect
from omzit_terminal.services.service_handlers import handle_uploaded_file

from .forms import GetTehDataForm
from .models import *


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

            handle_uploaded_file(request.FILES["excel_file"], filename)  # обработчик загрузки файла
            print(form.cleaned_data)
            list_names = form.cleaned_data['list_names']
            exception_names = form.cleaned_data['exception_names']
            category = form.cleaned_data['category']
            print(list_names, exception_names, category)
            # return redirect('tehnolog')  # обновление страницы при успехе TODO сделать сообщение об успехе!
            # вызов получения данных из xlsx

            # try:
            #     TechData.objects.create(**form.cleaned_data) # распакованный словарь с ключами равными БД полям
            #     return redirect('home')
            # except:
            #     form.add_error(None, 'Ошибка добавления данных')


    else:
        form = GetTehDataForm()  # чистая форма для первого запуска
    return render(request, r"tehnolog/tehnolog.html", {'form': form})


# TODO переместить из views в отдельную библиотеку, для бизнес логики



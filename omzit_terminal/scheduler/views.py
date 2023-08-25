from django.shortcuts import render, redirect
from .forms import SchedulerWorkshop
from .models import WorkshopSchedule, ShiftTask


def scheduler(request):
    # отображение графика цеха
    # TODO разобрать исходник для передачи в контекст для управления в HTML
    # workshop_schedule = WorkshopSchedule.objects.all().values()


    if request.method == 'POST':
        form = SchedulerWorkshop(request.POST)  # класс форм с частично заполненными данными
        if form.is_valid():
            # заполнение модели графика цеха новыми данными
            try:
                if not (WorkshopSchedule.objects.filter(order=form.cleaned_data['order'],
                                                        model_name=form.cleaned_data['model_name'],
                                                        workshop=form.cleaned_data['workshop'],
                                                        datetime_done=form.cleaned_data['datetime_done']).exists()):
                    WorkshopSchedule.objects.create(order=form.cleaned_data['order'],
                                                    model_name=form.cleaned_data['model_name'],
                                                    workshop=form.cleaned_data['workshop'],
                                                    datetime_done=form.cleaned_data['datetime_done'])
                    print('Данные успешно занесены!')
                    return redirect('scheduler')  # обновление страницы при успехе TODO сделать сообщение об успехе!
                else:
                    form.add_error(None, 'Такой заказ уже запланирован!')
                    context = {'form': form}

            except Exception as e:
                print(e, ' Ошибка запаси в базу SchedulerWorkshop')

            #

        else:
            context = {'form': form
                       }

    # Выбрать всё из модели tech_data с номером заказа из model_list и заполнить цех и номер заказа в своей модели
    #

    else:
        form = SchedulerWorkshop()  # чистая форма для первого запуска
        context = {'form': form, 'schedule': workshop_schedule}
    return render(request, r"scheduler/scheduler.html", context=context)

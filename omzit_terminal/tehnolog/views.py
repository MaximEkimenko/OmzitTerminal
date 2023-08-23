from django.shortcuts import render
from .forms import GetTehDataForm
from .models import ProductCategory


def tehnolog_wp(request):
    form = GetTehDataForm()  # класс форм
    print(ProductCategory.objects.all().values(), type(ProductCategory.objects.all().values()))
    return render(request, r"tehnolog/tehnolog.html", {'form': form})




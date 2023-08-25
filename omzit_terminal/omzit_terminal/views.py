from django.shortcuts import render


def home(request):
    return render(request, r"omzit_terminal/omzit_terminal.html")


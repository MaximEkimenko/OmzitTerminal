from django.http import HttpResponse
from django.shortcuts import render
from django.http import FileResponse

def home(request):
    return render(request, r"omzit_terminal/omzit_terminal.html")


def get_pdf(request):
    # return FileResponse(open(r'files/800М 0000.000 Котел Lavart 800.pdf', 'rb'))
    return FileResponse(open(r'O:\ПТО\котлы\M\Lavart 800 M\800М.0000.000 Котел Lavart 800М\800М.0000.001 Фланец.pdf', 'rb'))

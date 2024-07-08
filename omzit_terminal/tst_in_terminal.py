import datetime
from decimal import Decimal, ROUND_HALF_UP, ROUND_CEILING

# from scheduler.models import ShiftTask, Doers  # noqa
from django.shortcuts import render, redirect


# from omzit_terminal.settings import BASE_DIR  # noqa


def tst(request):
    return render(request, r"tst/tst.html")


def date_time_play():
    full_date = datetime.datetime.combine(datetime.datetime.strptime('2024-04-05', '%Y-%m-%d'),
                                          (datetime.datetime.min.time()))
    # print(full_date.timestamp())
    # print(date.min.date())
    date = datetime.datetime.strptime('2024-04-05', '%Y-%m-%d')
    print(date.timestamp())
    cycle_1 = Decimal('77.70').quantize(Decimal('1'), ROUND_CEILING)
    print(cycle_1)
    cycle_2 = Decimal('9.24').quantize(Decimal('1'), ROUND_CEILING)
    print(cycle_2)
    print(full_date + datetime.timedelta(days=int(cycle_1)))
    print(date.fromtimestamp(1712253600))

if __name__ == '__main__':
    date_time_play()

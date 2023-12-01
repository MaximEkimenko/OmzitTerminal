import openpyxl
from fpdf import FPDF
import datetime
import os

from ..models import WorkshopSchedule, ShiftTask
import matplotlib.pyplot as plt
import matplotlib
from omzit_terminal.settings import BASE_DIR
from omzit_terminal.settings import STATIC_ROOT


def get_done_rate(order_number: str) -> float:
    """
    Получение процента готовности заказа
    :param order_number: номер заказа
    :return:
    """
    # метод расчёта по количеству принятых сменных заданий
    # TODO реализовать альтернативный метод расчёта по выполненной трудоёмкости.
    all_st = ShiftTask.objects.filter(order=order_number).count()
    done_st = ShiftTask.objects.filter(order=order_number, st_status='принято').count()
    try:
        done_rate = round(100 * (all_st - (all_st - done_st))/all_st, 2)
    except ZeroDivisionError:
        done_rate = 0
    return done_rate


def get_all_done_rate() -> None:
    """
    Получение процента готовности всех заказов, обновление записей done_rate в БД
    :return: None
    """
    order_rate_dict = dict()  # TODO удалить при рефакторинге
    all_orders = WorkshopSchedule.objects.values('order').distinct()
    for dict_order in all_orders:
        order = dict_order['order']
        done_rate = get_done_rate(order)
        order_rate_dict[order] = done_rate
        # установка статуса в зависимости от процента готовности
        if done_rate == float(0):
            order_status = None
        elif done_rate == float(100):
            order_status = 'выполнено'
        else:
            order_status = 'в работе'
        # запись в БД
        if order_status:
            WorkshopSchedule.objects.filter(order=order).update(done_rate=done_rate, order_status=order_status)
    # print(order_rate_dict)


def make_workshop_plan_plot(workshop: int, days_list: list, fact_list: list, aver_fact: float,
                            start_day: datetime, end_day: datetime, yesterday: datetime) -> None:
    """
    Функция для построения инфографики работы цеха
    :param yesterday:
    :param end_day:
    :param start_day:
    :param workshop: цех
    :param days_list: список дней
    :param fact_list: список % фактического выполнения плана цехом по дням
    :param aver_fact: среднее значение факта
    :return: None
    """
    matplotlib.use('agg')  # отключение интерактивного режима
    plt.figure(figsize=(18, 8))  # размер графика
    plt.xlabel('Дата')
    plt.ylabel('% выполнения')
    plt.title(f"График выполнения плана цеха № {workshop} по {yesterday.strftime('%d.%m.%Y')}", fontsize=20)
    plt.yticks(range(0, 300, 10), fontsize=12)  # деления оси y
    fact_color = 'red' if aver_fact < 100 else 'green'  # цвет линии факта
    # корректировка fact_list при небольших значениях
    result_length = 3  # минимальная длина отчёта
    if len(fact_list) < result_length:
        hundred_list = [100] * result_length
        aver_list = [aver_fact] * result_length
        y_axis = [0] * result_length
        x_axis = [(start_day + datetime.timedelta(days=x)).strftime('%d.%m') for x in range(0, end_day.day)]
        for i in range(result_length):
            if i < len(fact_list):
                y_axis[i] = fact_list[i]
            else:
                break
    else:
        y_axis = fact_list
        x_axis = days_list
        result_length = len(fact_list)
        hundred_list = [100] * len(fact_list)
        aver_list = [aver_fact] * len(fact_list)
    plt.tick_params(direction='in', right=True, top=True, left=True)
    plt.plot(x_axis[0:result_length], y_axis, lw=1, color='blue', alpha=1, marker='o', markersize=2)  # факт
    plt.plot(x_axis[0:result_length], aver_list, lw=3, color=fact_color, alpha=1)  # факт средняя
    plt.plot(x_axis[0:result_length], hundred_list, lw=3, color='black', alpha=1)  # 100%
    # вертикальная линия на сегодня
    plt.axvline(x=days_list.index(yesterday.strftime('%d.%m')), color='gray', linestyle='--')
    plt.grid(ls=':')  # сетка графика
    # легенда
    plt.legend(('Кривая выполнения плана', fr'Факт на {days_list[len(days_list)-1]} - '
                                           fr'{round(aver_fact, 2)}%', '100%'), loc=3, fontsize=16)
    # сохранение графика
    filename = rf'scheduler\static\scheduler\jpg\plan{workshop}-{days_list[0][-2:]}.jpg'
    filename_2 = rf'O:\Расчет эффективности\отчёты цехов\plan{workshop}-{days_list[0][-2:]}.jpg'  # копия в сеть
    filepath = os.path.join(BASE_DIR, filename)
    plt.savefig(fname=filepath,   orientation='landscape', bbox_inches='tight', transparent=True)
    # копия в расчёт эффективности
    plt.savefig(fname=filename_2, orientation='landscape', bbox_inches='tight', transparent=True)
    # plt.show()


def create_pdf_report(filename: str, table_data: tuple, image_path: str, header_text: str, footer_text: str,
                      output_dir: str = None, ) -> str:
    """
    Функция создает pdf отчёт о работе цехв из картинки графики и списка табличных данных
    :param filename: имя файла
    :param table_data: список рядов таблицы, каждый ряд: список ячеек
    :param image_path: путь к картинке графика
    :param output_dir: директория сохранения файла результатов
    :return: полный путь файла
    """

    filepath = os.path.join(output_dir, filename) if output_dir else filename
    # график плана
    pdf = FPDF(orientation='L', unit='mm')
    pdf.add_page()
    pdf.image(image_path, x=0, y=0, w=290)
    pdf.add_font('Arial', '', r'C:\WINDOWS\FONTS\ARIAL.ttf', uni=True)
    pdf.set_font("Arial", '', size=14)
    pdf.ln(130)  # Отступ от графика

    # таблица
    row_height = pdf.font_size + 2  # высота ряда
    spacing = 1  # внутренний отступ таблицы
    col_width = [len(x)*2 + pdf.font_size*2.5 + 2 for x in table_data[0]]  # переменная по шапке ширина рядов
    # заголовок
    pdf.cell(sum(col_width), row_height * spacing, txt=header_text, align='C')
    pdf.ln(row_height * spacing)  # отступ заголовка
    for row in table_data:
        for i, item in enumerate(row):
            pdf.cell(col_width[i], row_height * spacing, txt=item, border=1, align='C', ln=0)
        pdf.ln(row_height * spacing)

    # футер
    pdf.add_font('Arial', '', r'C:\WINDOWS\FONTS\ARIAL.ttf', uni=True)
    pdf.set_font("Arial", '', size=10)
    pdf.ln(row_height * spacing)  # отступ футера
    pdf.cell(sum(col_width), row_height * spacing, txt=footer_text, align='L')

    pdf.output(filepath)
    return filepath


def simple_report_read(exel_file):
    """
    Функция читает простой файл excel по колонкам дат согласно стандартной форме;
    возвращает словарь {номер цеха: (данные колонки за вчера; данные колонки итого)}
    """
    ex_wb = openpyxl.load_workbook(exel_file, data_only=True)  # чтение исходник Excel
    ex_sh = ex_wb.active
    # определение номера колонки чтения по дате - вчерашний день (число)
    report_day = datetime.datetime.now() - datetime.timedelta(1)
    number_day = int(report_day.strftime('%d'))  # номер дня в формат числа
    day_c1, day_c2, day_c3, day_c4 = 0, 0, 0, 0  # переменные дней
    sum_c1, sum_c2, sum_c3, sum_c4 = 0, 0, 0, 0  # переменные суммы
    for ex_col in ex_sh.iter_cols(min_row=1, max_row=ex_sh.max_row, min_col=1,  # проход по файлу excel
                                  max_col=ex_sh.max_column, values_only=True):
        if ex_col[1] == number_day:
            day_c1 = ex_col[2] if ex_col[2] else 0
            sum_c1 = ex_sh.cell(3, 33).value
            day_c2 = ex_col[3] if ex_col[3] else 0
            sum_c2 = ex_sh.cell(4, 33).value
            day_c3 = ex_col[4] if ex_col[4] else 0
            sum_c3 = ex_sh.cell(5, 33).value
            day_c4 = ex_col[5] if ex_col[5] else 0
            sum_c4 = ex_sh.cell(6, 33).value
    ex_wb.close()
    return {'c1': {'день_сумма': (day_c1, sum_c1), 'результат': f'{day_c1} / {sum_c1}'},
            'c2': {'день_сумма': (day_c2, sum_c2), 'результат': f'{day_c2} / {sum_c2}'},
            'c3': {'день_сумма': (day_c3, sum_c3), 'результат': f'{day_c3} / {sum_c3}'},
            'c4': {'день_сумма': (day_c4, sum_c4), 'результат': f'{day_c4} / {sum_c4}'}}





import datetime
import random

from fpdf import FPDF
from lorem_text import lorem

from omzit_terminal.settings import BASE_DIR


class SzPdf(FPDF):
    data = {}

    def __init__(self, data=None, filename=None, **kwargs):
        super().__init__(**kwargs)
        self.filename = filename
        self.sz_number = data["sz"]["sz_number"]
        self.product_name = data["sz"]["product_name"]
        self.sz_text = data["sz"]["sz_text"]
        self.need_date = data["sz"]["need_date"]
        self.author = data["sz"]["author"]
        self.products = [((
                              str(i + 1),
                              product["name"],
                              product["material"],
                              product["length"],
                              product["count"]
                          ),
                          product["draw"]
        ) for i, product in enumerate(data["products"])]

    def create(self):
        cell_height = 7
        self.alias_nb_pages()
        self.add_page()
        self.add_font(
            family='Arial',
            style='',
            fname=BASE_DIR / r'scheduler/services/arial.ttf',
            uni=True
        )
        self.set_font(family='Arial', style='', size=14)

        # Заголовок
        self.cell(100)  # отступ слева
        self.multi_cell(w=0, h=cell_height, txt='Петрову Петру Петровичу ')
        self.cell(100)  # отступ слева
        self.multi_cell(w=0, h=cell_height, txt=f'от {self.author}')

        self.cell(w=0, h=10, ln=2)  # отступ
        self.multi_cell(w=100, h=cell_height, txt=self.product_name)

        # Служебная записка
        self.cell(w=0, h=10, ln=2)  # отступ
        self.cell(w=0, h=cell_height, txt='Служебная записка', ln=2, align="C")
        self.cell(w=0, h=10, ln=2)  # отступ

        # Текст СЗ
        self.multi_cell(w=0, h=cell_height, txt=f'   {self.sz_text}')
        self.cell(w=0, h=5, ln=2)  # отступ

        # Дата потребности
        self.multi_cell(w=0, h=cell_height, txt=f"Дата потребности - {self.need_date}")
        self.cell(w=0, h=10, ln=2)  # отступ

        # Перечень деталей
        self.create_table()

        self.output(self.filename)


    def create_table(self):
        cell_height = 7
        widths = [10, 50, 90, 20, 20]

        table = [(1, (["№"], ["Наименование"], ["Материал"], ["Длина"], ["Кол-во"]))]
        for i, product in enumerate(self.products):
            row = []
            max_cell_height = 0
            for i_cell, field in enumerate(product[0]):
                cells = []
                width = widths[i_cell]
                cells.extend(
                    self.multi_cell(w=width, h=cell_height, txt=f"{field}", border=1, align="L", split_only=True))
                if len(cells) > max_cell_height:
                    max_cell_height = len(cells)
                row.append(cells)
            table.append((max_cell_height, row))

        x0 = self.x
        y = self.y
        i_row = 0
        aligns = ["C", "C", "C", "C", "C"]
        draw = ""
        for max_cell_height, row in table:
            if i_row != 0 and draw != self.products[i_row - 1][1]:
                self.multi_cell(w=190, h=cell_height, txt=f"Чертёж - {self.products[i_row - 1][1]}", border="LRTB",
                                align="C")
                draw = self.products[i_row - 1][1]
                y = self.y
            i_row += 1
            x = x0
            if self.y + max_cell_height * cell_height > 270:
                self.add_page()
                y = self.y + max_cell_height * cell_height
                for i_cell, cell in enumerate(table[0][1]):
                    self.set_y(y)
                    border = "LRBT"
                    width = widths[i_cell]
                    self.set_x(x)
                    self.cell(w=width, h=cell_height, txt=f"{cell[0]}", border=border, align="C", ln=1)
                    x += width
                x = x0
                y += cell_height

            for i_cell, cell in enumerate(row):
                self.set_y(y)
                width = widths[i_cell]
                for line_no in range(max_cell_height):
                    self.set_x(x)
                    if max_cell_height == 1:
                        border = "LRBT"
                    elif line_no == 0:
                        border = "LRT"
                    elif line_no == max_cell_height - 1:
                        border = "LRB"
                    else:
                        border = "LR"
                    try:
                        self.cell(w=width, h=cell_height, txt=f"{cell[line_no]}", border=border, align=aligns[i_cell], ln=1)
                    except Exception:
                        self.cell(w=width, h=cell_height, border=border, align=aligns[i_cell], ln=1)
                x += width
            aligns = ["C", "L", "L", "C", "C"]
            y += max_cell_height * cell_height

    def footer(self):
        """ Нижний колонтитул. """

        self.set_y(-15)
        # Номер СЗ и датой формирования
        self.cell(0, 0, f"{self.sz_number} от {datetime.datetime.today().strftime('%d.%m.%Y')}", 0, 0, "L")

        # Номер страницы и количество
        self.cell(0, 5, f"Страница {self.page_no()}/{{nb}}", 0, 0, "R")


def create_pdf_sz(data, filename):
    pdf = SzPdf(data=data, filename=filename, orientation='P', unit='mm', format='A4')
    pdf.create()


if __name__ == "__main__":
    draw_1 = lorem.words(5)
    draw_2 = lorem.words(5)
    data = {
        "sz": {
            "sz_number": lorem.words(1),
            "product_name": lorem.words(2),
            "sz_text": 5 * lorem.paragraph(),
            "need_date": "12.12.2023",
            "author": lorem.words(3).title()
        },
        "products": [

            {
                "draw": draw_1,
                "name": lorem.words(5),
                "material": lorem.words(5),
                "length": random.randint(100, 99999),
                "count": random.randint(0, 50),
            },
            {
                "draw": draw_1,
                "name": lorem.words(5),
                "material": lorem.words(5),
                "length": random.randint(100, 99999),
                "count": random.randint(0, 50),
            },
            {
                "draw": draw_1,
                "name": lorem.words(5),
                "material": lorem.words(5),
                "length": random.randint(100, 99999),
                "count": random.randint(0, 50),
            },
            {
                "draw": draw_1,
                "name": lorem.words(5),
                "material": lorem.words(5),
                "length": random.randint(100, 99999),
                "count": random.randint(0, 50),
            },
            {
                "draw": draw_1,
                "name": lorem.words(5),
                "material": lorem.words(5),
                "length": random.randint(100, 99999),
                "count": random.randint(0, 50),
            },
            {
                "draw": draw_1,
                "name": lorem.words(5),
                "material": lorem.words(5),
                "length": random.randint(100, 99999),
                "count": random.randint(0, 50),
            },
            {
                "draw": draw_1,
                "name": lorem.words(5),
                "material": lorem.words(5),
                "length": random.randint(100, 99999),
                "count": random.randint(0, 50),
            },
            {
                "draw": draw_1,
                "name": lorem.words(5),
                "material": lorem.words(5),
                "length": random.randint(100, 99999),
                "count": random.randint(0, 50),
            },
            {
                "draw": draw_1,
                "name": lorem.words(5),
                "material": lorem.words(5),
                "length": random.randint(100, 99999),
                "count": random.randint(0, 50),
            },
            {
                "draw": draw_1,
                "name": lorem.words(5),
                "material": lorem.words(5),
                "length": random.randint(100, 99999),
                "count": random.randint(0, 50),
            },

            {
                "draw": draw_2,
                "name": lorem.words(5),
                "material": lorem.words(5),
                "length": random.randint(100, 99999),
                "count": random.randint(0, 50),
            },{
                "draw": draw_2,
                "name": lorem.words(5),
                "material": lorem.words(5),
                "length": random.randint(100, 99999),
                "count": random.randint(0, 50),
            },{
                "draw": draw_2,
                "name": lorem.words(5),
                "material": lorem.words(5),
                "length": random.randint(100, 99999),
                "count": random.randint(0, 50),
            },{
                "draw": draw_2,
                "name": lorem.words(5),
                "material": lorem.words(5),
                "length": random.randint(100, 99999),
                "count": random.randint(0, 50),
            },{
                "draw": draw_2,
                "name": lorem.words(5),
                "material": lorem.words(5),
                "length": random.randint(100, 99999),
                "count": random.randint(0, 50),
            },{
                "draw": draw_2,
                "name": lorem.words(5),
                "material": lorem.words(5),
                "length": random.randint(100, 99999),
                "count": random.randint(0, 50),
            },{
                "draw": draw_2,
                "name": lorem.words(5),
                "material": lorem.words(5),
                "length": random.randint(100, 99999),
                "count": random.randint(0, 50),
            },{
                "draw": draw_2,
                "name": lorem.words(5),
                "material": lorem.words(5),
                "length": random.randint(100, 99999),
                "count": random.randint(0, 50),
            },{
                "draw": draw_2,
                "name": lorem.words(5),
                "material": lorem.words(5),
                "length": random.randint(100, 99999),
                "count": random.randint(0, 50),
            },{
                "draw": draw_2,
                "name": lorem.words(5),
                "material": lorem.words(5),
                "length": random.randint(100, 99999),
                "count": random.randint(0, 50),
            },{
                "draw": draw_2,
                "name": lorem.words(5),
                "material": lorem.words(5),
                "length": random.randint(100, 99999),
                "count": random.randint(0, 50),
            },{
                "draw": draw_2,
                "name": lorem.words(5),
                "material": lorem.words(5),
                "length": random.randint(100, 99999),
                "count": random.randint(0, 50),
            },{
                "draw": draw_2,
                "name": lorem.words(5),
                "material": lorem.words(5),
                "length": random.randint(100, 99999),
                "count": random.randint(0, 50),
            },{
                "draw": draw_2,
                "name": lorem.words(5),
                "material": lorem.words(5),
                "length": random.randint(100, 99999),
                "count": random.randint(0, 50),
            },{
                "draw": draw_2,
                "name": lorem.words(5),
                "material": lorem.words(5),
                "length": random.randint(100, 99999),
                "count": random.randint(0, 50),
            },{
                "draw": draw_2,
                "name": lorem.words(5),
                "material": lorem.words(5),
                "length": random.randint(100, 99999),
                "count": random.randint(0, 50),
            },


        ]
    }
    create_pdf_sz(data, "simple_demo.pdf")

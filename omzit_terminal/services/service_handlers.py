import os


def handle_uploaded_file(f, filename: str, path: str = r'\xlsx\\') -> None:   # обработчик для копирования файлов
    """
    Обработчик копирует файл из формы загрузки частями в директорию path
    :param path: директория сохранения файла
    :param f: объект файла django
    :param filename: имя файла
    :return: None
    """
    with open(os.getcwd() + path + filename, 'wb+') as destination:
        for chunk in f.chunks():
            destination.write(chunk)

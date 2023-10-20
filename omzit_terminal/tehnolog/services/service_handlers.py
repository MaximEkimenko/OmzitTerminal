import os


def handle_uploaded_file(f, filename: str, path: str = os.getcwd() + r'\xlsx') -> str:
    """
    Обработчик копирует файл из формы загрузки частями в директорию path
    :param path: директория сохранения файла
    :param f: объект файла django
    :param filename: имя файла
    :return: полный путь сохраненного файла
    """
    with open(rf"{path}\{filename}", 'wb+') as destination:
        for chunk in f.chunks():
            try:
                destination.write(chunk)
            except Exception as e:
                print(e, f"Ошибка копирования файла! {destination.name}")
    return destination.name

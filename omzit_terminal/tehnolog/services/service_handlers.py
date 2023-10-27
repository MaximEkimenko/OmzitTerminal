import json
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


def handle_uploaded_draw_file(username, f, filename: str, path: str) -> str:
    """
    Обработчик копирует файл из формы загрузки частями в директорию path
    :param username: имя пользователя
    :param path: директория сохранения файла
    :param f: объект файла django
    :param filename: имя файла
    :return: полный путь сохраненного файла
    """
    error = False
    file_path = rf"{path}\{filename}"
    print(f"Начало создания файла {file_path} пользователем {username}")

    permissions_json_path = rf"{path}\permissions.json"

    # получаем данные из файла с доступами
    permissions = {}
    try:
        with open(permissions_json_path, 'r') as json_file:
            permissions = json.load(json_file)
    except Exception as e:
        print(f'При обращении к файлу  доступов {permissions_json_path} при попытке чтения вызвано исключение: {e}')

    # определяем доступ пользователя к перезаписи файла
    if not os.path.exists(file_path):
        uploading_allowed = True
        print(f'Нет загруженного файла с таким именем')
    elif permissions.get(filename) is None:
        uploading_allowed = False
        print(f'Файл существует, но автор не определен! Доступ запрещен! '
              f'Добавьте разрешение для пользователя в {permissions_json_path}')
    elif permissions.get(filename) == username:
        uploading_allowed = True
        print(f'У пользователя есть доступ! Файл будет перезаписан')
    else:
        uploading_allowed = False
        print(f'У пользователя отсутствует доступ с перезаписи файла!')

    # при наличии доступа пробуем создать файл
    if uploading_allowed:
        try:
            with open(file_path, 'wb+') as destination:
                for chunk in f.chunks():
                    try:
                        destination.write(chunk)
                    except Exception as e:
                        print(e, f"Ошибка создания файла!")
                        error = True
                        break
                else:
                    print(f"Файл создан!")
        except Exception as e:
            error = True
            print(e, f"Ошибка создания файла!")

    if error:
        # при ошибке создания файла, удаляем его
        try:
            os.remove(file_path)
            print(f'Файл удален из-за проблем с созданием!')
        except OSError:
            print('Файл не найден при попытке удаления!')
        file_path = ''
    elif uploading_allowed:
        # если ошибок нет, и доступ разрешен, то добавляем пользователю доступ к файлу
        permissions.update({filename: username})
        try:
            with open(permissions_json_path, 'w') as json_file:
                json.dump(permissions, json_file)
            print(f"Доступ к файлу добавлен!")
        except Exception as e:
            print(f'Доступ к файлу не добавлен! '
                  f'При обращении к файлу доступов {permissions_json_path} при попытке записи вызвано исключение: {e}')
    else:
        print(f'Файл не создан из-за проблем с доступом!')
        file_path = ''

    return file_path

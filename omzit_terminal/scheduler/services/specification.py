import ast
import json
import logging
import os
import subprocess
import threading

import paramiko

from scheduler.services.cdw_reader import get_specification

USERS = {"192.168.12.51": ["user-357", "Qwedsaq123"]}


def connect_to_client(ip):
    try:
        host = ip
        ip = "192.168.12.51"
        user, password = USERS.get(ip)

        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(hostname=host, username=user, password=password)
        return client
    except Exception as ex:
        print(f"При подключении к ip {ip} по ssh вызвано исключение: {ex}")
        return


def get_specifications_ssh(client, files):
    python_dir = r'D:\Projects\cdw_dxf_reader\venv\Scripts\python.exe'
    py_file = r'D:\Projects\omzit_terminal\OmzitTerminal\omzit_terminal\scheduler\services\cdw_reader.py'
    files = "+-+".join(files)

    cmd = " ".join((python_dir, py_file, files))
    stdin, stdout, stderr = client.exec_command(cmd, timeout=90)
    out = stdout.read().decode("Windows-1251")
    err = stderr.read().decode("Windows-1251")
    if err != "" or out != "":
        raise Exception(f"При выполнении скрипта получения спецификации на клиенте вызвано исключение: {err}, {out}")


def get_specifications_server(files):
    """
    Создает новый процесс с cdw_reader
    :param files: Список файлов с полными путями
    :return: pid запущенного процесса
    """
    files = "+-+".join(files)  # Создаем строку с разделителями и передаем в качестве аргумента py файла
    result = subprocess.Popen(args=["python", r"scheduler/services/cdw_reader.py", files])
    return result.pid


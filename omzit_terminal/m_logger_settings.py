import json
import logging.config
import os
from pathlib import Path
import logging
import pandas as pd
import logging.handlers
from multiprocessing import Process, Queue, Event, current_process

# logging.handlers.QueueHandler()

# BASEDIR = Path(__file__).parent
BASEDIR = Path(__file__).resolve().parent
logs_path = BASEDIR / 'logs'
os.makedirs(logs_path, exist_ok=True)

log_file_debug = BASEDIR / 'logs' / 'debug.log'
log_file_info = BASEDIR / 'logs' / 'info.log'
log_file_json = BASEDIR / 'logs' / 'json_log.jsonl'

if not os.path.exists(log_file_debug):
    f_debug = open(log_file_debug, 'a').close()
    f_info = open(log_file_info, 'a').close()
    f_json = open(log_file_json, 'a').close()
q = Queue()
date_format = "%Y-%m-%d %H:%M:%S"

LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": True,
    "formatters": {
        "console": {
            # pip install colorlog
            "()": "colorlog.ColoredFormatter",
            "format": "%(asctime)s: %(log_color)s%(levelname)s%(reset)s|"
                      "%(module)s|%(funcName)s|%(lineno)-15s %(light_white)s%(message)s%(reset)-15s"
                      "%(filename)s",
            "log_colors": {
                "DEBUG": "cyan",
                "INFO": "green",
                "WARNING": "yellow",
                "ERROR": "red",
                "CRITICAL": "light_white,bg_red",
            },
            "datefmt": date_format,
        },
        "file": {
            "format": "%(asctime)s|%(levelname)s|%(module)s|%(funcName)s|%(lineno)s|%(message)s|%(pathname)s",
            "datefmt": date_format,
        },

        "json": {
            # pip install python-json-logger
            "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
            "format": f"""
                    asctime: %(asctime)s
                    created: %(created)f
                    filename: %(filename)s
                    funcName: %(funcName)s
                    levelname: %(levelname)s
                    levelno: %(levelno)s
                    lineno: %(lineno)d
                    message: '%(message)s'
                    module: %(module)s
                    msec: %(msecs)d
                    name: %(name)s
                    pathname: %(pathname)s
                    process: %(process)d
                    processName: %(processName)s
                    relativeCreated: %(relativeCreated)d
                    thread: %(thread)d
                    threadName: %(threadName)s
                    exc_info: %(exc_info)s
                """,
            "datefmt": date_format,
        },
    },
    "handlers": {

        "console": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
            "formatter": "console",
        },
        "file_debug": {
            "level": "DEBUG",
            'class': 'logging.handlers.RotatingFileHandler',
            'encoding': 'utf-8',
            "formatter": "file",
            "filename": log_file_debug,
            'maxBytes': 102400000,
            'backupCount': 2,
        },
        "file_info": {
            "encoding": "utf-8",
            "level": "INFO",
            "class": "logging.handlers.RotatingFileHandler",
            "formatter": "file",
            "filename": log_file_info,
            "maxBytes": 102400000,
            "backupCount": 2,
        },
        "json": {
            "encoding": "utf-8",
            "level": "DEBUG",
            "formatter": "json",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": log_file_json,
            "maxBytes": 102400000,
            "backupCount": 2,
        },
        # "queue_handler": {
        #     "class": "logging.handlers.QueueHandler",
        #     "handlers": [
        #         "json", "console", "file_debug"
        #     ],
        #     "respect_handler_level": True
        # }
    },
    "loggers": {
        "logger": {
            "handlers": ["json", "console", "file_debug"],
            "level": "DEBUG",
        },
        # "logger": {
        #     "handlers": ["queue_handler"],
        #     "level": "DEBUG",
        # },
        "": {
            "handlers": ["file_info"],
            "level": "INFO",
        },

    },
}

logger = logging.getLogger("logger")
logging.config.dictConfig(LOGGING_CONFIG)


# queue_handler = logging.handlers.("queue_handler")
# if queue_handler is not None:
#     queue_handler.listener.start()
#     # atexit.register(queue_handler.listener.stop)


def json_log_refactor_and_xlsx():
    """
    Функция создаёт единый файл json_log.json из логов в файле json_log.jsonl, а также создаёт xlsx файл
    :return: None
    """
    json_list = []  # результирующий список словарей
    full_json_file = Path.absolute(log_file_json).parent / 'json_log.json'
    excel_file = Path.absolute(log_file_json).parent / 'xlsx_log.xlsx'
    try:
        with open(log_file_json, 'r') as original_file:
            for line in original_file.readlines():
                json_list.append(json.loads(line))
        with open(full_json_file, 'w') as full_j_file:
            json.dump(json_list, full_j_file, indent=2, ensure_ascii=True)
        # преобразование в excel
        df = pd.DataFrame(json_list)
        df.to_excel(excel_file, index=False)
        logger.info(f'json and xlsx log files created')
    except Exception as e:
        logger.error(f'error while creating json and xlsx log files')
        logger.exception(e)


if __name__ == '__main__':
    json_log_refactor_and_xlsx()

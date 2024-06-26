import re
import traceback
from pprint import pprint
import asyncio
import datetime
import socket
import json
from django.http import JsonResponse, HttpResponse, Http404
from django.db.models import Q
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework.exceptions import PermissionDenied
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework.views import APIView
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect, render

from m_logger_settings import logger  # noqa
from api.serializers import ShiftTaskSerializer, ShiftTaskIdSerializer  # noqa
from scheduler.models import ShiftTask  # noqa
from worker.services.master_call_function import get_client_ip, send_call_master, send_call_dispatcher  # noqa
from worker.views import resume_work  # noqa
from scheduler.models import WorkshopSchedule  # noqa


class ShiftTaskListView(ListAPIView):
    """
    Получение данных shift_task НЕИСПОЛЬЗУЕТСЯ
    """
    serializer_class = ShiftTaskSerializer

    def get(self, request, *args, **kwargs):
        allowed_terminal_list = ('APM-0036',  # Екименко
                                 'SPR-008',  # Терминал №3
                                 'APM-0168',  # Отто
                                 'APM-0314',  # Чекаловец
                                 'APM-0168',
                                 'TZ-001',  # Новые терминалы по порядку
                                 'TZ-002',
                                 'TZ-003',
                                 'TZ-004',
                                 'TZ-005',
                                 'TZ-006',
                                 'TZ-007',
                                 'TZ-008',
                                 'TZ-009',
                                 'APM-0229',  # Планшет
                                 )
        terminal_ip = get_client_ip(self.request)  # определение IP терминала
        terminal_name = socket.getfqdn(terminal_ip)  # определение полного имени по IP
        if terminal_name[:terminal_name.find('.')] not in allowed_terminal_list:
            raise PermissionDenied
        else:
            print(f'Permission granted to {terminal_name[:terminal_name.find(".")]}')
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        ws_number = self.kwargs.get('ws_number')
        today = datetime.datetime.now().strftime('%d.%m.%Y')
        shift_tasks = (ShiftTask.objects.values(
            'id', 'ws_number', 'model_name', 'order', 'op_number',
            'op_name_full', 'norm_tech', 'fio_doer', 'st_status',
            'datetime_job_start', 'decision_time'
        ).filter(
            ws_number=ws_number, next_shift_task=None
        ).exclude(
            fio_doer='не распределено'
        ).exclude(
            Q(decision_time__lte=datetime.datetime.strptime(today, '%d.%m.%Y')) & Q(st_status='принято')
        ).exclude(
            Q(decision_time__lte=datetime.datetime.strptime(today, '%d.%m.%Y')) & Q(st_status='брак')
        ).exclude(
            Q(decision_time__lte=datetime.datetime.strptime(today, '%d.%m.%Y')) & Q(st_status='не принято')
        ).order_by("st_status"))

        return shift_tasks


@method_decorator(csrf_exempt, name='dispatch')
class StartJobView(APIView):
    """
    Запуск СЗ в работу через API. НЕИСПОЛЬЗУЕТСЯ.
    """

    def post(self, request):
        serializer = ShiftTaskIdSerializer(data=self.request.data)
        success = False
        if serializer.is_valid():
            shift_task = ShiftTask.objects.get(pk=int(serializer.data['st_number']))
            if shift_task.st_status == 'запланировано':
                shift_task.st_status = 'в работе'
                shift_task.datetime_job_start = timezone.now()
                shift_task.datetime_job_resume = timezone.now()
                shift_task.job_duration = timezone.timedelta(0)
                shift_task.save()
                success = True
            elif shift_task.st_status == 'пауза':
                resume_work(task_id=int(serializer.data['st_number']))
                success = True
        return Response({"is_launched": success})


@method_decorator(csrf_exempt, name='dispatch')
class CallMaserView(APIView):
    """
    Обработка вызова мастера. НЕИСПОЛЬЗУЕТСЯ.
    """

    def post(self, request):
        serializer = ShiftTaskIdSerializer(data=self.request.data)
        success = False
        if serializer.is_valid():
            shift_task = ShiftTask.objects.get(pk=int(serializer.data['st_number']))
            message_to_master = (f"Мастера ожидают на Т{shift_task.ws_number}. "
                                 f"Номер СЗ: {shift_task.id}. "
                                 f"Заказ: {shift_task.order}. "
                                 f"Изделие: {shift_task.model_name}. "
                                 f"Операция: {shift_task.op_number} {shift_task.op_name_full}. "
                                 f"Исполнители: {shift_task.fio_doer}")
            try:
                asyncio.run(send_call_master(message_to_master, shift_task.ws_number))
                shift_task.master_called = 'вызван'
                shift_task.st_status = 'ожидание мастера'
                shift_task.master_calls += 1
                shift_task.save()
                # thread = threading.Thread(target=continue_work, args=(shift_task.id,))
                # thread.start()
                success = True
            except Exception:
                pass
        return Response({'is_called': success})


@method_decorator(csrf_exempt, name='dispatch')
class CallDispatcherView(APIView):
    """
    Обработка вызова диспетчера. НЕИСПОЛЬЗУЕТСЯ.
    """

    def post(self, request):
        serializer = ShiftTaskIdSerializer(data=self.request.data)
        success = False
        if serializer.is_valid():
            shift_task = ShiftTask.objects.get(pk=int(serializer.data['st_number']))
            message_to_dispatcher = (f"Диспетчера ожидают на Т{shift_task.ws_number}. "
                                     f"Номер СЗ: {shift_task.id}. "
                                     f"Заказ: {shift_task.order}. "
                                     f"Изделие: {shift_task.model_name}. "
                                     f"Операция: {shift_task.op_number} {shift_task.op_name_full}. "
                                     f"Исполнители: {shift_task.fio_doer}")
            try:
                asyncio.run(send_call_dispatcher(message_to_dispatcher, shift_task.ws_number))
                success = True
            except Exception:
                pass
        return Response({'is_called': success})


@csrf_exempt
def save_strat_plan(request):
    """
    Получение данных из страницы STRAT плана и их сохранение в БД
    :param request:
    :return:
    """
    model_pattern = r"^[\-A-Za-z0-9]+$"
    order_pattern = r"^[А-Яа-яA-Za-z0-9\(\)\-]+$"
    if request.method == 'POST':
        try:
            # получение данных
            data = json.loads(request.body)
            # обработка id новых записей - определение максимального id
            all_ids = WorkshopSchedule.objects.all().values_list('id', flat=True)
            next_max_id = max(list(all_ids)) + 1
            # добавление next_max_id вместо tmp
            for task in data['tasks']:
                # обработка некорректного ввода
                try:
                    if not re.match(order_pattern, task['code']) or task['code'] is None:
                        logger.error(f'Неверное имя заказа {task["code"]}.')
                        return HttpResponse({'status': 'error', 'message': 'order_error'}, status=400)
                    if not re.match(model_pattern, task['name']) or task['name'] is None:
                        logger.error(f'Неверное имя модели. {task["name"]}')
                        return HttpResponse({'status': 'error', 'message': 'model_error'}, status=400)
                except Exception as e:
                    traceback.print_exception(e)
                    return
                if 'tmp' in str(task['id']):
                    task['id'] = next_max_id
                    next_max_id = next_max_id + 1
            json_ids = [item['id'] for item in data['tasks']]  # все id для обновления
            schedules_to_update = WorkshopSchedule.objects.filter(pk__in=json_ids)  # все объекты для обновления
            # print(schedules_to_update[0])
            existing_ids = set(schedules_to_update.values_list('pk', flat=True))  # существующие id
            # словарь для получения данных json по id
            json_data_by_id = {item['id']: item for item in data['tasks']}
            # список для обновления данных
            for schedule in schedules_to_update:
                json_item = json_data_by_id[schedule.pk]
                # расчётная дата сдачи с + # TODO костыль компенсации смещения на 1 день
                schedule.calculated_datetime_done = ((datetime.datetime.fromtimestamp(json_item['end'] / 1000).date())
                                                     + datetime.timedelta(days=1))
                # степень готовности
                schedule.done_rate = json_item['progress']
                # цикл производства
                schedule.produce_cycle = json_item['duration']
                # расчётная дата запуска
                schedule.calculated_datetime_start = (schedule.calculated_datetime_done -
                                                      datetime.timedelta(days=schedule.produce_cycle))
                # фиксирование в графике
                schedule.is_fixed = json_item.get('is_fixed', False)
                # отставание дней
                schedule.late_days = json_item.get('late_days', 0)
                # статус завершено при готовности 100 %
                if json_item['progress'] >= 100:
                    schedule.order_status = 'завершено'
                else:
                    schedule.order_status = schedule.order_status

            # список для создания новых записей
            new_schedules = []
            try:
                for json_id in json_ids:
                    if json_id not in existing_ids:
                        json_item = json_data_by_id[json_id]

                        calculated_datetime_done = datetime.datetime.fromtimestamp(
                            int(json_item['end'] / 1000)).date()

                        if json_item['progress'] >= 100:
                            order_status = 'завершено'
                        elif json_item['progress'] == 0:
                            order_status = 'не запланировано'
                        else:
                            order_status = 'в работе'
                        produce_cycle = json_item['duration']

                        is_fixed = json_item.get('is_fixed', False)
                        new_schedule = WorkshopSchedule(
                            pk=json_id,
                            workshop=int(data['workshop']),
                            calculated_datetime_done=calculated_datetime_done,
                            datetime_done=calculated_datetime_done,
                            order=json_item['code'],
                            model_name=json_item['name'],
                            model_order_query=f"{json_item['code']}_{json_item['name']}",
                            td_status='не заказано',
                            order_status=order_status,
                            query_prior=4,
                            done_rate=json_item['progress'],
                            produce_cycle=produce_cycle,
                            is_fixed=is_fixed,
                            late_days=0
                        )
                        new_schedules.append(new_schedule)
            except Exception as e:
                logger.exception(e)
            # обновление данных
            try:
                WorkshopSchedule.objects.bulk_update(schedules_to_update,
                                                     ['calculated_datetime_done', 'done_rate', 'produce_cycle',
                                                      'order_status', 'is_fixed', 'calculated_datetime_start',
                                                      'late_days'])
                logger.debug('Данные планирования успешно обновлены.')
            except Exception as e:
                logger.error('Ошибка при обновлении данных WorkshopSchedule.')
                logger.exception(e)
            # добавление данных
            if new_schedules:
                try:
                    WorkshopSchedule.objects.bulk_create(new_schedules)
                    logger.debug(f'Данные планирования f{new_schedules} успешно добавлены.')
                except Exception as e:
                    logger.error('Ошибка при добавлении данных WorkshopSchedule.')
                    logger.exception(e)

            response_data = {
                'status': 'ok',
                'message': 'данные получены'
            }
            return JsonResponse(response_data, status=200)
        except json.JSONDecodeError as e:
            logger.error('Неверный формат JSON')
            logger.exception(e)
            return JsonResponse({'status': 'error', 'message': 'Неверный формат JSON'}, status=400)
    else:
        raise PermissionDenied


@csrf_exempt
def delete_model_from_start_plan(request, model_id):
    """
    Удаление модели из WorkshopSchedule по id из front strat_plan
    :param request:
    :param model_id:
    :return:
    """
    try:
        WorkshopSchedule.objects.get(pk=model_id).delete()
        logger.debug(f'Модель {model_id} успешно удалена из WorkshopSchedule.')
        return JsonResponse({'status': 'ok', 'message': f'{model_id} успешно удалена'}, status=200)
    except Exception as e:
        logger.error('Ошибка при удалении модели из WorkshopSchedule.')
        logger.exception(e)
        return JsonResponse({'status': 'error', 'message': 'Ошибка при удалении модели'}, status=500)

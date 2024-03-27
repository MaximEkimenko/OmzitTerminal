import asyncio
import datetime
import socket
import threading

from django.db.models import Q
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework.exceptions import PermissionDenied
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from api.serializers import ShiftTaskSerializer, ShiftTaskIdSerializer
from scheduler.models import ShiftTask
from worker.services.master_call_db import continue_work
from worker.services.master_call_function import get_client_ip, send_call_master, send_call_dispatcher
from worker.views import resume_work


class ShiftTaskListView(ListAPIView):
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

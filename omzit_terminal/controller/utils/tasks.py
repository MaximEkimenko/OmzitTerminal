from controller.utils.utils import add_defect_acts
def create_defect_act_at_first_run():
    """
    Первый запуск для формирования таблицы DefectAct из ShiftTask
    """
    add_defect_acts()

def add_defect_act_from_shift_task():
    """
    Ежедневные запуски для добавления новых записей о браке из ShiftTask
    """
    add_defect_acts()

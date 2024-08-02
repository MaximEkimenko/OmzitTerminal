from orders.utils.roles import Position

CONTROLLER = [Position.Admin, Position.Controller]
TECHNOLOG = [Position.Admin, Position.Technolog]
CHIEF = [Position.Admin, Position.HoS]

FIELD_EDIT_PERMISSIONS = {
    "datetime_fail": CONTROLLER,
    "workshop": CONTROLLER,
    "operation": CONTROLLER,
    "processing_object": CONTROLLER,
    "control_object": CONTROLLER,
    "quantity": CONTROLLER,
    "inconsistencies": CONTROLLER,
    "remark": CONTROLLER,
    "tech_service": TECHNOLOG,
    "tech_solution": TECHNOLOG,
    "fixable": TECHNOLOG,
    "fio_failer": CHIEF,
    "manual_fixing_time": CHIEF,
    "cause": TECHNOLOG,
    "master_finish_wp": CHIEF,
}

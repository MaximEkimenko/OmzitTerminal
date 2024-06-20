from django.urls import path
from .views import (
    equipment,
    orders,
    EquipmentCardView,
    EquipmentCardEditView,
    # OrderEditView,
    order_start_repair,
    order_finish_repair,
    order_accept_repair,
    order_revision,
    repair_orders_reports,
    order_clarify_repair,
    order_confirm_materials,
    order_info,
    order_edit,
    repair_history,
    order_cancel_repair,
    order_delete_proc,
    ShopsView,
    ShopsEdit,
    ShopsDelete,
    shop_delete_proc,
    shop_edit_proc,
)

urlpatterns = [
    path("equipment/", equipment, name="equipment"),
    path("equipment/<int:equipment_id>/", EquipmentCardView.as_view(), name="equipment_card"),
    path(
        "equipment_edit/<int:equipment_id>/",
        EquipmentCardEditView.as_view(),
        name="equipment_card_edit",
    ),
    path("start_repair/<int:pk>", order_start_repair, name="start_repair"),
    path("clarify_repair/<int:pk>", order_clarify_repair, name="clarify_repair"),
    path("confirm_materials/<int:pk>", order_confirm_materials, name="confirm_materials"),
    path("finish_repair/<int:pk>", order_finish_repair, name="finish_repair"),
    path("accept_repair/<int:pk>", order_accept_repair, name="accept_repair"),
    path("revision_repair/<int:pk>", order_revision, name="revision_repair"),
    path("cancel_repair/<int:pk>", order_cancel_repair, name="cancel_repair"),
    path("order_info/<int:pk>", order_info, name="order_info"),
    # path("orders/<int:pk>", OrderEditView.as_view(), name="orders_edit"),
    path("orders/", orders, name="orders"),
    path("orders_report/", repair_orders_reports, name="orders_report"),
    path("order_delete_proc/", order_delete_proc, name="order_delete_proc"),
    path("edit_repair/<int:pk>", order_edit, name="edit_repair"),
    path("repair_history/<int:pk>", repair_history, name="repair_history"),
    path("shops/", ShopsView.as_view(), name="shops"),
    path("shops_edit/<int:pk>", ShopsEdit.as_view(), name="shops_edit"),
    path("shops_delete/<int:pk>", ShopsDelete.as_view(), name="shops_delete"),
    path("shop_edit/", shop_edit_proc, name="shop_edit"),
    path("shops_delete/", shop_delete_proc, name="shop_delete"),
]
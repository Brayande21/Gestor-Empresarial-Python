from types import SimpleNamespace

from ui import admin_view


def test_on_task_double_click_opens_order_editor_not_customer_dialog(monkeypatch):
    calls = []

    view = admin_view.AdminView.__new__(admin_view.AdminView)
    view.tree = SimpleNamespace(
        identify_row=lambda y: 'row-1',
        item=lambda row_id, field: {'values': (42,)} if field == 'values' else {}
    )
    view.task_service = SimpleNamespace(get_task=lambda task_id: {'id': 42, 'customer_id': 7})
    view.customer_service = SimpleNamespace(get_customer=lambda customer_id: {'id': 7, 'full_name': 'Cliente Demo'})
    view.edit_task = lambda task_id: calls.append(task_id)

    event = SimpleNamespace(y=10)
    view.on_task_double_click(event)

    assert calls == [42]

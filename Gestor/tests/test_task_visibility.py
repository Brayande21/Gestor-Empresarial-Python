import sqlite3

import config
from database.connection import init_db
from business.task_service import TaskService


def _insert_user(db_path, username, full_name, role, user_id=None):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    if user_id is not None:
        cursor.execute(
            "INSERT INTO users (id, username, password_hash, full_name, email, role, department, position, is_active) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1)",
            (user_id, username, 'hash', full_name, f'{username}@test.com', role, 'Dept', 'Cargo'),
        )
    else:
        cursor.execute(
            "INSERT INTO users (username, password_hash, full_name, email, role, department, position, is_active) VALUES (?, ?, ?, ?, ?, ?, ?, 1)",
            (username, 'hash', full_name, f'{username}@test.com', role, 'Dept', 'Cargo'),
        )
    conn.commit()
    conn.close()


def test_manager_sees_all_tasks_when_has_management_access(tmp_path, monkeypatch):
    db_path = tmp_path / 'empresa.db'
    monkeypatch.setattr(config, 'DATABASE_PATH', db_path)
    init_db()
    _insert_user(db_path, 'gerente_test', 'Gerente Test', 'manager', 7)
    _insert_user(db_path, 'taller_test', 'Taller Test', 'taller', 5)
    _insert_user(db_path, 'admin_test', 'Admin Test', 'admin', 101)
    _insert_user(db_path, 'servicio_test', 'Servicio Test', 'service_client', 102)

    service = TaskService()
    gerente_task = service.create_task(
        title='orden gerente 1',
        description='visible para gerente',
        priority='high',
        estimated_hours=2,
        due_date='2030-01-10',
        assigned_to=None,
        assigned_by=7,
        created_by=7,
    )
    assigned_task = service.create_task(
        title='orden gerente 2',
        description='otra visible para gerente',
        priority='medium',
        estimated_hours=3,
        due_date='2030-01-11',
        assigned_to=5,
        assigned_by=7,
        created_by=5,
    )
    admin_task = service.create_task(
        title='orden admin visible',
        description='visible por admin',
        priority='low',
        estimated_hours=1,
        due_date='2030-01-12',
        assigned_to=None,
        assigned_by=101,
        created_by=101,
    )
    service_client_task = service.create_task(
        title='orden servicio visible',
        description='visible por servicio al cliente',
        priority='urgent',
        estimated_hours=4,
        due_date='2030-01-13',
        assigned_to=7,
        assigned_by=102,
        created_by=102,
    )

    visible = service.get_visible_tasks(7, 'manager')
    visible_ids = {task['id'] for task in visible}

    assert gerente_task in visible_ids
    assert assigned_task in visible_ids
    assert admin_task in visible_ids
    assert service_client_task in visible_ids


def test_service_client_sees_all_tasks(tmp_path, monkeypatch):
    db_path = tmp_path / 'empresa.db'
    monkeypatch.setattr(config, 'DATABASE_PATH', db_path)
    init_db()
    _insert_user(db_path, 'servicio_test', 'Servicio Test', 'service_client', 102)
    _insert_user(db_path, 'admin_test', 'Admin Test', 'admin', 101)

    service = TaskService()
    task_1 = service.create_task(
        title='orden desde servicio',
        description='creada por servicio',
        priority='medium',
        estimated_hours=2,
        due_date='2030-01-14',
        assigned_to=None,
        assigned_by=102,
        created_by=102,
    )
    task_2 = service.create_task(
        title='orden desde admin',
        description='creada por admin',
        priority='high',
        estimated_hours=3,
        due_date='2030-01-15',
        assigned_to=None,
        assigned_by=101,
        created_by=101,
    )

    visible = service.get_visible_tasks(102, 'service_client')
    visible_ids = {task['id'] for task in visible}

    assert task_1 in visible_ids
    assert task_2 in visible_ids


def test_assignable_users_are_only_taller(tmp_path, monkeypatch):
    from business.auth_service import AuthService

    db_path = tmp_path / 'empresa.db'
    monkeypatch.setattr(config, 'DATABASE_PATH', db_path)
    init_db()

    auth = AuthService()
    auth.create_user('admin_test', '123', 'Admin', 'admin@test.com', 'admin')
    auth.create_user('manager_test', '123', 'Gerente', 'gerente@test.com', 'manager')
    auth.create_user('taller_1', '123', 'Taller Uno', 'taller1@test.com', 'taller')
    auth.create_user('service_test', '123', 'Servicio', 'servicio@test.com', 'service_client')

    assignable = auth.get_assignable_users()
    roles = {user['role'] for user in assignable}

    assert roles == {'taller'}
    assert all(user['role'] == 'taller' for user in assignable)


def test_completed_tasks_do_not_show_in_user_worklist(tmp_path, monkeypatch):
    db_path = tmp_path / 'empresa.db'
    monkeypatch.setattr(config, 'DATABASE_PATH', db_path)
    init_db()

    service = TaskService()
    task_active = service.create_task(
        title='orden activa',
        description='debe verse',
        priority='medium',
        estimated_hours=2,
        due_date='2030-01-20',
        assigned_to=9,
        assigned_by=1,
        created_by=1,
    )
    task_done = service.create_task(
        title='orden completada',
        description='no debe verse',
        priority='low',
        estimated_hours=1,
        due_date='2030-01-21',
        assigned_to=9,
        assigned_by=1,
        created_by=1,
    )
    service.update_task(task_done, status='completed')

    tasks = service.get_user_tasks(9)
    task_ids = {task['id'] for task in tasks}

    assert task_active in task_ids
    assert task_done not in task_ids


def test_completed_tasks_are_excluded_from_active_lists(tmp_path, monkeypatch):
    db_path = tmp_path / 'empresa.db'
    monkeypatch.setattr(config, 'DATABASE_PATH', db_path)
    init_db()

    service = TaskService()
    active_id = service.create_task(
        title='activa',
        description='debe verse',
        priority='medium',
        estimated_hours=2,
        due_date='2030-02-01',
        assigned_to=None,
        assigned_by=1,
        created_by=1,
    )
    done_id = service.create_task(
        title='completada',
        description='no debe verse',
        priority='low',
        estimated_hours=1,
        due_date='2030-02-01',
        assigned_to=None,
        assigned_by=1,
        created_by=1,
    )
    service.update_task(done_id, status='completed')

    active_ids = {task['id'] for task in service.get_all_tasks()}
    assert active_id in active_ids
    assert done_id not in active_ids


def test_employee_workflow_advances_through_stages(tmp_path, monkeypatch):
    import tkinter as tk
    from ui.employee_view import EmployeeView

    db_path = tmp_path / 'empresa.db'
    monkeypatch.setattr(config, 'DATABASE_PATH', db_path)
    init_db()

    root = tk.Tk()
    root.withdraw()

    class DummyAuth:
        def __init__(self):
            self.user = {'id': 9, 'full_name': 'Taller Tester', 'role': 'taller'}
        def get_current_user(self):
            return self.user

    try:
        view = EmployeeView(root, DummyAuth(), TaskService(), mode='taller')
        task_id = view.task_service.create_task(
            title='orden flujo',
            description='prueba',
            priority='high',
            estimated_hours=4,
            due_date='2030-05-01',
            assigned_to=9,
            assigned_by=1,
            created_by=1,
        )

        sequence = ['design', 'machine', 'cleaning', 'transit', 'completed']
        for expected in sequence:
            view.advance_task_status(task_id)
            assert view.task_service.get_task(task_id)['status'] == expected
    finally:
        root.destroy()


def test_customer_support_view_initializes_without_crash():
    import tkinter as tk
    from ui.customer_support_view import CustomerSupportView

    root = tk.Tk()
    root.withdraw()

    class DummyAuth:
        def get_current_user(self):
            return {'id': 1, 'full_name': 'Servicio', 'role': 'service_client'}

    try:
        view = CustomerSupportView(root, DummyAuth(), TaskService(), mode='service_client')
        assert hasattr(view, 'notebook')
        assert len(view.notebook.tabs()) >= 4
    finally:
        root.destroy()


def test_service_client_view_supports_order_and_customer_editing():
    import tkinter as tk
    from ui.customer_support_view import CustomerSupportView

    root = tk.Tk()
    root.withdraw()

    class DummyAuth:
        def get_current_user(self):
            return {'id': 1, 'full_name': 'Servicio', 'role': 'service_client'}

    try:
        view = CustomerSupportView(root, DummyAuth(), TaskService(), mode='service_client')
        assert hasattr(view, 'edit_order')
        assert hasattr(view, 'edit_customer')
        assert hasattr(view, 'on_order_double_click')
    finally:
        root.destroy()


def test_service_client_logout_returns_to_login(monkeypatch):
    from types import SimpleNamespace
    from ui.customer_support_view import CustomerSupportView

    calls = []
    view = CustomerSupportView.__new__(CustomerSupportView)
    view.auth_service = SimpleNamespace(logout=lambda: calls.append('logout'))
    view.parent = SimpleNamespace()
    view.parent._logout_to_login = lambda: calls.append('login')
    monkeypatch.setattr('ui.customer_support_view.messagebox.askyesno', lambda *args, **kwargs: True)

    view.logout()

    assert calls == ['login']


def test_admin_sees_all_tasks(tmp_path, monkeypatch):
    db_path = tmp_path / 'empresa.db'
    monkeypatch.setattr(config, 'DATABASE_PATH', db_path)
    init_db()

    service = TaskService()
    service.create_task(
        title='orden admin 1',
        description='visible para admin',
        priority='low',
        estimated_hours=1,
        due_date='2030-01-12',
        assigned_to=None,
        assigned_by=1,
        created_by=1,
    )
    service.create_task(
        title='orden admin 2',
        description='otra visible para admin',
        priority='critical',
        estimated_hours=5,
        due_date='2030-01-13',
        assigned_to=2,
        assigned_by=1,
        created_by=1,
    )

    visible = service.get_visible_tasks(1, 'admin')

    assert len(visible) >= 2

import tkinter as tk

import pytest

from business.customer_service import CustomerService
from business.task_service import TaskService
from ui.dialogs.customer_dialog import CustomerDialog


def test_validate_customer_data_individual_requires_all_fields():
    with pytest.raises(ValueError, match='nombre completo|documento|email|teléfono|ciudad|dirección'):
        CustomerDialog.validate_customer_data(
            'individual',
            {
                'full_name': 'Ana García',
                'document_type': 'Cédula de 11 dígitos - Nacional',
                'document_id': '12345678901',
                'email': '',
                'phone': '',
                'city': '',
                'address': ''
            }
        )


def test_validate_customer_data_company_requires_all_fields():
    with pytest.raises(ValueError, match='razón social|RNC|teléfono comercial|ciudad|dirección'):
        CustomerDialog.validate_customer_data(
            'company',
            {
                'company_name': 'Empresa Demo',
                'company_ruc_type': 'RNC de 9 dígitos - Personas Jurídicas',
                'company_ruc': '123456789',
                'contact_name': 'Juan Pérez',
                'business_type': 'Consultoría',
                'email': 'info@demo.com',
                'company_phone': '',
                'city': '',
                'company_address': '',
            }
        )


def test_validate_document_type_passport_allows_letters_and_numbers():
    dialog = CustomerDialog.__new__(CustomerDialog)
    is_valid, error_msg = dialog.validate_document_type('Pasaporte', 'AB12345')
    assert is_valid is True
    assert error_msg is None


def test_validate_document_type_license_requires_11_digits():
    dialog = CustomerDialog.__new__(CustomerDialog)
    is_valid, error_msg = dialog.validate_document_type('Licencia de conducir', '12345678901')
    assert is_valid is True
    assert error_msg is None

    is_valid, error_msg = dialog.validate_document_type('Licencia de conducir', '1234567890')
    assert is_valid is False
    assert '11 dígitos' in error_msg


def test_validate_customer_data_rejects_letters_in_phone_numbers():
    with pytest.raises(ValueError, match='teléfono|comercial'):
        CustomerDialog.validate_customer_data(
            'individual',
            {
                'full_name': 'Ana García',
                'document_type': 'Cédula de 11 dígitos - Nacional',
                'document_id': '12345678901',
                'email': 'ana@test.com',
                'phone': '809-123-ABCD',
                'city': 'Santo Domingo',
                'address': 'Calle 1'
            }
        )

    with pytest.raises(ValueError, match='teléfono comercial'):
        CustomerDialog.validate_customer_data(
            'company',
            {
                'company_name': 'Empresa Demo',
                'company_ruc_type': 'RNC de 9 dígitos - Personas Jurídicas',
                'company_ruc': '123456789',
                'email': 'info@demo.com',
                'company_phone': '809-555-ABCD',
                'city': 'Santo Domingo',
                'company_address': 'Calle Comercial 2'
            }
        )


def test_validate_customer_data_rejects_whitespace_only_values():
    with pytest.raises(ValueError, match='nombre completo|documento|email|teléfono|ciudad|dirección'):
        CustomerDialog.validate_customer_data(
            'individual',
            {
                'full_name': '   ',
                'document_type': '  ',
                'document_id': '   ',
                'email': '     ',
                'phone': '   ',
                'city': '  ',
                'address': '   '
            }
        )

    with pytest.raises(ValueError, match='RNC|teléfono comercial|persona de contacto|ciudad|dirección'):
        CustomerDialog.validate_customer_data(
            'company',
            {
                'company_ruc_type': '  ',
                'company_ruc': '   ',
                'email': '    ',
                'company_phone': '   ',
                'contact_phone': '   ',
                'city': '   ',
                'company_address': '   '
            }
        )


def test_build_form_keeps_document_id_when_editing_individual_customer():
    root = tk.Tk()
    root.withdraw()
    try:
        dialog = CustomerDialog.__new__(CustomerDialog)
        dialog.parent = root
        dialog.customer_service = CustomerService()
        dialog.on_save_callback = None
        dialog.customer = {
            'id': 1,
            'customer_type': 'individual',
            'full_name': 'Ana García',
            'document_type': 'Cédula de 11 dígitos - Nacional',
            'document_id': '12345678901',
            'email': 'ana@test.com',
            'phone': '8091234567',
            'city': 'Santo Domingo',
            'address': 'Calle 1',
        }
        dialog.type_var = tk.StringVar(value='individual')
        dialog.dynamic_frame = tk.Frame(root)
        dialog.filter_combo = lambda combo, values: None
        dialog._apply_required_style = lambda widget, is_required: None
        dialog._reset_required_styles = lambda: None
        dialog._mark_missing_required = lambda missing: None

        dialog.build_form()

        doc_entry = dialog.entries['document_id']
        assert doc_entry.get() == '12345678901'
        assert doc_entry.cget('state') == 'normal'
    finally:
        root.destroy()


def test_document_type_combo_is_readonly():
    root = tk.Tk()
    root.withdraw()
    try:
        dialog = CustomerDialog.__new__(CustomerDialog)
        dialog.parent = root
        dialog.customer_service = CustomerService()
        dialog.on_save_callback = None
        dialog.customer = None
        dialog.type_var = tk.StringVar(value='individual')
        dialog.dynamic_frame = tk.Frame(root)
        dialog.filter_combo = lambda combo, values: None
        dialog._apply_required_style = lambda widget, is_required: None
        dialog._reset_required_styles = lambda: None
        dialog._mark_missing_required = lambda missing: None

        dialog.build_form()

        assert str(dialog.entries['document_type'].cget('state')) == 'readonly'
    finally:
        root.destroy()


def test_document_type_change_clears_existing_value_only_when_incompatible():
    root = tk.Tk()
    root.withdraw()
    try:
        dialog = CustomerDialog.__new__(CustomerDialog)
        dialog.parent = root
        dialog.customer_service = CustomerService()
        dialog.on_save_callback = None
        dialog.customer = None
        dialog.type_var = tk.StringVar(value='individual')
        dialog.dynamic_frame = tk.Frame(root)
        dialog.filter_combo = lambda combo, values: None
        dialog._apply_required_style = lambda widget, is_required: None
        dialog._reset_required_styles = lambda: None
        dialog._mark_missing_required = lambda missing: None
        dialog._last_document_type_selection = None

        dialog.build_form()
        dialog.entries['document_type'].set('Cédula de 11 dígitos - Nacional')
        dialog._last_document_type_selection = 'Cédula de 11 dígitos - Nacional'
        dialog.entries['document_id'].configure(state='normal')
        dialog.entries['document_id'].delete(0, tk.END)
        dialog.entries['document_id'].insert(0, '1234567890')

        dialog.entries['document_type'].set('Licencia de conducir')
        dialog.update_document_field_state()

        assert dialog.entries['document_id'].get() == ''
    finally:
        root.destroy()


def test_company_rnc_type_change_clears_existing_value_only_when_incompatible():
    root = tk.Tk()
    root.withdraw()
    try:
        dialog = CustomerDialog.__new__(CustomerDialog)
        dialog.parent = root
        dialog.customer_service = CustomerService()
        dialog.on_save_callback = None
        dialog.customer = None
        dialog.type_var = tk.StringVar(value='company')
        dialog.dynamic_frame = tk.Frame(root)
        dialog.filter_combo = lambda combo, values: None
        dialog._apply_required_style = lambda widget, is_required: None
        dialog._reset_required_styles = lambda: None
        dialog._mark_missing_required = lambda missing: None
        dialog._last_rnc_type_selection = None

        dialog.build_form()
        dialog.entries['company_ruc_type'].set('RNC de 9 dígitos - Personas Jurídicas')
        dialog._last_rnc_type_selection = 'RNC de 9 dígitos - Personas Jurídicas'
        dialog.entries['company_ruc'].configure(state='normal')
        dialog.entries['company_ruc'].delete(0, tk.END)
        dialog.entries['company_ruc'].insert(0, '12345678')

        dialog.entries['company_ruc_type'].set('RNC de 11 dígitos - Personas Físicas nacionales')
        dialog.update_rnc_field_state()

        assert dialog.entries['company_ruc'].get() == ''
    finally:
        root.destroy()


def test_update_customer_clears_old_individual_fields_when_switching_to_company():
    service = CustomerService()
    customer_id = service.create_customer(
        customer_type='individual',
        full_name='Ana García',
        document_type='Cédula de 11 dígitos - Nacional',
        document_id='12345678901',
        email='ana@test.com',
        phone='8091234567',
        city='Santo Domingo',
        address='Calle 1',
    )

    assert customer_id is not None

    assert service.update_customer(
        customer_id,
        customer_type='company',
        full_name='Empresa Demo',
        company_name='Empresa Demo',
        company_phone='8095550000',
        company_address='Calle Comercial 2',
        contact_person='Juan Pérez',
        contact_phone='8094440000',
        business_type='Consultoría',
        email='info@demo.com',
        city='Santo Domingo',
        document_type=None,
        document_id=None,
        phone=None,
        address=None,
        notes=None,
    ) is True

    updated = service.get_customer(customer_id)
    assert updated['customer_type'] == 'company'
    assert updated['full_name'] == 'Empresa Demo'
    assert updated['document_type'] is None
    assert updated['document_id'] is None
    assert updated['phone'] is None
    assert updated['address'] is None


def test_company_customer_saves_document_type_and_id():
    service = CustomerService()
    customer_id = service.create_customer(
        customer_type='company',
        full_name='Empresa Demo',
        company_name='Empresa Demo',
        document_type='RNC de 9 dígitos - Personas Jurídicas',
        document_id='223456799',
        email='info@demo.com',
        phone=None,
        address=None,
        city='Santo Domingo',
        company_phone='8095550000',
        company_address='Calle Comercial 2',
        contact_person='Juan Pérez',
        contact_phone='8094440000',
        business_type='Consultoría',
        notes=None,
    )

    assert customer_id is not None
    customer = service.get_customer(customer_id)
    assert customer['customer_type'] == 'company'
    assert customer['document_type'] == 'RNC de 9 dígitos - Personas Jurídicas'
    assert customer['document_id'] == '223456799'


def test_same_document_id_can_be_used_across_customer_types():
    service = CustomerService()
    individual_id = service.create_customer(
        customer_type='individual',
        full_name='Ana García',
        document_type='Cédula de 11 dígitos - Nacional',
        document_id='12345678901',
        email='ana@test.com',
        phone='8091234567',
        city='Santo Domingo',
        address='Calle 1',
    )
    assert individual_id is not None

    company_id = service.create_customer(
        customer_type='company',
        full_name='Empresa Demo',
        company_name='Empresa Demo',
        document_type='RNC de 9 dígitos - Personas Jurídicas',
        document_id='12345678901',
        email='info@demo.com',
        city='Santo Domingo',
        company_phone='8095550000',
        company_address='Calle Comercial 2',
        contact_person='Juan Pérez',
        contact_phone='8094440000',
        business_type='Consultoría',
    )

    assert company_id is not None
    assert service.get_customer(company_id)['customer_type'] == 'company'
    assert service.get_customer(individual_id)['document_id'] == '12345678901'


def test_toggle_type_prompts_before_switching_existing_customer_type(monkeypatch):
    import tkinter.messagebox as messagebox

    root = tk.Tk()
    root.withdraw()
    try:
        dialog = CustomerDialog.__new__(CustomerDialog)
        dialog.parent = root
        dialog.customer_service = CustomerService()
        dialog.on_save_callback = None
        dialog.customer = {'id': 1, 'customer_type': 'individual'}
        dialog.type_var = tk.StringVar(value='individual')
        dialog.dynamic_frame = tk.Frame(root)
        dialog.build_form = lambda: None
        dialog.entries = {}

        confirmed = {'value': False}

        def fake_confirm(title, msg):
            confirmed['value'] = True
            return False

        monkeypatch.setattr(messagebox, 'askyesno', fake_confirm)

        dialog.type_var.set('company')
        dialog.toggle_type()

        assert confirmed['value'] is True
        assert dialog.type_var.get() == 'individual'
    finally:
        root.destroy()


def test_update_customer_changes_document_id_and_type(tmp_path, monkeypatch):
    import config
    from database.connection import init_db

    db_path = tmp_path / 'empresa.db'
    monkeypatch.setattr(config, 'DATABASE_PATH', db_path)
    init_db()

    service = CustomerService()
    customer_id = service.create_customer(
        customer_type='individual',
        full_name='Ana García',
        document_id='12345678901',
        document_type='Cédula de 11 dígitos - Nacional',
        email='ana@test.com',
        phone='8091234567',
        city='Santo Domingo',
        address='Calle 1',
    )

    updated = service.update_customer(
        customer_id,
        document_id='98765432109',
        document_type='Licencia de conducir',
        full_name='Ana García',
        email='ana@test.com',
        phone='8091234567',
        city='Santo Domingo',
        address='Calle 1',
    )

    assert updated is True
    customer = service.get_customer(customer_id)
    assert customer['document_id'] == '98765432109'
    assert customer['document_type'] == 'Licencia de conducir'


def test_update_customer_keeps_same_record_instead_of_creating_duplicate(tmp_path, monkeypatch):
    import config
    from database.connection import init_db

    db_path = tmp_path / 'empresa.db'
    monkeypatch.setattr(config, 'DATABASE_PATH', db_path)
    init_db()

    service = CustomerService()
    customer_id = service.create_customer(
        customer_type='individual',
        full_name='Ana García',
        document_id='12345678901',
        email='ana@test.com',
        phone='8091234567',
        city='Santo Domingo',
        address='Calle 1',
    )

    updated = service.update_customer(customer_id, full_name='Ana García', city='Santiago', email='ana.nueva@test.com')

    assert updated is True
    customer = service.get_customer(customer_id)
    assert customer['city'] == 'Santiago'
    assert customer['email'] == 'ana.nueva@test.com'
    assert customer['id'] == customer_id


def test_update_task_keeps_same_record_id(tmp_path, monkeypatch):
    import config
    from database.connection import init_db

    db_path = tmp_path / 'empresa.db'
    monkeypatch.setattr(config, 'DATABASE_PATH', db_path)
    init_db()

    service = CustomerService()
    customer_id = service.create_customer(
        customer_type='individual',
        full_name='Cliente orden',
        document_id='98765432109',
        email='orden@test.com',
        phone='8095550000',
        city='Santo Domingo',
        address='Calle 2',
    )

    task_service = TaskService()
    task_id = task_service.create_task(
        title='ORD-100',
        description='descripción original',
        priority='medium',
        estimated_hours=2,
        due_date='2030-01-05',
        assigned_to=None,
        assigned_by=1,
        created_by=1,
        customer_id=customer_id,
    )

    updated = task_service.update_task(task_id, title='ORD-100', description='descripción editada', priority='high')

    assert updated is True
    task = task_service.get_task(task_id)
    assert task['id'] == task_id
    assert task['description'] == 'descripción editada'
    assert task['priority'] == 'high'

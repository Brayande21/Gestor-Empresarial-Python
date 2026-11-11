import pytest

from business.task_service import TaskService


def test_validate_task_data_accepts_complete_order():
    service = TaskService()

    result = service.validate_task_data(
        title='ORD-1001',
        customer_id=7,
        priority='high',
        due_date='2026-08-20',
        description='Revisión completa del equipo'
    )

    assert result is True


def test_validate_task_data_rejects_missing_required_fields():
    service = TaskService()

    with pytest.raises(ValueError, match='orden|cliente|prioridad|descripción'):
        service.validate_task_data(title='', customer_id=7, priority='high', description='Texto')

    with pytest.raises(ValueError, match='cliente|prioridad|descripción'):
        service.validate_task_data(title='ORD-1001', customer_id=None, priority='high', description='Texto')

    with pytest.raises(ValueError, match='prioridad|vencimiento|descripción'):
        service.validate_task_data(title='ORD-1001', customer_id=7, priority='', description='Texto')

    with pytest.raises(ValueError, match='descripción'):
        service.validate_task_data(title='ORD-1001', customer_id=7, priority='high', due_date='2026-08-20', description='')

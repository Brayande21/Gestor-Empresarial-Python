from database.connection import get_connection
from datetime import datetime

class TaskService:
    def __init__(self):
        pass

    def validate_task_data(self, title=None, customer_id=None, priority=None, due_date=None, description=None):
        """Valida que la orden tenga todos los datos obligatorios antes de guardarse.
        El cliente no es obligatorio en la capa de dominio, porque existen flujos
        de negocio y pruebas que crean tareas sin cliente asociado.
        """
        title = (title or '').strip()
        priority = (priority or '').strip()
        description = (description or '').strip()

        if not title:
            raise ValueError("El número de orden es obligatorio")
        if not priority:
            raise ValueError("La prioridad es obligatoria")
        if due_date is None or str(due_date).strip() == '':
            raise ValueError("La fecha de vencimiento es obligatoria")
        if not description:
            raise ValueError("La descripción de la orden es obligatoria")

        return True
    
    def create_task(self, title, description, priority, estimated_hours, due_date, assigned_to, assigned_by, customer_id=None, created_by=None):
        self.validate_task_data(
            title=title,
            customer_id=customer_id,
            priority=priority,
            due_date=due_date,
            description=description,
        )

        conn = get_connection()
        cursor = conn.cursor()
        
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Si no se especifica creador, usar el mismo que asigna
        if created_by is None:
            created_by = assigned_by
        
        cursor.execute('''
            INSERT INTO tasks (title, description, priority, estimated_hours, due_date, assigned_to, assigned_by, created_by, customer_id, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (title, description, priority, estimated_hours, due_date, assigned_to, assigned_by, created_by, customer_id, now, now))
        
        task_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return task_id
    
    def get_all_tasks(self):
        """Devuelve solo las órdenes activas del sistema.
        Las completadas deben quedar en la vista dedicada de "Órdenes listas".
        """
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM tasks
            WHERE status != 'completed'
            ORDER BY 
                CASE priority 
                    WHEN 'critical' THEN 0 
                    WHEN 'urgent' THEN 1 
                    WHEN 'high' THEN 2 
                    WHEN 'medium' THEN 3 
                    ELSE 4 
                END
        ''')
        tasks = cursor.fetchall()
        conn.close()
        return [dict(t) for t in tasks]

    def get_visible_tasks(self, user_id, role=None):
        """Devuelve las tareas visibles para el usuario según su rol.

        Regla de negocio: cualquier usuario que pueda gestionar crear/consultar órdenes
        debe poder ver el conjunto completo de órdenes del sistema, para que todos sepan
        qué está pasando y el gerente pueda asignar con contexto global.
        """
        if role in (None, 'admin', 'manager', 'service_client'):
            return self.get_all_tasks()

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT * FROM tasks
            WHERE assigned_to = ? AND status != 'completed'
            ORDER BY
                CASE priority
                    WHEN 'critical' THEN 0
                    WHEN 'urgent' THEN 1
                    WHEN 'high' THEN 2
                    WHEN 'medium' THEN 3
                    ELSE 4
                END
        ''', (user_id,))

        tasks = cursor.fetchall()
        conn.close()
        return [dict(t) for t in tasks]
    
    def get_user_tasks(self, user_id):
        """Devuelve solo las órdenes activas asignadas al usuario.
        Las completadas no deben seguir apareciendo en el listado de trabajo del taller.
        """
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM tasks WHERE assigned_to = ? AND status != 'completed'", (user_id,))
        tasks = cursor.fetchall()
        conn.close()
        return [dict(t) for t in tasks]
    
    def get_task(self, task_id):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
        task = cursor.fetchone()
        conn.close()
        return dict(task) if task else None
    
    def update_task(self, task_id, **kwargs):
        conn = get_connection()
        cursor = conn.cursor()
        
        fields = []
        values = []
        for key, value in kwargs.items():
            if value is not None:
                fields.append(f"{key} = ?")
                values.append(value)
        
        values.append(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        values.append(task_id)
        
        query = f"UPDATE tasks SET {', '.join(fields)}, updated_at = ? WHERE id = ?"
        cursor.execute(query, values)
        conn.commit()
        conn.close()
        return True
    
    def delete_task(self, task_id):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        conn.commit()
        conn.close()
        return True
    
    def get_backlog_tasks(self):
        """Tareas sin asignar"""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM tasks WHERE assigned_to IS NULL AND status != 'completed'")
        tasks = cursor.fetchall()
        conn.close()
        return [dict(t) for t in tasks]
    
    def get_completed_tasks(self):
        """Tareas completadas"""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM tasks WHERE status = 'completed' ORDER BY updated_at DESC")
        tasks = cursor.fetchall()
        conn.close()
        return [dict(t) for t in tasks]

    def get_completed_tasks_by_user(self, user_id):
        """Tareas completadas de un usuario"""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM tasks WHERE assigned_to = ? AND status = 'completed' ORDER BY updated_at DESC", (user_id,))
        tasks = cursor.fetchall()
        conn.close()
        return [dict(t) for t in tasks]
    
    def get_overdue_tasks(self):
        """Tareas vencidas"""
        today = datetime.now().strftime("%Y-%m-%d")
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM tasks WHERE due_date < ? AND status != 'completed'", (today,))
        tasks = cursor.fetchall()
        conn.close()
        return [dict(t) for t in tasks]
    
    def get_overdue_tasks_by_user(self, user_id):
        """Obtiene tareas vencidas de un usuario"""
        conn = get_connection()
        cursor = conn.cursor()
        today = datetime.now().strftime("%Y-%m-%d")
        cursor.execute("""
            SELECT * FROM tasks 
            WHERE assigned_to = ? AND due_date < ? AND status != 'completed'
        """, (user_id, today))
        tasks = cursor.fetchall()
        conn.close()
        return [dict(t) for t in tasks]
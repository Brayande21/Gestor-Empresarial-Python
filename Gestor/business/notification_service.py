import tkinter as tk
from tkinter import ttk
import threading
import time

class NotificationService:
    def __init__(self, task_service, auth_service):
        self.task_service = task_service
        self.auth_service = auth_service
        self.notifications = []
        self.monitoring = False
        self.monitor_thread = None
        self.current_user_id = None
    
    def start_monitoring(self, user_id):
        """Inicia el monitoreo de tareas asignadas"""
        self.current_user_id = user_id
        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_tasks, daemon=True)
        self.monitor_thread.start()
    
    def stop_monitoring(self):
        """Detiene el monitoreo de tareas"""
        self.monitoring = False
    
    def _monitor_tasks(self):
        """Thread que monitorea tareas en background"""
        while self.monitoring:
            try:
                tasks = self.task_service.get_all_tasks()
                for task in tasks:
                    # Verificar si hay tareas asignadas al usuario actual
                    if task['assigned_to'] == self.current_user_id:
                        if task['status'] == 'pending' and task not in [n.get('task_id') for n in self.notifications]:
                            self.notifications.append({
                                'title': '📌 Nueva tarea asignada',
                                'message': f"Te han asignado: {task['title']}",
                                'task_id': task['id'],
                                'type': 'new_task'
                            })
                    
                    # Verificar tareas vencidas
                    if task['due_date'] and task['status'] != 'completed':
                        from datetime import datetime
                        due = datetime.strptime(task['due_date'], '%Y-%m-%d')
                        if due < datetime.now():
                            notif_exists = any(n.get('type') == 'overdue' and n.get('task_id') == task['id'] for n in self.notifications)
                            if not notif_exists:
                                self.notifications.append({
                                    'title': '⚠️ Tarea vencida',
                                    'message': f"La tarea '{task['title']}' está vencida",
                                    'task_id': task['id'],
                                    'type': 'overdue'
                                })
                
                time.sleep(5)  # Verificar cada 5 segundos
            except Exception as e:
                print(f"Error en monitoreo: {e}")
                time.sleep(5)
    
    def clear_notifications(self):
        """Limpia todas las notificaciones"""
        self.notifications = []
    
    def add_notification(self, title, message):
        """Agrega una notificación manual"""
        self.notifications.append({
            'title': title,
            'message': message,
            'type': 'manual'
        })

class NotificationPanel:
    def __init__(self, parent, notification_service):
        self.parent = parent
        self.notification_service = notification_service
        self.setup_ui()
    
    def setup_ui(self):
        self.btn_frame = tk.Frame(self.parent, bg='#4e73df')
        self.btn_frame.pack(side='right', padx=(0, 10))
        
        self.notif_btn = tk.Button(self.btn_frame, text="🔔", 
                                   command=self.show_notifications,
                                   bg='#4e73df', fg='white',
                                   font=('Arial', 14),
                                   relief='flat', cursor='hand2')
        self.notif_btn.pack()
        
        self.badge = None
        self.update_badge()
    
    def update_badge(self):
        count = len(self.notification_service.notifications)
        
        if self.badge:
            self.badge.destroy()
        
        if count > 0:
            self.badge = tk.Label(self.btn_frame, text=str(count), 
                                  bg='#e74a3b', fg='white',
                                  font=('Arial', 8, 'bold'),
                                  padx=3, pady=1)
            self.badge.place(x=18, y=0)
        
        self.parent.after(5000, self.update_badge)
    
    def show_notifications(self):
        dialog = tk.Toplevel(self.parent)
        dialog.title("🔔 Notificaciones")
        dialog.geometry("400x400")
        dialog.configure(bg='white')
        dialog.transient(self.parent)
        dialog.grab_set()
        
        tk.Label(dialog, text="Centro de Notificaciones", font=('Arial', 14, 'bold'),
                bg='white', fg='#4e73df').pack(pady=15)
        
        frame = tk.Frame(dialog, bg='white')
        frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        canvas = tk.Canvas(frame, bg='white', highlightthickness=0)
        scrollbar = ttk.Scrollbar(frame, orient='vertical', command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg='white')
        
        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        if not self.notification_service.notifications:
            tk.Label(scrollable_frame, text="📭 No hay notificaciones", 
                    font=('Arial', 12), bg='white', fg='#999'
                   ).pack(pady=50)
        else:
            for notif in self.notification_service.notifications:
                card = tk.Frame(scrollable_frame, bg='#f8f9fa', padx=10, pady=10,
                               highlightthickness=1, highlightbackground='#e0e0e0')
                card.pack(fill='x', pady=5)
                
                tk.Label(card, text=notif['title'], font=('Arial', 10, 'bold'),
                        bg='#f8f9fa', fg='#e74a3b').pack(anchor='w')
                
                tk.Label(card, text=notif['message'], font=('Arial', 9),
                        bg='#f8f9fa', fg='#666', wraplength=350
                       ).pack(anchor='w', pady=(5, 0))
        
        def clear_and_close():
            self.notification_service.clear_notifications()
            self.update_badge()
            dialog.destroy()
        
        btn_frame = tk.Frame(dialog, bg='white')
        btn_frame.pack(fill='x', padx=10, pady=10)
        
        tk.Button(btn_frame, text="🗑️ Limpiar todo", command=clear_and_close,
                 bg='#6c757d', fg='white', relief='flat', padx=15, pady=5
                ).pack(side='left', padx=5)
        
        tk.Button(btn_frame, text="Cerrar", command=dialog.destroy,
                 bg='#4e73df', fg='white', relief='flat', padx=15, pady=5
                ).pack(side='right', padx=5)
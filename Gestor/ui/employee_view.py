import tkinter as tk
from tkinter import ttk, messagebox

class EmployeeView:
    def __init__(self, parent, auth_service, task_service, mode='taller'):
        self.parent = parent
        self.auth_service = auth_service
        self.task_service = task_service
        self.current_user = auth_service.get_current_user()
        self.mode = mode
        self.selected_task_id = None

        self.setup_ui()
        self.load_tasks()
        if self.mode == 'taller':
            self.load_reports()
    
    def setup_ui(self):
        header = tk.Frame(self.parent, bg='#4e73df', height=80)
        header.pack(fill='x')
        header.pack_propagate(False)

        logo_frame = tk.Frame(header, bg='#4e73df')
        logo_frame.pack(side='left', padx=25, pady=15)

        tk.Label(logo_frame, text="⚡", font=('Arial', 28, 'bold'),
                fg='white', bg='#4e73df').pack(side='left', padx=(0, 10))
        tk.Label(logo_frame, text="BR CORP", font=('Arial', 20, 'bold'),
                fg='white', bg='#4e73df').pack(side='left')
        tk.Label(logo_frame, text=f"Panel de Taller • {self.current_user['full_name']}",
                font=('Arial', 10), fg='#e0e0e0', bg='#4e73df').pack(side='left', padx=(15, 0))

        btn_frame = tk.Frame(header, bg='#4e73df')
        btn_frame.pack(side='right', padx=20)

        tk.Button(btn_frame, text="🚪 CERRAR SESIÓN", command=self.logout,
                 bg='white', fg='#ef4444', font=('Arial', 10, 'bold'),
                 relief='flat', cursor='hand2', padx=20, pady=8).pack(side='right', padx=5)

        self.notebook = ttk.Notebook(self.parent, style='TNotebook')
        self.notebook.pack(fill='both', expand=True, padx=15, pady=15)

        style = ttk.Style()
        style.theme_use('clam')
        style.configure('TNotebook', background='#0f172a', borderwidth=0)
        style.configure('TNotebook.Tab', background='#1e293b', foreground='white',
                       padding=[15, 5], font=('Arial', 10, 'bold'))
        style.map('TNotebook.Tab', background=[('selected', '#4e73df')],
                  foreground=[('selected', 'white')])

        self.orders_tab = tk.Frame(self.notebook, bg='#f8fafc')
        self.notebook.add(self.orders_tab, text="📋 ÓRDENES")

        toolbar = tk.Frame(self.orders_tab, bg='#f8fafc', height=52)
        toolbar.pack(fill='x', padx=20, pady=(14, 10))
        toolbar.pack_propagate(False)

        tk.Label(toolbar, text="📋 MIS ÓRDENES DE TRABAJO", font=('Arial', 14, 'bold'),
                bg='#f8fafc', fg='#312e81').pack(side='left')

        toolbar_buttons = tk.Frame(toolbar, bg='#f8fafc')
        toolbar_buttons.pack(side='right')
        self.edit_priority_btn = tk.Button(toolbar_buttons, text="✏️ Editar prioridad",
                                           state='disabled', command=self.toggle_priority_editor,
                                           bg='#f59e0b', fg='white', relief='flat', cursor='hand2',
                                           padx=12, pady=6, font=('Arial', 9, 'bold'))
        self.edit_priority_btn.pack(side='right')

        frame = tk.Frame(self.orders_tab, bg='white', highlightthickness=1, highlightbackground='#e2e8f0')
        frame.pack(fill='both', expand=True, padx=20, pady=(0, 20))

        columns = ('ID', 'Número de orden', 'Prioridad', 'Estado', 'Progreso', 'Acciones')
        self.tree = ttk.Treeview(frame, columns=columns, show='headings', height=18)

        col_widths = {'ID': 50, 'Número de orden': 250, 'Prioridad': 100, 'Estado': 120, 'Progreso': 100, 'Acciones': 100}
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=col_widths.get(col, 100))

        scrollbar = ttk.Scrollbar(frame, orient='vertical', command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')

        self.tree.bind('<ButtonRelease-1>', self.on_click)
        self.tree.bind('<<TreeviewSelect>>', self.on_select)

        self.details_frame = tk.Frame(self.orders_tab, bg='#f8fafc')
        self.details_frame.pack(fill='x', padx=20, pady=(0, 10))
        self.selected_task_label = tk.Label(self.details_frame, text="Selecciona una tarea para ver opciones de prioridad.",
                                            bg='#f8fafc', fg='#334155', font=('Arial', 10))
        self.selected_task_label.pack(side='left', padx=(0, 10))

        self.priority_editor = tk.Frame(self.orders_tab, bg='white', bd=1, relief='solid', highlightthickness=1, highlightbackground='#cbd5e1')
        self.priority_editor_visible = False
        self.priority_var = tk.StringVar(value='medium')
        self.priority_description = tk.Label(self.priority_editor, text="", bg='white', fg='#334155',
                                             font=('Arial', 10), anchor='w')
        self.priority_description.pack(fill='x', padx=10, pady=(10, 5))

        radio_texts = [
            ('critical', '🔴 CRÍTICA'),
            ('urgent', '🟠 URGENTE'),
            ('high', '🟡 ALTA'),
            ('medium', '🟢 MEDIA'),
            ('low', '🔵 BAJA')
        ]
        radio_frame = tk.Frame(self.priority_editor, bg='white')
        radio_frame.pack(fill='x', padx=10)
        for value, text in radio_texts:
            tk.Radiobutton(radio_frame, text=text, variable=self.priority_var, value=value,
                           bg='white', anchor='w', padx=5, fg='#1f2937').pack(side='left', padx=5, pady=5)

        btn_frame = tk.Frame(self.priority_editor, bg='white')
        btn_frame.pack(fill='x', padx=10, pady=(0, 10))
        tk.Button(btn_frame, text="💾 Guardar prioridad", command=self.save_priority,
                  bg='#4f46e5', fg='white', relief='flat', cursor='hand2', font=('Arial', 9, 'bold')).pack(side='left', padx=(0, 8))
        tk.Button(btn_frame, text="❌ Cancelar", command=self.hide_priority_editor,
                  bg='#e2e8f0', fg='#334155', relief='flat', cursor='hand2', font=('Arial', 9, 'bold')).pack(side='right')

        if self.mode == 'taller':
            self.reports_tab = tk.Frame(self.notebook, bg='#f8fafc')
            self.notebook.add(self.reports_tab, text="📊 REPORTES")
            self.setup_reports_tab()

        self.status_bar = tk.Label(self.parent, text="Listo", bg='#e2e8f0', fg='#475569',
                                   font=('Arial', 9), anchor='w')
        self.status_bar.pack(side='bottom', fill='x')

    def setup_reports_tab(self):
        tk.Label(self.reports_tab, text="📊 RESUMEN DEL TALLER", font=('Arial', 16, 'bold'),
                 bg='#f8fafc', fg='#312e81').pack(anchor='w', padx=20, pady=(20, 10))
        self.report_text = tk.Text(self.reports_tab, height=18, bg='#f8fafc', relief='flat', padx=14, pady=12, fg='#1f2937')
        self.report_text.pack(fill='both', expand=True, padx=20, pady=(0, 20))
        self.report_text.config(state='disabled')

    def load_reports(self):
        if self.mode != 'taller':
            return
        tasks = self.task_service.get_user_tasks(self.current_user['id'])
        status_counts = {
            'pending': 0,
            'design': 0,
            'machine': 0,
            'cleaning': 0,
            'transit': 0,
            'completed': 0,
        }
        for task in tasks:
            status_counts[task.get('status', 'pending')] = status_counts.get(task.get('status', 'pending'), 0) + 1

        total = len(tasks)
        report = (
            f"Resumen del taller\n"
            f"Usuario: {self.current_user['full_name']}\n\n"
            f"Total de órdenes: {total}\n"
            f"Pendientes: {status_counts['pending']}\n"
            f"En diseño: {status_counts['design']}\n"
            f"En máquina: {status_counts['machine']}\n"
            f"En limpieza: {status_counts['cleaning']}\n"
            f"En tránsito: {status_counts['transit']}\n"
            f"Listas: {status_counts['completed']}\n\n"
            f"Últimas órdenes:\n"
        )
        for task in tasks[:5]:
            report += f"- #{task['id']} | {task['title']} | {task.get('status', 'pending')}\n"
        self.report_text.config(state='normal')
        self.report_text.delete('1.0', tk.END)
        self.report_text.insert('1.0', report)
        self.report_text.config(state='disabled')
    
    def build_progress_bar(self, progress, width=12):
        """Devuelve una barra visual de progreso."""
        progress = max(0, min(100, float(progress)))
        filled = int(round((progress / 100) * width))
        bar = '█' * filled + '░' * (width - filled)
        return f"{bar} {progress:.0f}%"

    def load_tasks(self):
        self.hide_priority_editor()
        self.selected_task_id = None
        self.selected_task_label.config(text="Selecciona una tarea para ver opciones de prioridad.")
        self.edit_priority_btn.config(state='disabled')
        
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        tasks = self.task_service.get_user_tasks(self.current_user['id'])
        
        priority_display = {
            'critical': '🔴 CRÍTICA',
            'urgent': '🟠 URGENTE',
            'high': '🟡 ALTA',
            'medium': '🟢 MEDIA',
            'low': '🔵 BAJA'
        }
        
        status_display = {
            'pending': '⏳ Pendiente',
            'design': '🎨 En diseño',
            'machine': '⚙️ En máquina',
            'cleaning': '🧼 En limpieza',
            'transit': '🚚 En tránsito',
            'completed': '✅ Lista',
            'in_progress': '⚙️ En progreso',
            'review': '🔍 En revisión'
        }

        action_display = {
            'pending': '▶ Orden en diseño',
            'design': '▶ Orden en máquina',
            'machine': '▶ Orden en limpieza',
            'cleaning': '▶ Orden en tránsito',
            'transit': '▶ Orden Lista',
            'completed': '✅ Lista',
            'in_progress': '▶ Orden en diseño',
            'review': '▶ Revisar'
        }
        
        for task in tasks:
            progress = (task['actual_hours'] / task['estimated_hours'] * 100) if task['estimated_hours'] > 0 else 0
            progress_label = self.build_progress_bar(progress)
            task_status = task.get('status', 'pending')
            
            self.tree.insert('', 'end', values=(
                task['id'],
                task['title'][:50],
                priority_display.get(task['priority'], 'MEDIA'),
                status_display.get(task_status, 'Pendiente'),
                progress_label,
                action_display.get(task_status, '▶ Orden en diseño')
            ), tags=(task['priority'], task_status, task['id']))
        
        self.tree.tag_configure('critical', background='#FFE5E5')
        self.tree.tag_configure('urgent', background='#FFE0CC')
        self.tree.tag_configure('high', background='#FFF0E0')
        self.tree.tag_configure('medium', background='#FFFFE0')
        self.tree.tag_configure('low', background='#E5FFE5')
    
    def advance_task_status(self, task_id):
        task = self.task_service.get_task(task_id)
        if not task:
            return

        status_order = ['pending', 'design', 'machine', 'cleaning', 'transit', 'completed']
        current_status = task.get('status', 'pending')
        current_index = status_order.index(current_status) if current_status in status_order else 0
        next_status = status_order[min(current_index + 1, len(status_order) - 1)]

        self.task_service.update_task(task_id, status=next_status)
        self.load_tasks()

        status_labels = {
            'pending': 'Orden en diseño',
            'design': 'Orden en máquina',
            'machine': 'Orden en limpieza',
            'cleaning': 'Orden en tránsito',
            'transit': 'Orden Lista',
            'completed': 'Orden Lista'
        }
        self.status_bar.config(text=f"{status_labels.get(next_status, 'Estado actualizado')}")

    def on_click(self, event):
        region = self.tree.identify_region(event.x, event.y)
        if region == "cell":
            column = self.tree.identify_column(event.x)
            if column == '#6':  # Columna Acciones
                item = self.tree.identify_row(event.y)
                if item:
                    task_id = self.tree.item(item)['values'][0]
                    self.advance_task_status(task_id)

    def on_select(self, event):
        selection = self.tree.selection()
        if not selection:
            return
        item = selection[0]
        task_id = self.tree.item(item)['values'][0]
        task = self.task_service.get_task(task_id)
        if not task:
            return
        self.selected_task_id = task_id
        self.priority_var.set(task['priority'] or 'medium')
        priority_display = {
            'critical': '🔴 CRÍTICA',
            'urgent': '🟠 URGENTE',
            'high': '🟡 ALTA',
            'medium': '🟢 MEDIA',
            'low': '🔵 BAJA'
        }
        self.selected_task_label.config(
            text=f"Tarea seleccionada: {task['title'][:50]} | Prioridad: {priority_display.get(task['priority'], 'MEDIA')}"
        )
        self.edit_priority_btn.config(state='normal')

    def toggle_priority_editor(self):
        if self.priority_editor_visible:
            self.hide_priority_editor()
        else:
            self.show_priority_editor()

    def show_priority_editor(self):
        if not self.selected_task_id:
            return
        task = self.task_service.get_task(self.selected_task_id)
        if not task:
            return
        self.priority_var.set(task['priority'] or 'medium')
        self.priority_description.config(text="Selecciona una nueva prioridad y guarda para actualizar la orden.")
        self.priority_editor.pack(fill='x', padx=20, pady=(0, 10))
        self.priority_editor_visible = True

    def hide_priority_editor(self):
        if self.priority_editor_visible:
            self.priority_editor.pack_forget()
        self.priority_editor_visible = False

    def save_priority(self):
        if not self.selected_task_id:
            return
        new_priority = self.priority_var.get()
        task = self.task_service.get_task(self.selected_task_id)
        if not task or new_priority == task['priority']:
            self.status_bar.config(text="No hubo cambios en la prioridad.")
            return
        self.task_service.update_task(self.selected_task_id, priority=new_priority)
        self.load_tasks()
        self.status_bar.config(text=f"Prioridad actualizada a {new_priority.upper()}.")
        self.selected_task_label.config(text="Selecciona una tarea para ver opciones de prioridad.")
        self.edit_priority_btn.config(state='disabled')

    def start_task(self, task_id):
        self.advance_task_status(task_id)

    def complete_task(self, task_id):
        self.advance_task_status(task_id)
    
    def logout(self):
        if hasattr(self.parent, '_logout_to_login'):
            self.parent._logout_to_login()
        else:
            self.auth_service.logout()
            self.parent.destroy()
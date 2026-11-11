import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, timedelta
from tkcalendar import DateEntry
import hashlib
from database.connection import get_connection
from database.audit_logger import AuditLogger
from business.notification_service import NotificationService
from ui.notification_panel import NotificationPanel
from business.customer_service import CustomerService
from ui.dialogs.customer_dialog import CustomerDialog

class AdminView:
    def __init__(self, parent, auth_service, task_service, is_manager_mode=False):
        self.parent = parent
        self.auth_service = auth_service
        self.task_service = task_service
        self.current_user = auth_service.get_current_user()
        self.is_manager_mode = is_manager_mode
        self.can_manage_users = not is_manager_mode
        self.selected_task_id = None
        self.selected_user_id = None
        self.department_options = ['Producción', 'Servicio al cliente']
        self.position_options = [
            'Auxiliar de Producción',
            'Encargado de Producción',
            'Operario de Producción',
            'Auxiliar de Servicio al cliente',
            'Encargado de Servicio al cliente'
        ]
        self.role_options = [
            ('admin', 'Administrador'),
            ('manager', 'Gerente'),
            ('taller', 'Taller'),
            ('service_client', 'Servicio al cliente')
        ]
        
        # Cache para usuarios (mejora rendimiento)
        self.users_cache = None
        self.last_cache_update = None
        
        # Notificaciones
        self.notification_service = NotificationService(task_service, auth_service)
        self.notification_service.start_monitoring(self.current_user['id'])
        
        # Servicio de clientes
        self.customer_service = CustomerService()
        
        self.parent.title("BR Corp - Panel de " + ("Gerente" if self.is_manager_mode else "Administrador"))
        self.parent.geometry("1400x800")
        self.parent.configure(bg='#0f172a')
        
        # Configurar estilos
        self.setup_styles()
        self.setup_ui()
        self.load_tasks()
        self.load_users()
    
    def setup_styles(self):
        """Configura estilos visuales modernos"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Estilo para el Notebook
        style.configure('TNotebook', background='#0f172a', borderwidth=0)
        style.configure('TNotebook.Tab', background='#1e293b', foreground='white',
                       padding=[15, 5], font=('Arial', 10, 'bold'))
        style.map('TNotebook.Tab', background=[('selected', '#4e73df')],
                 foreground=[('selected', 'white')])
        
        # Estilo para Treeview
        style.configure('Treeview', background='white', foreground='#333',
                       rowheight=30, fieldbackground='white', font=('Arial', 9))
        style.configure('Treeview.Heading', background='#4e73df', foreground='white',
                       font=('Arial', 10, 'bold'), relief='flat')
        style.map('Treeview.Heading', background=[('active', '#3b5ab9')])
    
    def setup_ui(self):
        try:
            # Header con gradiente
            header = tk.Frame(self.parent, bg='#4e73df', height=80)
            header.pack(fill='x')
            header.pack_propagate(False)
            
            # Logo y título
            logo_frame = tk.Frame(header, bg='#4e73df')
            logo_frame.pack(side='left', padx=25, pady=15)
            
            tk.Label(logo_frame, text="⚡", font=('Arial', 28, 'bold'),
                    fg='white', bg='#4e73df').pack(side='left', padx=(0, 10))
            
            tk.Label(logo_frame, text="BR CORP", font=('Arial', 20, 'bold'),
                    fg='white', bg='#4e73df').pack(side='left')
            
            tk.Label(logo_frame, text=f"Bienvenido, {self.current_user['full_name']}",
                    font=('Arial', 10), fg='#e0e0e0', bg='#4e73df'
                   ).pack(side='left', padx=(15, 0))
            
            # Botones header
            btn_frame = tk.Frame(header, bg='#4e73df')
            btn_frame.pack(side='right', padx=20)
            
            # Botón con efecto hover
            logout_btn = tk.Button(btn_frame, text="🚪 CERRAR SESIÓN", command=self.logout,
                                  bg='white', fg='#e74a3b', font=('Arial', 10, 'bold'),
                                  relief='flat', cursor='hand2', padx=20, pady=8)
            logout_btn.pack(side='right', padx=5)
            
            # Efectos hover
            logout_btn.bind('<Enter>', lambda e: logout_btn.config(bg='#f8f9fa'))
            logout_btn.bind('<Leave>', lambda e: logout_btn.config(bg='white'))
            
            self.notification_panel = NotificationPanel(btn_frame, self.notification_service)
            
            # Barra de estado
            self.status_bar = tk.Label(self.parent, text="✅ Sistema listo", bg='#1e293b', fg='#94a3b8',
                                       font=('Arial', 9), anchor='w')
            
            # Notebook con pestañas
            self.notebook = ttk.Notebook(self.parent, style='TNotebook')
            self.notebook.pack(fill='both', expand=True, padx=15, pady=15)
            
            # ==================== PESTAÑA ÓRDENES ====================
            self.tasks_tab = tk.Frame(self.notebook, bg='#f8f9fa')
            self.notebook.add(self.tasks_tab, text="📋 ÓRDENES DE TRABAJO")
            self.setup_tasks_tab()
            
            if self.can_manage_users:
                # ==================== PESTAÑA USUARIOS ====================
                self.users_tab = tk.Frame(self.notebook, bg='#f8f9fa')
                self.notebook.add(self.users_tab, text="👥 USUARIOS")
                self.setup_users_tab()

            # ==================== PESTAÑA REPORTES ====================
            self.reports_tab = tk.Frame(self.notebook, bg='#f8f9fa')
            self.notebook.add(self.reports_tab, text="📊 REPORTES")
            try:
                self.setup_reports_tab()
            except ModuleNotFoundError:
                tk.Label(self.reports_tab,
                         text="Reportes no disponibles: instale matplotlib",
                         font=('Arial', 12, 'bold'), bg='#f8f9fa', fg='#6b7280').pack(pady=40)
            except Exception as e:
                tk.Label(self.reports_tab,
                         text="Error al cargar reportes",
                         font=('Arial', 12, 'bold'), bg='#f8f9fa', fg='#e74a3b').pack(pady=40)
            
            # ==================== PESTAÑA CLIENTES ====================
            self.customers_tab = tk.Frame(self.notebook, bg='#f8f9fa')
            self.notebook.add(self.customers_tab, text="👥 CLIENTES")
            self.setup_customers_tab()
            
            # ==================== PESTAÑA ÓRDENES COMPLETADAS ====================
            self.completed_tab = tk.Frame(self.notebook, bg='#f8f9fa')
            self.notebook.add(self.completed_tab, text="✅ ÓRDENES COMPLETADAS")
            self.setup_completed_tab()
            
            # Barra de estado
            self.status_bar.pack(side='bottom', fill='x')
        except Exception as e:
            print(f"Error en setup_ui: {e}")
    
    # ==================== PESTAÑA ÓRDENES ====================
    
    def setup_tasks_tab(self):
        # Panel izquierdo - Formulario
        left_panel = tk.Frame(self.tasks_tab, bg='white', padx=25, pady=25,
                              highlightthickness=1, highlightbackground='#e0e0e0')
        left_panel.pack(side='left', fill='y', padx=(0, 15))
        
        title_frame = tk.Frame(left_panel, bg='white')
        title_frame.pack(fill='x', pady=(0, 20))
        tk.Label(title_frame, text="✨ NUEVA ORDEN", font=('Arial', 14, 'bold'),
                bg='white', fg='#4e73df').pack(side='left')
        
        # Número de orden
        tk.Label(left_panel, text="📌 Número de orden *", font=('Arial', 11, 'bold'),
                bg='white', fg='#333').pack(anchor='w', pady=(0, 5))
        self.title_entry = tk.Entry(left_panel, font=('Arial', 11), 
                                   bg='#f8f9fa', relief='flat', bd=1)
        self.title_entry.pack(fill='x', pady=(0, 15), ipady=8)

        # Selección de Cliente
        tk.Label(left_panel, text="👤 Cliente", font=('Arial', 11, 'bold'),
                bg='white', fg='#333').pack(anchor='w', pady=(0, 5))

        customer_frame = tk.Frame(left_panel, bg='white')
        customer_frame.pack(fill='x', pady=(0, 15))

        self.customer_var = tk.StringVar()
        self.customer_search_values = []
        self.customer_combo = ttk.Combobox(customer_frame, textvariable=self.customer_var,
                                          state='normal', width=30)
        self.customer_combo.pack(side='left', padx=(0, 5))
        self.customer_combo.bind('<KeyRelease>', self.on_customer_search)
        self.customer_combo.bind('<<ComboboxSelected>>', self.on_customer_selected)

        tk.Button(customer_frame, text="➕ Agregar Cliente", command=self.add_customer_from_tasks,
                 bg='#4e73df', fg='white', font=('Arial', 9, 'bold'),
                 relief='flat', cursor='hand2', padx=12, pady=5
                ).pack(side='left')

        try:
            self.load_customers_to_combo()
        except Exception:
            pass
        
        # Descripción
        tk.Label(left_panel, text="📝 Descripción", font=('Arial', 11, 'bold'),
                bg='white', fg='#333').pack(anchor='w', pady=(0, 5))
        self.desc_text = tk.Text(left_panel, height=5, font=('Arial', 10),
                                bg='#f8f9fa', relief='flat', bd=1)
        self.desc_text.pack(fill='x', pady=(0, 15))
        
        # Prioridad con colores
        tk.Label(left_panel, text="🎯 Prioridad", font=('Arial', 11, 'bold'),
                bg='white', fg='#333').pack(anchor='w', pady=(0, 5))
        self.priority_var = tk.StringVar(value='medium')
        priority_frame = tk.Frame(left_panel, bg='white')
        priority_frame.pack(fill='x', pady=(0, 15))

        priorities = [
            ('🔴 CRÍTICA', 'critical', '#dc3545'),
            ('🟠 URGENTE', 'urgent', '#fd7e14'),
            ('🟡 ALTA', 'high', '#ffc107'),
            ('🟢 MEDIA', 'medium', '#20c997'),
            ('🔵 BAJA', 'low', '#0d6efd')
        ]

        for text, val, color in priorities:
            frame = tk.Frame(priority_frame, bg='white')
            frame.pack(side='left', padx=5)
            color_box = tk.Label(frame, bg=color, width=2, height=1, relief='flat')
            color_box.pack(side='left', padx=(0, 5))
            rb = tk.Radiobutton(frame, text=text, variable=self.priority_var,
                               value=val, bg='white', font=('Arial', 9),
                               selectcolor='white', activebackground='white',
                               indicatoron=1, padx=0)
            rb.pack(side='left')
        
        # Horas estimadas
        tk.Label(left_panel, text="⏱️ Horas estimadas", font=('Arial', 11, 'bold'),
                bg='white', fg='#333').pack(anchor='w', pady=(0, 5))

        hours_frame = tk.Frame(left_panel, bg='white')
        hours_frame.pack(fill='x', pady=(0, 15))

        self.hours_var = tk.DoubleVar(value=0.0)
        self.hours_value_label = tk.Label(hours_frame, text="0h 00m", font=('Arial', 11, 'bold'),
                                         bg='white', fg='#4e73df')
        self.hours_value_label.pack(anchor='w', pady=(0, 6))

        self.hours_scale = tk.Scale(hours_frame, from_=0, to=24, orient=tk.HORIZONTAL,
                                   variable=self.hours_var, length=260, resolution=0.083333,
                                   showvalue=False, bg='white', highlightthickness=0,
                                   troughcolor='#e2e8f0', activebackground='#4e73df',
                                   sliderlength=18, width=12)
        self.hours_scale.pack(fill='x', expand=True)
        self.hours_scale.bind('<ButtonRelease-1>', lambda event: self.update_hours_label())
        self.hours_scale.bind('<Motion>', lambda event: self.update_hours_label())
        self.update_hours_label()

        tk.Label(hours_frame, text="Intervalo: 5 min", font=('Arial', 9), bg='white', fg='#6b7280').pack(anchor='w', pady=(4, 0))
        
        # Fecha límite
        tk.Label(left_panel, text="📅 Fecha límite", font=('Arial', 11, 'bold'),
                bg='white', fg='#333').pack(anchor='w', pady=(0, 5))
        
        date_frame = tk.Frame(left_panel, bg='white')
        date_frame.pack(fill='x', pady=(0, 15))
        
        self.due_date_var = tk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))
        self.due_date_entry = DateEntry(date_frame, width=12, background='#4e73df',
                                       foreground='white', borderwidth=2,
                                       date_pattern='yyyy-mm-dd',
                                       mindate=datetime.now().date())
        self.due_date_entry.pack(side='left')
        
        # Botón crear
        create_btn = tk.Button(left_panel, text="✨ CREAR ORDEN", command=self.create_task,
                              bg='#1cc88a', fg='white', font=('Arial', 11, 'bold'),
                              relief='flat', cursor='hand2', padx=25, pady=12)
        create_btn.pack(fill='x', pady=(10, 0))
        create_btn.bind('<Enter>', lambda e: create_btn.config(bg='#17a673'))
        create_btn.bind('<Leave>', lambda e: create_btn.config(bg='#1cc88a'))
        
        # Panel derecho - Lista de órdenes
        right_panel = tk.Frame(self.tasks_tab, bg='white',
                              highlightthickness=1, highlightbackground='#e0e0e0')
        right_panel.pack(side='right', fill='both', expand=True)
        
        # Toolbar
        task_toolbar = tk.Frame(right_panel, bg='#f8f9fa', height=45)
        task_toolbar.pack(fill='x', padx=15, pady=10)
        task_toolbar.pack_propagate(False)
        
        tk.Label(task_toolbar, text="📋 LISTA DE ÓRDENES", font=('Arial', 12, 'bold'),
                bg='#f8f9fa', fg='#4e73df').pack(side='left')
        
        btn_container = tk.Frame(task_toolbar, bg='#f8f9fa')
        btn_container.pack(side='right')
        
        buttons = [
            ('🎯 Prioridad', self.change_priority, '#f6c23e'),
            ('👥 Asignar', self.assign_task, '#36b9cc'),
            ('📋 Backlog', self.show_backlog_inline, '#6c757d'),
            ('🗑️ Eliminar', self.delete_task, '#e74a3b')
        ]
        
        for text, cmd, color in buttons:
            btn = tk.Button(btn_container, text=text, command=cmd,
                          bg=color, fg='white', font=('Arial', 9, 'bold'),
                          relief='flat', cursor='hand2', padx=12, pady=5)
            btn.pack(side='left', padx=3)
            btn.bind('<Enter>', lambda e, b=btn, c=color: b.config(bg=self.darken_color(c)))
            btn.bind('<Leave>', lambda e, b=btn, c=color: b.config(bg=c))
        
        # Treeview
        frame = tk.Frame(right_panel, bg='white')
        frame.pack(fill='both', expand=True, padx=15, pady=(0, 10))
        
        columns = ('ID', 'Número de orden', 'Cliente', 'Creado por', 'Creado el', 'Asignado por', 'Asignado a', 'Prioridad', 'Estado', 'Progreso')
        self.tree = ttk.Treeview(frame, columns=columns, show='headings', height=18, style='Treeview')

        col_widths = {'ID': 50, 'Número de orden': 180, 'Cliente': 140, 'Creado por': 120, 
                     'Creado el': 120, 'Asignado por': 120, 'Asignado a': 120, 
                     'Prioridad': 90, 'Estado': 100, 'Progreso': 70}
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=col_widths.get(col, 100))
        
        scrollbar = ttk.Scrollbar(frame, orient='vertical', command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        self.tree.bind('<<TreeviewSelect>>', self.on_task_select)
        self.tree.bind('<Double-1>', self.on_task_double_click)

        self._tooltip = None
        self._tooltip_after_id = None
    
    def darken_color(self, color):
        colors = {'#f6c23e': '#e0a800', '#36b9cc': '#2c9faf',
                 '#6c757d': '#5a6268', '#e74a3b': '#c82333'}
        return colors.get(color, color)
    
    def on_task_double_click(self, event):
        row_id = self.tree.identify_row(event.y)
        if not row_id:
            return
        item_data = self.tree.item(row_id, 'values')
        if isinstance(item_data, dict):
            values = item_data.get('values', ())
        else:
            values = item_data or ()
        if not values:
            return
        task_id = values[0]
        task = self.task_service.get_task(task_id)
        if task:
            self.edit_task(task_id)

    def edit_task(self, task_id):
        task = self.task_service.get_task(task_id)
        if not task:
            messagebox.showwarning("Advertencia", "No se encontró la orden seleccionada")
            return

        dialog = tk.Toplevel(self.parent)
        dialog.title(f"Editar orden #{task_id}")
        dialog.geometry("650x640")
        dialog.configure(bg='white')
        dialog.transient(self.parent)
        dialog.grab_set()

        frame = tk.Frame(dialog, bg='white', padx=18, pady=18)
        frame.pack(fill='both', expand=True)

        tk.Label(frame, text=f"Editar Orden #{task_id}", font=('Arial', 14, 'bold'), bg='white', fg='#4e73df').pack(anchor='w', pady=(0, 18))

        tk.Label(frame, text="Número de orden *", bg='white', font=('Arial', 10, 'bold')).pack(anchor='w')
        title_var = tk.StringVar(value=task.get('title', ''))
        tk.Entry(frame, textvariable=title_var, width=60, font=('Arial', 10)).pack(fill='x', pady=(0, 12))

        tk.Label(frame, text="Cliente *", bg='white', font=('Arial', 10, 'bold')).pack(anchor='w')
        customers = self.customer_service.get_all_customers()
        customer_names = []
        current_customer_value = ''
        for c in customers:
            if c.get('customer_type') == 'company':
                name = c.get('company_name') or c.get('full_name') or 'Sin nombre'
                doc = c.get('company_ruc') or c.get('rnc') or c.get('tax_id') or c.get('document_number') or 'Sin documento'
            else:
                name = c.get('full_name') or 'Sin nombre'
                doc = c.get('document_id') or c.get('document_number') or c.get('cedula') or c.get('id_number') or 'Sin documento'
            entry_text = f"{name} | {doc}"
            customer_names.append(entry_text)
            if c['id'] == task.get('customer_id'):
                current_customer_value = entry_text
        customer_var = tk.StringVar(value=current_customer_value)
        ttk.Combobox(frame, textvariable=customer_var, values=customer_names, width=60, state='readonly', font=('Arial', 10)).pack(fill='x', pady=(0, 12))

        tk.Label(frame, text="Descripción", bg='white', font=('Arial', 10, 'bold')).pack(anchor='w')
        description_text = tk.Text(frame, height=5, width=60, font=('Arial', 10))
        description_text.pack(fill='x', pady=(0, 12))
        if task.get('description'):
            description_text.insert('1.0', task.get('description', ''))

        tk.Label(frame, text="Prioridad *", bg='white', font=('Arial', 10, 'bold')).pack(anchor='w')
        priority_var = tk.StringVar(value=task.get('priority', 'medium'))
        ttk.Combobox(frame, textvariable=priority_var, values=['critical', 'urgent', 'high', 'medium', 'low'], width=60, state='readonly', font=('Arial', 10)).pack(fill='x', pady=(0, 12))

        tk.Label(frame, text="Fecha de vencimiento *", bg='white', font=('Arial', 10, 'bold')).pack(anchor='w')
        due_date_entry = DateEntry(frame, width=48, background='#4e73df', foreground='white', borderwidth=2, date_pattern='yyyy-mm-dd', mindate=datetime.now().date())
        due_date_entry.pack(fill='x', pady=(0, 18))
        if task.get('due_date'):
            try:
                due_date_entry.set_date(datetime.strptime(task['due_date'], '%Y-%m-%d').date())
            except Exception:
                pass

        btn_frame = tk.Frame(frame, bg='white')
        btn_frame.pack(fill='x', pady=(10, 0))

        def save_task():
            title = title_var.get().strip()
            if not title:
                messagebox.showwarning('Validación', 'El número de orden es obligatorio')
                return

            customer_id = None
            selected_customer = customer_var.get().strip()
            if selected_customer and selected_customer != 'No se encontraron clientes':
                for c in self.customer_service.get_all_customers():
                    if c.get('customer_type') == 'company':
                        name = c.get('company_name', c.get('full_name', 'Sin nombre'))
                        doc = c.get('company_ruc') or c.get('rnc') or c.get('tax_id') or c.get('document_number') or 'Sin documento'
                    else:
                        name = c.get('full_name', 'Sin nombre')
                        doc = c.get('document_id') or c.get('document_number') or c.get('cedula') or c.get('id_number') or 'Sin documento'
                    if f"{name} | {doc}" == selected_customer:
                        customer_id = c['id']
                        break

            due_date = due_date_entry.get_date().isoformat() if due_date_entry else None
            try:
                self.task_service.validate_task_data(
                title=title,
                customer_id=customer_id,
                priority=priority_var.get(),
                due_date=due_date,
                description=description_text.get('1.0', tk.END).strip(),
            )
            except ValueError as exc:
                messagebox.showwarning('Validación', str(exc))
                return

            self.task_service.update_task(
                task_id,
                title=title,
                description=description_text.get('1.0', tk.END).strip(),
                priority=priority_var.get(),
                due_date=due_date,
                customer_id=customer_id,
            )
            messagebox.showinfo('Éxito', 'Orden actualizada correctamente')
            dialog.destroy()
            self.load_tasks()

        tk.Button(btn_frame, text='💾 Guardar cambios', command=save_task, bg='#1cc88a', fg='white', font=('Arial', 10, 'bold'), relief='flat', padx=16, pady=8).pack(side='left')
        tk.Button(btn_frame, text='❌ Cancelar', command=dialog.destroy, bg='#d1d3e2', fg='#333333', font=('Arial', 10), relief='flat', padx=16, pady=8).pack(side='right')

    def build_progress_bar(self, progress, width=12):
        """Devuelve una representación visual tipo barra de progreso."""
        progress = max(0, min(100, float(progress)))
        filled = int(round((progress / 100) * width))
        bar = '█' * filled + '░' * (width - filled)
        return f"{bar} {progress:.0f}%"

    def load_tasks(self):
        try:
            for item in self.tree.get_children():
                self.tree.delete(item)

            user_role = self.current_user.get('role') if self.current_user else None
            tasks = self.task_service.get_visible_tasks(self.current_user['id'], user_role)

            if not tasks:
                return
            
            priority_display = {'critical': '🔴 Crítica', 'urgent': '🟠 Urgente',
                               'high': '🟡 Alta', 'medium': '🟢 Media', 'low': '🔵 Baja'}
            status_display = {'pending': '⏳ Pendiente', 'design': '🎨 En diseño',
                             'machine': '⚙️ En máquina', 'cleaning': '🧼 En limpieza',
                             'transit': '🚚 En tránsito', 'completed': '✅ Lista',
                             'in_progress': '⚙️ Progreso'}
            
            for task in tasks:
                progress = 0
                
                # Obtener datos de cliente
                customer_name = 'Sin cliente'
                if task.get('customer_id'):
                    try:
                        customer = self.customer_service.get_customer(task['customer_id'])
                        if customer:
                            if customer.get('customer_type') == 'company':
                                customer_name = customer.get('company_name', customer.get('full_name', 'Sin cliente'))
                            else:
                                customer_name = customer.get('full_name', 'Sin cliente')
                    except Exception:
                        customer_name = 'Sin cliente'

                # Trazabilidad
                created_by_name = self.get_user_name(task.get('created_by')) if task.get('created_by') else 'Sistema'
                assigned_by_name = self.get_user_name(task.get('assigned_by')) if task.get('assigned_by') else 'Sin asignar'
                assigned_to_name = self.get_user_name(task.get('assigned_to')) if task.get('assigned_to') else 'Sin asignar'
                created_date = task.get('created_at', '')[:16] if task.get('created_at') else 'Sin fecha'

                progress_label = self.build_progress_bar(progress)

                self.tree.insert('', 'end', values=(
                    task['id'], task['title'][:35], customer_name,
                    created_by_name, created_date, assigned_by_name, assigned_to_name,
                    priority_display.get(task['priority'], 'Media'),
                    status_display.get(task['status'], 'Pendiente'),
                    progress_label
                ), tags=(task['priority'],))
            
            self.tree.update_idletasks()
            if hasattr(self, 'completed_tree'):
                self.load_completed_tasks()
        except Exception as e:
            print(f"Error en load_tasks: {e}")
    
    def create_task(self):
        title = self.title_entry.get().strip()
        if not title:
            messagebox.showerror("Error", "El número de orden es obligatorio")
            self.title_entry.config(bg='#FFE5E5')
            return

        customer_id = None
        customer_selection = self.customer_combo.get().strip()
        if customer_selection and customer_selection != 'No se encontraron clientes':
            for customer in self.customer_service.get_all_customers():
                if customer.get('customer_type') == 'company':
                    name = customer.get('company_name', customer.get('full_name', 'Sin nombre'))
                    doc = customer.get('company_ruc') or customer.get('rnc') or customer.get('tax_id') or customer.get('document_number') or 'Sin documento'
                else:
                    name = customer.get('full_name', 'Sin nombre')
                    doc = customer.get('document_id') or customer.get('document_number') or customer.get('cedula') or customer.get('id_number') or 'Sin documento'

                if f"{name} | {doc}" == customer_selection:
                    customer_id = customer['id']
                    break

        due_date = self.due_date_var.get() if self.due_date_var.get() else None
        if due_date:
            try:
                due_date_obj = datetime.strptime(due_date, "%Y-%m-%d")
                if due_date_obj.date() < datetime.now().date():
                    messagebox.showerror("Error", "No se puede seleccionar una fecha anterior a hoy")
                    return
            except:
                pass

        try:
            hours = float(self.hours_var.get() or 0)
        except ValueError:
            hours = 0

        try:
            self.task_service.validate_task_data(
                title=title,
                customer_id=customer_id,
                priority=self.priority_var.get(),
                due_date=due_date,
                description=self.desc_text.get("1.0", tk.END).strip(),
            )
        except ValueError as exc:
            messagebox.showwarning("Validación", str(exc))
            return

        self.task_service.create_task(
            title=title,
            description=self.desc_text.get("1.0", tk.END).strip(),
            priority=self.priority_var.get(),
            estimated_hours=hours,
            due_date=due_date,
            assigned_to=None,
            assigned_by=self.current_user['id'],
            customer_id=customer_id,
            created_by=self.current_user['id']
        )
        
        # Log de auditoría
        AuditLogger.log(self.current_user['id'], "CREAR_ORDEN", f"Título: {title}")
        
        self.title_entry.delete(0, tk.END)
        self.title_entry.config(bg='#f8f9fa')
        self.desc_text.delete("1.0", tk.END)
        self.hours_var.set(0.0)
        self.update_hours_label()
        self.due_date_var.set(datetime.now().strftime("%Y-%m-%d"))
        self.priority_var.set('medium')
        
        self.load_tasks()
        self.status_bar.config(text="✅ Orden creada correctamente", fg='#1cc88a')
        self.parent.after(3000, lambda: self.status_bar.config(text="✅ Sistema listo", fg='#94a3b8'))
    
    def update_hours_label(self):
        value = float(self.hours_var.get() or 0)
        total_minutes = int(round(value * 60))
        hours = total_minutes // 60
        minutes = total_minutes % 60
        self.hours_value_label.config(text=f"{hours}h {minutes:02d}m")

    def on_task_select(self, event):
        selection = self.tree.selection()
        if selection:
            self.selected_task_id = self.tree.item(selection[0])['values'][0]
    
    def change_priority(self):
        if not self.selected_task_id:
            messagebox.showwarning("Advertencia", "Seleccione una orden")
            return
        
        task = self.task_service.get_task(self.selected_task_id)
        
        dialog = tk.Toplevel(self.parent)
        dialog.title("Cambiar Prioridad de Orden")
        dialog.configure(bg='white')
        dialog.transient(self.parent)
        dialog.grab_set()
        dialog.resizable(False, False)
        
        tk.Label(dialog, text=f"📌 Orden", font=('Arial', 12, 'bold'),
                bg='white', fg='#4e73df').pack(pady=(15, 5))
        tk.Label(dialog, text=task['title'][:50], font=('Arial', 10),
                bg='white', fg='#666', wraplength=280).pack(pady=(0, 15))
        
        priority_var = tk.StringVar(value=task['priority'])
        priorities = [('🔴 CRÍTICA', 'critical'), ('🟠 URGENTE', 'urgent'),
                     ('🟡 ALTA', 'high'), ('🟢 MEDIA', 'medium'), ('🔵 BAJA', 'low')]
        
        for text, val in priorities:
            rb = tk.Radiobutton(dialog, text=text, variable=priority_var,
                               value=val, bg='white', font=('Arial', 11),
                               selectcolor='white', activebackground='white',
                               padx=20, pady=5)
            rb.pack(anchor='w')
        
        def save():
            old_priority = task['priority']
            new_priority = priority_var.get()
            if new_priority == old_priority:
                messagebox.showinfo("Sin cambios", "No se realizó ningún cambio en la prioridad.")
                return
            self.task_service.update_task(self.selected_task_id, priority=new_priority)
            AuditLogger.log(self.current_user['id'], "CAMBIAR_PRIORIDAD", 
                          f"Orden ID: {self.selected_task_id} | {old_priority} → {new_priority}")
            self.load_tasks()
            dialog.destroy()
            self.status_bar.config(text="✅ Prioridad actualizada")
        
        tk.Label(dialog, text="Selecciona la nueva prioridad y presiona Guardar.",
                font=('Arial', 10), bg='white', fg='#666', wraplength=280).pack(pady=(0, 10))
        
        btn_frame = tk.Frame(dialog, bg='white')
        btn_frame.pack(pady=(10, 20))
        tk.Button(btn_frame, text="💾 Guardar prioridad", command=save,
                 bg='#1cc88a', fg='white', font=('Arial', 10, 'bold'),
                 relief='flat', padx=25, pady=5).pack(side='left', padx=5)
        tk.Button(btn_frame, text="❌ Cancelar", command=dialog.destroy,
                 bg='#e74a3b', fg='white', font=('Arial', 10, 'bold'),
                 relief='flat', padx=20, pady=5).pack(side='left', padx=5)
    
    def assign_task(self):
        if not self.selected_task_id:
            messagebox.showwarning("Advertencia", "Seleccione una orden")
            return

        task = self.task_service.get_task(self.selected_task_id)
        employees = self.auth_service.get_assignable_users()

        if not employees:
            messagebox.showwarning("Advertencia", "No hay personal del taller disponible")
            return
        
        dialog = tk.Toplevel(self.parent)
        dialog.title("Asignar Orden")
        dialog.geometry("400x220")
        dialog.configure(bg='white')
        dialog.transient(self.parent)
        dialog.grab_set()
        
        tk.Label(dialog, text=f"📋 {task['title'][:50]}", font=('Arial', 11, 'bold'),
                bg='white', fg='#4e73df', wraplength=350).pack(pady=15)
        
        tk.Label(dialog, text="Seleccionar empleado:", font=('Arial', 10),
                bg='white').pack()
        
        combo = ttk.Combobox(dialog, values=[f"{e['full_name']} ({e['username']})" for e in employees],
                            state='readonly', width=35, font=('Arial', 10))
        combo.pack(pady=10)
        
        def assign():
            selected = combo.get()
            if selected:
                employee_id = None
                employee_name = None
                for e in employees:
                    if f"{e['full_name']} ({e['username']})" == selected:
                        employee_id = e['id']
                        employee_name = e['full_name']
                        break
                if employee_id:
                    self.task_service.update_task(self.selected_task_id, assigned_to=employee_id, assigned_by=self.current_user['id'])
                    AuditLogger.log(self.current_user['id'], "ASIGNAR_ORDEN", 
                                  f"Orden ID: {self.selected_task_id} | Asignado a: {employee_name}")
                    self.load_tasks()
                    dialog.destroy()
                    self.status_bar.config(text="✅ Orden asignada correctamente")
        
        tk.Button(dialog, text="Asignar", command=assign,
                 bg='#1cc88a', fg='white', font=('Arial', 10, 'bold'),
                 relief='flat', padx=25, pady=8).pack(pady=10)
    
    def show_backlog_inline(self):
        backlog = self.task_service.get_backlog_tasks()
        if not backlog:
            messagebox.showinfo("Backlog", "No hay órdenes sin asignar")
            return
        
        dialog = tk.Toplevel(self.parent)
        dialog.title("📋 Backlog - Órdenes sin asignar")
        dialog.geometry("650x450")
        dialog.configure(bg='white')
        dialog.transient(self.parent)
        dialog.grab_set()
        
        tk.Label(dialog, text="📋 Órdenes sin asignar", font=('Arial', 14, 'bold'),
                bg='white', fg='#4e73df').pack(pady=15)
        
        frame = tk.Frame(dialog, bg='white')
        frame.pack(fill='both', expand=True, padx=15, pady=10)
        
        canvas = tk.Canvas(frame, bg='white', highlightthickness=0)
        scrollbar = ttk.Scrollbar(frame, orient='vertical', command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg='white')
        
        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        for task in backlog:
            card = tk.Frame(scrollable_frame, bg='#f8f9fa', padx=15, pady=10,
                           highlightthickness=1, highlightbackground='#e0e0e0')
            card.pack(fill='x', pady=5)
            
            tk.Label(card, text=f"📌 {task['title']}", font=('Arial', 11, 'bold'),
                    bg='#f8f9fa', fg='#333').pack(anchor='w')
            
            if task.get('description'):
                tk.Label(card, text=task['description'][:80], font=('Arial', 9),
                        bg='#f8f9fa', fg='#666').pack(anchor='w', pady=(5, 0))
            
            tk.Button(card, text="👥 Asignar", command=lambda t=task: self.assign_backlog_task(t, dialog),
                     bg='#1cc88a', fg='white', font=('Arial', 9),
                     relief='flat', cursor='hand2', padx=15, pady=3
                    ).pack(side='right')
        
        tk.Button(dialog, text="Cerrar", command=dialog.destroy,
                 bg='#4e73df', fg='white', font=('Arial', 10, 'bold'),
                 relief='flat', padx=25, pady=8).pack(pady=10)
    
    def assign_backlog_task(self, task, dialog):
        employees = self.auth_service.get_assignable_users()

        if not employees:
            messagebox.showwarning("Advertencia", "No hay personal del taller disponible")
            return

        assign_dialog = tk.Toplevel(dialog)
        assign_dialog.title("Asignar orden")
        assign_dialog.geometry("350x180")
        assign_dialog.configure(bg='white')
        assign_dialog.transient(dialog)
        assign_dialog.grab_set()
        
        tk.Label(assign_dialog, text=f"Orden: {task['title'][:40]}", font=('Arial', 10),
                bg='white', wraplength=300).pack(pady=10)
        
        tk.Label(assign_dialog, text="Asignar a:", bg='white').pack()
        combo = ttk.Combobox(assign_dialog, values=[f"{e['full_name']} ({e['username']})" for e in employees],
                            state='readonly', width=30)
        combo.pack(pady=10)
        
        def assign():
            selected = combo.get()
            if selected:
                employee_id = None
                employee_name = None
                for e in employees:
                    if f"{e['full_name']} ({e['username']})" == selected:
                        employee_id = e['id']
                        employee_name = e['full_name']
                        break
                if employee_id:
                    self.task_service.update_task(task['id'], assigned_to=employee_id, assigned_by=self.current_user['id'])
                    AuditLogger.log(self.current_user['id'], "ASIGNAR_ORDEN_BACKLOG", 
                                  f"Orden ID: {task['id']} | Asignado a: {employee_name}")
                    self.load_tasks()
                    assign_dialog.destroy()
                    dialog.destroy()
                    self.status_bar.config(text="✅ Orden asignada")
        
        tk.Button(assign_dialog, text="Asignar", command=assign,
                 bg='#1cc88a', fg='white', relief='flat', padx=20, pady=5
                ).pack(pady=10)
    
    def delete_task(self):
        if not self.selected_task_id:
            messagebox.showwarning("Advertencia", "Seleccione una orden")
            return
        
        task = self.task_service.get_task(self.selected_task_id)
        
        if messagebox.askyesno("Confirmar", f"¿Eliminar la orden '{task['title']}'?\nEsta acción no se puede deshacer."):
            AuditLogger.log(self.current_user['id'], "ELIMINAR_ORDEN", 
                          f"Orden ID: {self.selected_task_id} | Título: {task['title']}")
            self.task_service.delete_task(self.selected_task_id)
            self.load_tasks()
            self.status_bar.config(text="✅ Orden eliminada")
    
    # ==================== PESTAÑA USUARIOS ====================
    
    def setup_users_tab(self):
        left_panel = tk.Frame(self.users_tab, bg='white', padx=25, pady=25,
                              highlightthickness=1, highlightbackground='#e0e0e0')
        left_panel.pack(side='left', fill='y', padx=(0, 15))
        
        tk.Label(left_panel, text="✨ NUEVO USUARIO", font=('Arial', 14, 'bold'),
                bg='white', fg='#4e73df').pack(anchor='w', pady=(0, 20))
        
        fields = [
            ("👤 Usuario *:", "username"),
            ("📝 Nombre completo *:", "full_name"),
            ("📧 Email *:", "email"),
            ("🔒 Contraseña *:", "password"),
            ("🔒 Confirmar *:", "confirm"),
            ("👔 Rol:", "role"),
            ("🏢 Departamento:", "department"),
            ("💼 Cargo:", "position")
        ]
        
        self.user_entries = {}
        for label, key in fields:
            tk.Label(left_panel, text=label, font=('Arial', 10, 'bold'),
                    bg='white', fg='#1f2937').pack(anchor='w', pady=(0, 5))

            if key == 'role':
                display_values = [label_text for _, label_text in self.role_options]
                entry = ttk.Combobox(left_panel, values=display_values, state='readonly', width=33, font=('Arial', 10))
                entry.set('Gerente')
            elif key == 'department':
                entry = ttk.Combobox(left_panel, values=self.department_options, state='normal', width=33,
                                    font=('Arial', 10))
                entry.set('Producción')
                entry.bind('<KeyRelease>', lambda e, cb=entry: self.filter_department_options(cb))
                entry.configure(justify='left')
            elif key == 'position':
                entry = ttk.Combobox(left_panel, values=self.position_options, state='normal', width=33,
                                    font=('Arial', 10))
                entry.set('Auxiliar de Producción')
                entry.bind('<KeyRelease>', lambda e, cb=entry: self.filter_position_options(cb))
                entry.configure(justify='left')
            elif key in ['password', 'confirm']:
                entry = tk.Entry(left_panel, show="•", font=('Arial', 11),
                               bg='#f8f9fa', relief='solid', bd=1, highlightthickness=1,
                               highlightbackground='#d1d5db', highlightcolor='#4f46e5')
            else:
                entry = tk.Entry(left_panel, font=('Arial', 11),
                               bg='#f8f9fa', relief='solid', bd=1, highlightthickness=1,
                               highlightbackground='#d1d5db', highlightcolor='#4f46e5')

            entry.pack(fill='x', pady=(0, 12), ipady=7)
            self.user_entries[key] = entry
        
        create_btn = tk.Button(left_panel, text="✨ CREAR USUARIO", command=self.create_user,
                              bg='#1cc88a', fg='white', font=('Arial', 11, 'bold'),
                              relief='flat', cursor='hand2', padx=25, pady=12)
        create_btn.pack(fill='x', pady=(15, 0))
        create_btn.bind('<Enter>', lambda e: create_btn.config(bg='#17a673'))
        create_btn.bind('<Leave>', lambda e: create_btn.config(bg='#1cc88a'))
        
        right_panel = tk.Frame(self.users_tab, bg='white',
                              highlightthickness=1, highlightbackground='#e0e0e0')
        right_panel.pack(side='right', fill='both', expand=True)
        
        user_toolbar = tk.Frame(right_panel, bg='#f8f9fa', height=45)
        user_toolbar.pack(fill='x', padx=15, pady=10)
        user_toolbar.pack_propagate(False)
        
        tk.Label(user_toolbar, text="👥 USUARIOS REGISTRADOS", font=('Arial', 12, 'bold'),
                bg='#f8f9fa', fg='#4e73df').pack(side='left')
        
        btn_container = tk.Frame(user_toolbar, bg='#f8f9fa')
        btn_container.pack(side='right')
        
        buttons = [
            ('✏️ Editar', self.open_edit_user_panel, '#4e73df'),
            ('🔑 Reset Password', self.reset_user_password, '#f6c23e'),
            ('🗑️ Eliminar', self.delete_user, '#e74a3b')
        ]
        
        for text, cmd, color in buttons:
            btn = tk.Button(btn_container, text=text, command=cmd,
                          bg=color, fg='white', font=('Arial', 9, 'bold'),
                          relief='flat', cursor='hand2', padx=12, pady=5)
            btn.pack(side='left', padx=3)
        
        frame = tk.Frame(right_panel, bg='white')
        frame.pack(fill='both', expand=True, padx=15, pady=(0, 10))
        
        columns = ('ID', 'Usuario', 'Nombre', 'Email', 'Rol', 'Departamento', 'Cargo', 'Estado')
        self.user_tree = ttk.Treeview(frame, columns=columns, show='headings', height=16, style='Treeview')
        
        col_widths = {'ID': 40, 'Usuario': 100, 'Nombre': 140, 'Email': 160,
                     'Rol': 100, 'Departamento': 100, 'Cargo': 100, 'Estado': 80}
        for col in columns:
            self.user_tree.heading(col, text=col)
            self.user_tree.column(col, width=col_widths.get(col, 100))
        
        scrollbar = ttk.Scrollbar(frame, orient='vertical', command=self.user_tree.yview)
        self.user_tree.configure(yscrollcommand=scrollbar.set)
        self.user_tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        self.user_tree.bind('<<TreeviewSelect>>', self.on_user_select)
    
    def load_users(self):
        try:
            for item in self.user_tree.get_children():
                self.user_tree.delete(item)
            
            users = self.auth_service.get_all_users()
            
            roles_display = {'admin': '🔴 Administrador', 'manager': '🟠 Gerente', 'taller': '🛠️ Taller', 'service_client': '💬 Servicio al cliente'}
            
            for u in users:
                estado = "✅ Activo" if u.get('is_active', True) else "❌ Inactivo"
                self.user_tree.insert('', 'end', values=(
                    u['id'], u['username'], u['full_name'][:25], u['email'][:25],
                    roles_display.get(u['role'], '⚪ Desconocido'),
                    u.get('department', '-')[:15], u.get('position', '-')[:15], estado
                ))
        except Exception as e:
            print(f"Error cargando usuarios: {e}")
    
    def on_user_select(self, event):
        selection = self.user_tree.selection()
        if selection:
            self.selected_user_id = self.user_tree.item(selection[0])['values'][0]
    
    def filter_department_options(self, combo):
        query = combo.get().strip().lower()
        if not query:
            combo.configure(values=self.department_options)
            return

        filtered = [option for option in self.department_options if query in option.lower()]
        if filtered:
            combo.configure(values=filtered)
        else:
            combo.configure(values=self.department_options)

    def filter_position_options(self, combo):
        query = combo.get().strip().lower()
        if not query:
            combo.configure(values=self.position_options)
            return

        filtered = [option for option in self.position_options if query in option.lower()]
        if filtered:
            combo.configure(values=filtered)
        else:
            combo.configure(values=self.position_options)

    def get_role_value(self, display_name):
        for value, label in self.role_options:
            if label == display_name:
                return value
        return display_name

    def create_user(self):
        username = self.user_entries['username'].get().strip()
        full_name = self.user_entries['full_name'].get().strip()
        email = self.user_entries['email'].get().strip()
        password = self.user_entries['password'].get()
        confirm = self.user_entries['confirm'].get()
        role_display = self.user_entries['role'].get()
        role = self.get_role_value(role_display)
        department = self.user_entries['department'].get().strip()
        position = self.user_entries['position'].get().strip()
        
        if not all([username, full_name, email, password]):
            messagebox.showerror("Error", "Complete los campos obligatorios (*)")
            return
        
        if password != confirm:
            messagebox.showerror("Error", "Las contraseñas no coinciden")
            return
        
        if len(password) < 6:
            messagebox.showerror("Error", "Mínimo 6 caracteres")
            return
        
        if self.auth_service.create_user(username, password, full_name, email, role, department, position):
            AuditLogger.log(self.current_user['id'], "CREAR_USUARIO", 
                          f"Usuario: {username} | Rol: {role}")
            messagebox.showinfo("Éxito", f"Usuario '{username}' creado correctamente")
            for key in ['username', 'full_name', 'email', 'password', 'confirm', 'department', 'position']:
                self.user_entries[key].delete(0, tk.END)
            self.user_entries['role'].set('taller')
            self.users_cache = None
            self.load_users()
            self.status_bar.config(text="✅ Usuario creado correctamente")
        else:
            messagebox.showerror("Error", "El usuario ya existe")
    
    def open_edit_user_panel(self):
        if not self.selected_user_id:
            messagebox.showwarning("Advertencia", "Seleccione un usuario")
            return
        
        users = self.auth_service.get_all_users()
        user = None
        for u in users:
            if u['id'] == self.selected_user_id:
                user = u
                break
        
        if not user:
            return
        
        if user['username'] == self.current_user['username']:
            messagebox.showwarning("Advertencia", "No puedes editar tu propio usuario")
            return
        
        dialog = tk.Toplevel(self.parent)
        dialog.title(f"✏️ Editar Usuario - {user['username']}")
        dialog.geometry("450x550")
        dialog.configure(bg='white')
        dialog.transient(self.parent)
        dialog.grab_set()
        
        tk.Label(dialog, text=f"✏️ EDITAR USUARIO", font=('Arial', 14, 'bold'),
                bg='white', fg='#4e73df').pack(pady=20)
        
        frame = tk.Frame(dialog, bg='white')
        frame.pack(fill='both', expand=True, padx=30, pady=10)
        
        entries = {}
        fields = [
            ("📝 Nombre completo:", "full_name", user.get('full_name', '')),
            ("📧 Email:", "email", user.get('email', '')),
            ("👔 Rol:", "role", user.get('role', 'taller')),
            ("🏢 Departamento:", "department", user.get('department', '')),
            ("💼 Cargo:", "position", user.get('position', ''))
        ]
        
        row = 0
        for label, key, value in fields:
            tk.Label(frame, text=label, font=('Arial', 10, 'bold'),
                    bg='white', fg='#333').grid(row=row, column=0, sticky='w', pady=(0, 5))
            row += 1

            if key == 'role':
                display_values = [label_text for _, label_text in self.role_options]
                entry = ttk.Combobox(frame, values=display_values, state='readonly', width=35, font=('Arial', 10))
                entry.set(next((label for val, label in self.role_options if val == value), 'Taller'))
            elif key == 'department':
                entry = ttk.Combobox(frame, values=self.department_options, state='normal', width=35,
                                    font=('Arial', 10))
                entry.set(value if value in self.department_options else 'Producción')
                entry.bind('<KeyRelease>', lambda e, cb=entry: self.filter_department_options(cb))
            elif key == 'position':
                entry = ttk.Combobox(frame, values=self.position_options, state='normal', width=35,
                                    font=('Arial', 10))
                entry.set(value if value in self.position_options else 'Auxiliar de Producción')
                entry.bind('<KeyRelease>', lambda e, cb=entry: self.filter_position_options(cb))
            else:
                entry = tk.Entry(frame, font=('Arial', 11), width=37,
                               bg='#f8f9fa', relief='flat', bd=1)
                entry.insert(0, value)
            
            entry.grid(row=row, column=0, pady=(0, 15))
            entries[key] = entry
            row += 1
        
        def save_changes():
            role_display = entries['role'].get()
            role_value = self.get_role_value(role_display)
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE users 
                SET full_name = ?, email = ?, role = ?, department = ?, position = ?
                WHERE id = ?
            """, (entries['full_name'].get().strip(), entries['email'].get().strip(),
                  role_value, entries['department'].get().strip(),
                  entries['position'].get().strip(), user['id']))
            conn.commit()
            conn.close()

            AuditLogger.log(self.current_user['id'], "EDITAR_USUARIO",
                          f"Usuario ID: {user['id']} | Nuevo rol: {role_value}")
            messagebox.showinfo("Éxito", "Usuario actualizado")
            self.users_cache = None
            self.load_users()
            dialog.destroy()
            self.status_bar.config(text="✅ Usuario actualizado")
        
        btn_frame = tk.Frame(dialog, bg='white')
        btn_frame.pack(pady=20)
        
        tk.Button(btn_frame, text="💾 GUARDAR", command=save_changes,
                 bg='#1cc88a', fg='white', font=('Arial', 10, 'bold'),
                 relief='flat', padx=25, pady=5).pack(side='left', padx=5)
        tk.Button(btn_frame, text="❌ CANCELAR", command=dialog.destroy,
                 bg='#e74a3b', fg='white', font=('Arial', 10, 'bold'),
                 relief='flat', padx=20, pady=5).pack(side='left', padx=5)
    
    def reset_user_password(self):
        if not self.selected_user_id:
            messagebox.showwarning("Advertencia", "Seleccione un usuario")
            return
        
        users = self.auth_service.get_all_users()
        user = None
        for u in users:
            if u['id'] == self.selected_user_id:
                user = u
                break
        
        if not user:
            return
        
        dialog = tk.Toplevel(self.parent)
        dialog.title(f"🔑 Resetear Contraseña - {user['username']}")
        dialog.geometry("380x280")
        dialog.configure(bg='white')
        dialog.transient(self.parent)
        dialog.grab_set()
        
        tk.Label(dialog, text=f"🔐 Resetear contraseña", font=('Arial', 14, 'bold'),
                bg='white', fg='#4e73df').pack(pady=20)
        
        tk.Label(dialog, text=f"Usuario: {user['username']}", font=('Arial', 11),
                bg='white', fg='#333').pack()
        
        tk.Label(dialog, text="Nueva contraseña:", bg='white', font=('Arial', 10)
                ).pack(pady=(15, 5))
        password_entry = tk.Entry(dialog, show="•", width=30, font=('Arial', 11),
                                 bg='#f8f9fa', relief='flat', bd=1)
        password_entry.pack(pady=5)
        
        tk.Label(dialog, text="Confirmar:", bg='white', font=('Arial', 10)
                ).pack(pady=(5, 5))
        confirm_entry = tk.Entry(dialog, show="•", width=30, font=('Arial', 11),
                                bg='#f8f9fa', relief='flat', bd=1)
        confirm_entry.pack(pady=5)
        
        def reset():
            password = password_entry.get()
            confirm = confirm_entry.get()
            
            if not password or len(password) < 6:
                messagebox.showerror("Error", "Mínimo 6 caracteres")
                return
            if password != confirm:
                messagebox.showerror("Error", "Las contraseñas no coinciden")
                return
            
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("UPDATE users SET password_hash = ? WHERE id = ?", (password_hash, user['id']))
            conn.commit()
            conn.close()
            
            AuditLogger.log(self.current_user['id'], "RESETEAR_PASSWORD", 
                          f"Usuario: {user['username']}")
            messagebox.showinfo("Éxito", "Contraseña actualizada")
            dialog.destroy()
            self.status_bar.config(text="✅ Contraseña restablecida")
        
        tk.Button(dialog, text="Resetear", command=reset,
                 bg='#f6c23e', fg='black', font=('Arial', 10, 'bold'),
                 relief='flat', padx=25, pady=8).pack(pady=20)
        tk.Button(dialog, text="Cancelar", command=dialog.destroy,
                 bg='#e74a3b', fg='white', relief='flat', padx=20, pady=5
                ).pack(pady=5)
    
    def delete_user(self):
        if not self.selected_user_id:
            messagebox.showwarning("Advertencia", "Seleccione un usuario")
            return
        
        users = self.auth_service.get_all_users()
        user = None
        for u in users:
            if u['id'] == self.selected_user_id:
                user = u
                break
        
        if not user:
            return
        
        if user['username'] == self.current_user['username']:
            messagebox.showwarning("Advertencia", "No puedes eliminar tu propio usuario")
            return
        
        if messagebox.askyesno("Confirmar", f"¿Eliminar a '{user['username']}'?\nEsta acción no se puede deshacer."):
            AuditLogger.log(self.current_user['id'], "ELIMINAR_USUARIO", 
                          f"Usuario ID: {user['id']} | Username: {user['username']}")
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("UPDATE tasks SET assigned_to = NULL WHERE assigned_to = ?", (user['id'],))
            cursor.execute("DELETE FROM users WHERE id = ?", (user['id'],))
            conn.commit()
            conn.close()
            self.users_cache = None
            self.load_users()
            self.load_tasks()
            self.status_bar.config(text="✅ Usuario eliminado")
    
    # ==================== PESTAÑA REPORTES ====================
    
    def setup_completed_tab(self):
        frame = tk.Frame(self.completed_tab, bg='white', padx=15, pady=15,
                        highlightthickness=1, highlightbackground='#e0e0e0')
        frame.pack(fill='both', expand=True)
        
        toolbar = tk.Frame(frame, bg='white', height=45)
        toolbar.pack(fill='x', pady=(0, 10))
        toolbar.pack_propagate(False)
        
        tk.Label(toolbar, text="📦 HISTORIAL DE ÓRDENES FINALIZADAS", font=('Arial', 14, 'bold'),
                bg='white', fg='#4e73df').pack(side='left')
        
        tk.Button(toolbar, text="🔄 Refrescar", command=self.load_completed_tasks,
                 bg='#1cc88a', fg='white', font=('Arial', 10, 'bold'),
                 relief='flat', cursor='hand2', padx=15, pady=5).pack(side='right')
        
        self.completed_canvas = tk.Canvas(frame, bg='white', highlightthickness=0)
        self.completed_scrollbar = ttk.Scrollbar(frame, orient='vertical', command=self.completed_canvas.yview)
        self.completed_canvas.configure(yscrollcommand=self.completed_scrollbar.set)
        self.completed_scrollbar.pack(side='right', fill='y')
        self.completed_canvas.pack(side='left', fill='both', expand=True)

        self.completed_content_frame = tk.Frame(self.completed_canvas, bg='white')
        self.completed_window_id = self.completed_canvas.create_window((0, 0), window=self.completed_content_frame, anchor='nw')
        self.completed_content_frame.bind('<Configure>', self._on_completed_content_configure)
        self.completed_canvas.bind('<Configure>', self._on_completed_canvas_configure)
        
        self.load_completed_tasks()

    def _on_completed_content_configure(self, event):
        self.completed_canvas.configure(scrollregion=self.completed_canvas.bbox('all'))

    def _on_completed_canvas_configure(self, event):
        self.completed_canvas.itemconfig(self.completed_window_id, width=event.width)

    def _parse_completed_date(self, value):
        if not value:
            return None
        value = str(value).strip()
        for fmt in ('%Y-%m-%d %H:%M:%S', '%Y-%m-%d', '%Y-%m-%dT%H:%M:%S', '%Y-%m-%dT%H:%M:%S.%f'):
            try:
                return datetime.strptime(value, fmt)
            except ValueError:
                continue
        return None

    def _get_completed_tasks_grouped(self, tasks):
        month_names = {
            'January': 'Enero', 'February': 'Febrero', 'March': 'Marzo', 'April': 'Abril',
            'May': 'Mayo', 'June': 'Junio', 'July': 'Julio', 'August': 'Agosto',
            'September': 'Septiembre', 'October': 'Octubre', 'November': 'Noviembre', 'December': 'Diciembre'
        }
        grouped = {}
        for task in tasks:
            completed_at = task.get('updated_at') or task.get('created_at') or ''
            parsed_date = self._parse_completed_date(completed_at)
            if parsed_date:
                year_key = str(parsed_date.year)
                month_key = month_names.get(parsed_date.strftime('%B'), parsed_date.strftime('%B'))
                day_key = str(parsed_date.day).zfill(2)
            else:
                year_key = 'Sin fecha'
                month_key = 'Sin fecha'
                day_key = 'Sin fecha'

            grouped.setdefault(year_key, {}).setdefault(month_key, {}).setdefault(day_key, []).append(task)
        return grouped

    def _get_completed_task_summary(self, task):
        customer_name = 'Sin cliente'
        if task.get('customer_id'):
            try:
                customer = self.customer_service.get_customer(task['customer_id'])
                if customer:
                    if customer.get('customer_type') == 'company':
                        customer_name = customer.get('company_name', customer.get('full_name', 'Sin cliente'))
                    else:
                        customer_name = customer.get('full_name', 'Sin cliente')
            except Exception:
                customer_name = 'Sin cliente'

        created_by_name = self.get_user_name(task.get('created_by')) if task.get('created_by') else 'Sistema'
        assigned_to_name = self.get_user_name(task.get('assigned_to')) if task.get('assigned_to') else 'Sin asignar'
        priority_display = {'critical': '🔴 Crítica', 'urgent': '🟠 Urgente',
                            'high': '🟡 Alta', 'medium': '🟢 Media', 'low': '🔵 Baja'}
        return customer_name, created_by_name, assigned_to_name, priority_display.get(task.get('priority'), '🟢 Media')

    def load_completed_tasks(self):
        try:
            for widget in self.completed_content_frame.winfo_children():
                widget.destroy()

            tasks = self.task_service.get_completed_tasks()
            if not tasks:
                tk.Label(self.completed_content_frame, text="No hay órdenes finalizadas aún.",
                         bg='white', fg='#6c757d', font=('Arial', 11)).pack(anchor='w', pady=10)
                return

            grouped = self._get_completed_tasks_grouped(tasks)
            tk.Label(self.completed_content_frame,
                     text="📅 Las órdenes se organizan por año, mes y día como un historial de carpetas.",
                     bg='white', fg='#4e73df', font=('Arial', 10, 'bold')).pack(anchor='w', pady=(0, 10))

            years = sorted(grouped.keys(), key=lambda y: (y == 'Sin fecha', 0 if y == 'Sin fecha' else int(y) * -1), reverse=False)
            years = [year for year in years if year != 'Sin fecha'] + (['Sin fecha'] if 'Sin fecha' in grouped else [])

            for year in years:
                year_frame = tk.Frame(self.completed_content_frame, bg='white', bd=1, relief='solid')
                year_frame.pack(fill='x', pady=(0, 10))

                year_count = sum(len(day_tasks) for month_dict in grouped[year].values() for day_tasks in month_dict.values())
                year_header = tk.Frame(year_frame, bg='#e9ecef')
                year_header.pack(fill='x', padx=5, pady=5)
                year_toggle = tk.Button(year_header, text='▶', width=2, bg='#e9ecef', fg='#4e73df', bd=0,
                                        font=('Arial', 10, 'bold'), cursor='hand2')
                year_toggle.pack(side='left')
                tk.Label(year_header, text=f"📁 {year} — {year_count} orden(es)", bg='#e9ecef', fg='#2d3748',
                         font=('Arial', 10, 'bold')).pack(side='left', padx=(8, 0))

                year_body = tk.Frame(year_frame, bg='white')
                def toggle_year(body=year_body, btn=year_toggle):
                    if body.winfo_ismapped():
                        body.pack_forget()
                        btn.config(text='▶')
                    else:
                        body.pack(fill='x', padx=8, pady=(0, 8))
                        btn.config(text='▼')
                year_toggle.config(command=toggle_year)

                months = grouped[year]
                month_names = sorted(months.keys(), key=lambda m: (m == 'Sin fecha', 0 if m == 'Sin fecha' else -self._month_order(m)))
                for month in month_names:
                    month_container = tk.Frame(year_body, bg='white', bd=1, relief='solid')
                    month_container.pack(fill='x', pady=(0, 8))

                    month_header = tk.Frame(month_container, bg='#f8fafc')
                    month_header.pack(fill='x', padx=5, pady=5)
                    month_toggle = tk.Button(month_header, text='▶', width=2, bg='#f8fafc', fg='#4e73df', bd=0,
                                             font=('Arial', 9, 'bold'), cursor='hand2')
                    month_toggle.pack(side='left')
                    month_count = sum(len(day_tasks) for day_tasks in months[month].values())
                    tk.Label(month_header, text=f"🗂️ {month} — {month_count} orden(es)", bg='#f8fafc', fg='#2d3748',
                             font=('Arial', 9, 'bold')).pack(side='left', padx=(8, 0))

                    month_body = tk.Frame(month_container, bg='white')
                    def toggle_month(body=month_body, btn=month_toggle):
                        if body.winfo_ismapped():
                            body.pack_forget()
                            btn.config(text='▶')
                        else:
                            body.pack(fill='x', padx=10, pady=(0, 8))
                            btn.config(text='▼')
                    month_toggle.config(command=toggle_month)

                    days = months[month]
                    for day in sorted(days.keys(), key=lambda d: (d == 'Sin fecha', 0 if d == 'Sin fecha' else -int(d))):
                        day_container = tk.Frame(month_body, bg='#f1f3f5', bd=1, relief='solid')
                        day_container.pack(fill='x', pady=(0, 6))

                        day_header = tk.Frame(day_container, bg='#f1f3f5')
                        day_header.pack(fill='x', padx=5, pady=5)
                        day_toggle = tk.Button(day_header, text='▶', width=2, bg='#f1f3f5', fg='#4e73df', bd=0,
                                               font=('Arial', 9, 'bold'), cursor='hand2')
                        day_toggle.pack(side='left')
                        day_count = len(days[day])
                        tk.Label(day_header, text=f"📅 Día {day} — {day_count} orden(es)", bg='#f1f3f5', fg='#495057',
                                 font=('Arial', 9, 'bold')).pack(side='left', padx=(8, 0))

                        day_body = tk.Frame(day_container, bg='white')
                        def toggle_day(body=day_body, btn=day_toggle):
                            if body.winfo_ismapped():
                                body.pack_forget()
                                btn.config(text='▶')
                            else:
                                body.pack(fill='x', padx=10, pady=(0, 8))
                                btn.config(text='▼')
                        day_toggle.config(command=toggle_day)

                        for task in days[day]:
                            customer_name, created_by_name, assigned_to_name, priority_display = self._get_completed_task_summary(task)
                            task_frame = tk.Frame(day_body, bg='#fdfdfd', padx=8, pady=6,
                                                  highlightthickness=1, highlightbackground='#f1f3f5')
                            task_frame.pack(fill='x', pady=(0, 4))
                            tk.Label(task_frame, text=f"#{task['id']} • {task.get('title', 'Sin título')[:55]}",
                                     bg='#fdfdfd', fg='#212529', font=('Arial', 9, 'bold'), anchor='w').pack(anchor='w')
                            tk.Label(task_frame, text=f"Cliente: {customer_name} | Responsable: {assigned_to_name} | Prioridad: {priority_display}",
                                     bg='#fdfdfd', fg='#6c757d', font=('Arial', 8), anchor='w').pack(anchor='w', pady=(2, 0))
                            tk.Label(task_frame, text=f"Creado por: {created_by_name}",
                                     bg='#fdfdfd', fg='#6c757d', font=('Arial', 8), anchor='w').pack(anchor='w')
        except Exception as e:
            print(f"Error en load_completed_tasks: {e}")

    def _toggle_section(self, body, button):
        if body.winfo_ismapped():
            body.pack_forget()
            button.config(text='▶')
        else:
            body.pack(fill='x', padx=10, pady=(0, 8))
            button.config(text='▼')

    def _month_order(self, month_name):
        order = {
            'Enero': 1, 'Febrero': 2, 'Marzo': 3, 'Abril': 4, 'Mayo': 5, 'Junio': 6,
            'Julio': 7, 'Agosto': 8, 'Septiembre': 9, 'Octubre': 10, 'Noviembre': 11, 'Diciembre': 12,
            'Sin fecha': 13
        }
        return order.get(month_name, 99)

    def setup_reports_tab(self):
        import matplotlib.pyplot as plt
        from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

        self.reports_frame = tk.Frame(self.reports_tab, bg='white', padx=25, pady=25)
        self.reports_frame.pack(fill='both', expand=True)

        tk.Label(self.reports_frame, text="📊 REPORTES Y ESTADÍSTICAS", font=('Arial', 16, 'bold'),
                bg='white', fg='#4e73df').pack(anchor='w', pady=(0, 25))

        self.figure = plt.Figure(figsize=(10, 5), dpi=100)
        self.ax = self.figure.add_subplot(111)
        self.ax.set_title('Distribución de órdenes por prioridad')
        self.ax.set_xlabel('Prioridad')
        self.ax.set_ylabel('Cantidad')
        self.ax.grid(axis='y', linestyle='--', alpha=0.3)

        self.canvas = FigureCanvasTkAgg(self.figure, master=self.reports_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill='both', expand=True)

        self.update_reports()
    
    def update_reports(self):
        try:
            import matplotlib.pyplot as plt
            user_role = self.current_user.get('role') if self.current_user else None
            tasks = self.task_service.get_visible_tasks(self.current_user['id'], user_role)
            priority_categories = ['critical', 'urgent', 'high', 'medium', 'low']
            priority_labels = ['Crítica', 'Urgente', 'Alta', 'Media', 'Baja']
            priority_colors = ['#dc3545', '#fd7e14', '#ffc107', '#20c997', '#0d6efd']

            counts = [sum(1 for t in tasks if t.get('priority') == p) for p in priority_categories]

            self.ax.clear()
            self.ax.bar(priority_labels, counts, color=priority_colors)
            self.ax.set_title('Distribución de órdenes por prioridad')
            self.ax.set_xlabel('Prioridad')
            self.ax.set_ylabel('Cantidad de órdenes')
            self.ax.set_ylim(0, max(counts + [1]) * 1.2)
            self.ax.grid(axis='y', linestyle='--', alpha=0.3)

            for i, value in enumerate(counts):
                self.ax.text(i, value + 0.1, str(value), ha='center', va='bottom', fontweight='bold')

            self.canvas.draw()
            if hasattr(self, 'status_bar'):
                self.status_bar.config(text="✅ Reportes actualizados")
                self.parent.after(3000, lambda: self.status_bar.config(text="✅ Sistema listo"))
        except Exception as e:
            print(f"Error actualizando reportes: {e}")
    
    # ==================== PESTAÑA CLIENTES ====================
    
    def setup_customers_tab(self):
        frame = tk.Frame(self.customers_tab, bg='white', padx=15, pady=15,
                        highlightthickness=1, highlightbackground='#e0e0e0')
        frame.pack(fill='both', expand=True)
        
        toolbar = tk.Frame(frame, bg='white', height=45)
        toolbar.pack(fill='x', pady=(0, 10))
        toolbar.pack_propagate(False)
        
        tk.Label(toolbar, text="👥 LISTA DE CLIENTES", font=('Arial', 12, 'bold'),
                bg='white', fg='#4e73df').pack(side='left')
        
        tk.Button(toolbar, text="🔄 Refrescar", command=self._reload_customer_lists,
                 bg='#f59e0b', fg='white', font=('Arial', 10, 'bold'),
                 relief='flat', cursor='hand2', padx=12, pady=5
                ).pack(side='right', padx=5)

        tk.Button(toolbar, text="➕ Agregar Cliente", command=self.add_customer,
                 bg='#1cc88a', fg='white', font=('Arial', 10, 'bold'),
                 relief='flat', cursor='hand2', padx=15, pady=5
                ).pack(side='right', padx=5)
        
        search_frame = tk.Frame(frame, bg='white')
        search_frame.pack(fill='x', pady=(0, 10))
        
        tk.Label(search_frame, text="🔍 Buscar:", font=('Arial', 10), bg='white'
                ).pack(side='left', padx=(0, 5))
        
        self.search_entry = tk.Entry(search_frame, font=('Arial', 10), width=30)
        self.search_entry.pack(side='left', padx=(0, 5))
        
        tk.Button(search_frame, text="Buscar", command=self.search_customers,
                 bg='#4e73df', fg='white', font=('Arial', 9), relief='flat', padx=10
                ).pack(side='left')
        
        toggle_frame = tk.Frame(frame, bg='white')
        toggle_frame.pack(fill='x', pady=(0, 10))

        self.customer_view_var = tk.StringVar(value='individual')
        self.customer_toggle_buttons = {}

        for value, label in [('individual', '👤 Personas'), ('company', '🏢 Empresas')]:
            btn = tk.Button(
                toggle_frame,
                text=label,
                command=lambda v=value: self._show_customer_view(v),
                bg='#e5e7eb',
                fg='#1f2937',
                font=('Arial', 10, 'bold'),
                relief='flat',
                padx=15,
                pady=6,
                cursor='hand2'
            )
            btn.pack(side='left', padx=(0, 8))
            self.customer_toggle_buttons[value] = btn

        tables_frame = tk.Frame(frame, bg='white')
        tables_frame.pack(fill='both', expand=True)

        self.person_customer_container = tk.Frame(tables_frame, bg='white')
        self.company_customer_container = tk.Frame(tables_frame, bg='white')

        person_frame = tk.Frame(self.person_customer_container, bg='white')
        person_frame.pack(fill='both', expand=True)
        tk.Label(person_frame, text='👤 PERSONAS', font=('Arial', 11, 'bold'), bg='white', fg='#4e73df').pack(anchor='w', pady=(0, 8))
        person_cols = ('ID', 'Nombre', 'Documento', 'Teléfono', 'Email', 'Ciudad')
        self.customer_tree = ttk.Treeview(person_frame, columns=person_cols, show='headings', height=15)
        person_widths = {'ID': 40, 'Nombre': 180, 'Documento': 110, 'Teléfono': 100, 'Email': 150, 'Ciudad': 100}
        for col in person_cols:
            self.customer_tree.heading(col, text=col)
            self.customer_tree.column(col, width=person_widths.get(col, 100), anchor='center')
        person_scroll = ttk.Scrollbar(person_frame, orient='vertical', command=self.customer_tree.yview)
        self.customer_tree.configure(yscrollcommand=person_scroll.set)
        self.customer_tree.pack(side='left', fill='both', expand=True)
        person_scroll.pack(side='right', fill='y')
        self.customer_tree.bind('<Double-1>', self.edit_customer)

        company_frame = tk.Frame(self.company_customer_container, bg='white')
        company_frame.pack(fill='both', expand=True)
        tk.Label(company_frame, text='🏢 EMPRESAS', font=('Arial', 11, 'bold'), bg='white', fg='#4e73df').pack(anchor='w', pady=(0, 8))
        company_cols = ('ID', 'Empresa', 'RNC', 'Teléfono', 'Email', 'Ciudad')
        self.company_customer_tree = ttk.Treeview(company_frame, columns=company_cols, show='headings', height=15)
        company_widths = {'ID': 40, 'Empresa': 180, 'RNC': 110, 'Teléfono': 100, 'Email': 150, 'Ciudad': 100}
        for col in company_cols:
            self.company_customer_tree.heading(col, text=col)
            self.company_customer_tree.column(col, width=company_widths.get(col, 100), anchor='center')
        company_scroll = ttk.Scrollbar(company_frame, orient='vertical', command=self.company_customer_tree.yview)
        self.company_customer_tree.configure(yscrollcommand=company_scroll.set)
        self.company_customer_tree.pack(side='left', fill='both', expand=True)
        company_scroll.pack(side='right', fill='y')
        self.company_customer_tree.bind('<Double-1>', self.edit_customer)

        self._show_customer_view('individual')

        btn_frame = tk.Frame(frame, bg='white')
        btn_frame.pack(fill='x', pady=(10, 0))
        
        tk.Button(btn_frame, text="✏️ Editar", command=self.edit_customer,
                 bg='#4e73df', fg='white', relief='flat', padx=15, pady=5
                ).pack(side='left', padx=5)
        
        tk.Button(btn_frame, text="🗑️ Eliminar", command=self.delete_customer,
                 bg='#e74a3b', fg='white', relief='flat', padx=15, pady=5
                ).pack(side='left', padx=5)
        
        self.load_customers()
    
    def _show_customer_view(self, view_type):
        self.customer_view_var.set(view_type)
        for key, button in self.customer_toggle_buttons.items():
            button.config(bg='#e5e7eb' if key != view_type else '#4e73df', fg='white' if key == view_type else '#1f2937')

        if view_type == 'company':
            self.person_customer_container.pack_forget()
            self.company_customer_container.pack(side='left', fill='both', expand=True)
        else:
            self.company_customer_container.pack_forget()
            self.person_customer_container.pack(side='left', fill='both', expand=True)

    def _reload_customer_lists(self):
        current_view = self.customer_view_var.get() if hasattr(self, 'customer_view_var') else 'individual'
        if hasattr(self, 'search_entry') and self.search_entry:
            term = self.search_entry.get().strip()
            self.load_customers(term if term else None)
        else:
            self.load_customers()
        self._show_customer_view(current_view)
        self._focus_latest_customer_in_active_view()

    def _focus_latest_customer_in_active_view(self):
        try:
            tree = self.company_customer_tree if self.customer_view_var.get() == 'company' else self.customer_tree
            if not tree or not tree.get_children():
                return
            latest_item = None
            latest_id = -1
            for item in tree.get_children():
                values = tree.item(item, 'values')
                if not values:
                    continue
                try:
                    current_id = int(values[0])
                except (TypeError, ValueError):
                    continue
                if current_id > latest_id:
                    latest_id = current_id
                    latest_item = item
            if latest_item:
                tree.selection_set(latest_item)
                tree.focus(latest_item)
                tree.see(latest_item)
        except Exception:
            pass

    def _safe_customer_text(self, value, fallback='-'):
        if value is None:
            return fallback
        text = str(value).strip()
        return text if text else fallback

    def load_customers(self, search_term=None):
        for tree in [self.customer_tree, self.company_customer_tree]:
            for item in tree.get_children():
                tree.delete(item)

        if search_term:
            customers = self.customer_service.search_customers(search_term)
        else:
            customers = self.customer_service.get_all_customers()

        for c in customers:
            if c.get('customer_type') == 'company':
                display_name = self._safe_customer_text(c.get('company_name') or c.get('full_name'), 'Sin nombre')
                display_doc = self._safe_customer_text(c.get('document_id') or c.get('company_ruc') or c.get('tax_id') or '-', '-')
                email = self._safe_customer_text(c.get('email'), '-')
                phone = self._safe_customer_text(c.get('company_phone') or c.get('phone'), '-')
                city = self._safe_customer_text(c.get('city'), '-')
                self.company_customer_tree.insert('', 'end', values=(
                    c['id'], display_name[:30], display_doc[:15],
                    phone[:15], email[:25], city[:20]
                ))
            else:
                display_name = self._safe_customer_text(c.get('full_name'), 'Sin nombre')
                display_doc = self._safe_customer_text(c.get('document_id'), '-')
                email = self._safe_customer_text(c.get('email'), '-')
                phone = self._safe_customer_text(c.get('phone'), '-')
                city = self._safe_customer_text(c.get('city'), '-')
                self.customer_tree.insert('', 'end', values=(
                    c['id'], display_name[:30], display_doc[:15],
                    phone[:15], email[:25], city[:20]
                ))

        if not search_term:
            self._focus_latest_customer_in_active_view()

    def search_customers(self):
        term = self.search_entry.get().strip()
        self.load_customers(term if term else None)
    
    def add_customer(self):
        if hasattr(self, 'search_entry'):
            self.search_entry.delete(0, tk.END)
        CustomerDialog(self.parent, self.customer_service, self._reload_customer_lists)
    
    def edit_customer(self, event=None):
        for tree in [self.customer_tree, self.company_customer_tree]:
            selection = tree.selection()
            if selection:
                customer_id = tree.item(selection[0])['values'][0]
                customer = self.customer_service.get_customer(customer_id)
                if customer:
                    CustomerDialog(self.parent, self.customer_service, self.load_customers, customer)
                return
        messagebox.showwarning("Advertencia", "Seleccione un cliente")
    
    def delete_customer(self):
        for tree in [self.customer_tree, self.company_customer_tree]:
            selection = tree.selection()
            if selection:
                customer_id = tree.item(selection[0])['values'][0]
                customer = self.customer_service.get_customer(customer_id)
                if customer:
                    if messagebox.askyesno("Confirmar", f"¿Eliminar a '{customer['full_name']}'?\nEsta acción no se puede deshacer."):
                        AuditLogger.log(self.current_user['id'], "ELIMINAR_CLIENTE", 
                              f"Cliente ID: {customer_id} | Nombre: {customer['full_name']}")
                        self.customer_service.delete_customer(customer_id)
                        self.load_customers()
                return
        messagebox.showwarning("Advertencia", "Seleccione un cliente")
        
        if messagebox.askyesno("Confirmar", f"¿Eliminar a '{customer['full_name']}'?\nEsta acción no se puede deshacer."):
            AuditLogger.log(self.current_user['id'], "ELIMINAR_CLIENTE", 
                          f"Cliente ID: {customer_id} | Nombre: {customer['full_name']}")
            self.customer_service.delete_customer(customer_id)
            self.load_customers()

    def load_customers_to_combo(self):
        customers = self.customer_service.get_all_customers()
        customer_list = []
        for c in customers:
            if c.get('customer_type') == 'company':
                display_name = self._safe_customer_text(c.get('company_name') or c.get('full_name'), 'Sin nombre')
                display_doc = '-'
            else:
                display_name = self._safe_customer_text(c.get('full_name'), 'Sin nombre')
                display_doc = self._safe_customer_text(c.get('document_id') or c.get('document_number') or c.get('cedula') or c.get('id_number'), 'Sin documento')
            customer_list.append(f"{display_name} | {display_doc}")

        self.customer_search_values = customer_list
        self.customer_combo['values'] = customer_list
        if customer_list:
            self.customer_combo.set('')

    def on_customer_search(self, event=None):
        query = self.customer_var.get().strip().lower()
        if not query:
            self.customer_combo['values'] = self.customer_search_values
            return

        filtered = [value for value in self.customer_search_values if value.lower().startswith(query)]
        self.customer_combo['values'] = filtered if filtered else ['No se encontraron clientes']

    def on_customer_selected(self, event=None):
        value = self.customer_var.get().strip()
        if value == 'No se encontraron clientes':
            self.customer_var.set('')
            self.customer_combo['values'] = self.customer_search_values

    def add_customer_from_tasks(self):
        def refresh_customers():
            self.load_customers_to_combo()
        CustomerDialog(self.parent, self.customer_service, refresh_customers)
    
    # ==================== UTILIDADES ====================
    
    def get_user_name(self, user_id):
        if not user_id:
            return None
        users = self.auth_service.get_all_users()
        for u in users:
            if u['id'] == user_id:
                return u['full_name']
        return f"ID:{user_id}"
    
    def logout(self):
        self.notification_service.stop_monitoring()
        if hasattr(self.parent, '_logout_to_login'):
            self.parent._logout_to_login()
        else:
            self.auth_service.logout()
            self.parent.destroy()
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, timedelta
from tkcalendar import DateEntry
from database.connection import get_connection
from business.customer_service import CustomerService
from ui.dialogs.customer_dialog import CustomerDialog

class CustomerSupportView:
    def __init__(self, parent, auth_service, task_service, mode='service_client'):
        self.parent = parent
        self.auth_service = auth_service
        self.task_service = task_service
        self.current_user = auth_service.get_current_user()
        self.mode = mode
        self.customer_service = CustomerService()
        
        self.selected_order_id = None
        self.selected_customer_id = None
        
        self.parent.title("BR Corp - Panel de Servicio al Cliente")
        self.parent.geometry("1400x800")
        self.parent.configure(bg='#0f172a')
        
        self.setup_styles()
        self.setup_ui()
        self.load_data()
    
    def setup_styles(self):
        """Configura estilos visuales modernos"""
        style = ttk.Style()
        style.theme_use('clam')

        style.configure('TNotebook', background='#0f172a', borderwidth=0)
        style.configure('TNotebook.Tab', background='#1e293b', foreground='white',
                       padding=[15, 5], font=('Arial', 10, 'bold'))
        style.map('TNotebook.Tab', background=[('selected', '#4e73df')],
                  foreground=[('selected', 'white')])

        style.configure('Treeview', background='white', foreground='#333',
                       rowheight=30, fieldbackground='white', font=('Arial', 9))
        style.configure('Treeview.Heading', background='#4e73df', foreground='white',
                       font=('Arial', 10, 'bold'), relief='flat')
        style.map('Treeview.Heading', background=[('active', '#3b5ab9')])

    def setup_ui(self):
        header = tk.Frame(self.parent, bg='#4e73df', height=80)
        header.pack(fill='x')
        header.pack_propagate(False)

        logo_frame = tk.Frame(header, bg='#4e73df')
        logo_frame.pack(side='left', padx=25, pady=15)

        tk.Label(logo_frame, text="⚡", font=('Arial', 28, 'bold'),
                fg='white', bg='#4e73df').pack(side='left', padx=(0, 10))

        title = "Panel de Servicio al Cliente" if self.mode == 'service_client' else "Panel de Gerente"
        tk.Label(logo_frame, text="BR CORP", font=('Arial', 20, 'bold'),
                fg='white', bg='#4e73df').pack(side='left')
        tk.Label(logo_frame, text=f"{title} • {self.current_user['full_name']}",
                font=('Arial', 10), fg='#e0e0e0', bg='#4e73df').pack(side='left', padx=(15, 0))

        btn_frame = tk.Frame(header, bg='#4e73df')
        btn_frame.pack(side='right', padx=20)

        logout_btn = tk.Button(btn_frame, text="🚪 CERRAR SESIÓN", command=self.logout,
                              bg='white', fg='#e74a3b', font=('Arial', 10, 'bold'),
                              relief='flat', cursor='hand2', padx=20, pady=8)
        logout_btn.pack(side='right', padx=5)

        self.notebook = ttk.Notebook(self.parent, style='TNotebook')
        self.notebook.pack(fill='both', expand=True, padx=15, pady=15)

        self.status_bar = tk.Label(self.parent, text="✅ Sistema listo", bg='#1e293b', fg='#94a3b8',
                                   font=('Arial', 9), anchor='w')
        self.status_bar.pack(side='bottom', fill='x')

        self.orders_tab = tk.Frame(self.notebook, bg='#f8f9fa')
        self.notebook.add(self.orders_tab, text="📋 ÓRDENES")
        self.setup_orders_tab()

        self.customers_tab = tk.Frame(self.notebook, bg='#f8f9fa')
        self.notebook.add(self.customers_tab, text="👥 CLIENTES")
        self.setup_customers_tab()

        self.reports_tab = tk.Frame(self.notebook, bg='#f8f9fa')
        self.notebook.add(self.reports_tab, text="📊 REPORTES")
        try:
            self.setup_reports_tab()
        except ImportError:
            tk.Label(self.reports_tab,
                     text="Reportes no disponibles: instale matplotlib",
                     font=('Arial', 12, 'bold'), bg='#f8f9fa', fg='#6b7280').pack(pady=40)
        except Exception as e:
            tk.Label(self.reports_tab,
                     text=f"Error al cargar reportes: {str(e)}",
                     font=('Arial', 12, 'bold'), bg='#f8f9fa', fg='#e74a3b').pack(pady=40)

        self.completed_tab = tk.Frame(self.notebook, bg='#f8f9fa')
        self.notebook.add(self.completed_tab, text="✅ ÓRDENES LISTAS")
        self.setup_completed_tab()
    
    def setup_orders_tab(self):
        """Configura la pestaña de órdenes igual al patrón del admin"""
        left_panel = tk.Frame(self.orders_tab, bg='white', padx=25, pady=25,
                              highlightthickness=1, highlightbackground='#e0e0e0')
        left_panel.pack(side='left', fill='y', padx=(0, 15))

        title_frame = tk.Frame(left_panel, bg='white')
        title_frame.pack(fill='x', pady=(0, 20))
        tk.Label(title_frame, text="✨ NUEVA ORDEN", font=('Arial', 14, 'bold'),
                bg='white', fg='#4e73df').pack(side='left')

        tk.Label(left_panel, text="📌 Número de orden *", font=('Arial', 11, 'bold'),
                bg='white', fg='#333').pack(anchor='w', pady=(0, 5))
        self.title_entry = tk.Entry(left_panel, font=('Arial', 11),
                                   bg='#f8f9fa', relief='flat', bd=1)
        self.title_entry.pack(fill='x', pady=(0, 15), ipady=8)

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

        tk.Button(customer_frame, text="➕ Agregar Cliente", command=self.create_new_customer,
                 bg='#4e73df', fg='white', font=('Arial', 9, 'bold'),
                 relief='flat', cursor='hand2', padx=12, pady=5).pack(side='left')

        try:
            self.load_customers_to_combo()
        except Exception:
            pass

        tk.Label(left_panel, text="📝 Descripción", font=('Arial', 11, 'bold'),
                bg='white', fg='#333').pack(anchor='w', pady=(0, 5))
        self.desc_text = tk.Text(left_panel, height=5, font=('Arial', 10),
                                bg='#f8f9fa', relief='flat', bd=1)
        self.desc_text.pack(fill='x', pady=(0, 15))

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

        create_btn = tk.Button(left_panel, text="✨ CREAR ORDEN", command=self.create_order_from_tab,
                              bg='#1cc88a', fg='white', font=('Arial', 11, 'bold'),
                              relief='flat', cursor='hand2', padx=25, pady=12)
        create_btn.pack(fill='x', pady=(10, 0))
        create_btn.bind('<Enter>', lambda e: create_btn.config(bg='#17a673'))
        create_btn.bind('<Leave>', lambda e: create_btn.config(bg='#1cc88a'))

        right_panel = tk.Frame(self.orders_tab, bg='white', highlightthickness=1,
                               highlightbackground='#e0e0e0')
        right_panel.pack(side='right', fill='both', expand=True)

        task_toolbar = tk.Frame(right_panel, bg='#f8f9fa', height=45)
        task_toolbar.pack(fill='x', padx=15, pady=10)
        task_toolbar.pack_propagate(False)

        tk.Label(task_toolbar, text="📋 LISTA DE ÓRDENES", font=('Arial', 12, 'bold'),
                bg='#f8f9fa', fg='#4e73df').pack(side='left')

        btn_container = tk.Frame(task_toolbar, bg='#f8f9fa')
        btn_container.pack(side='right')

        tk.Button(btn_container, text="✏️ Editar", command=self.edit_order,
                 bg='#4e73df', fg='white', font=('Arial', 9, 'bold'),
                 relief='flat', cursor='hand2', padx=12, pady=5).pack(side='left', padx=3)

        tk.Button(btn_container, text="🔄 Refrescar", command=self.load_orders,
                 bg='#4e73df', fg='white', font=('Arial', 9, 'bold'),
                 relief='flat', cursor='hand2', padx=12, pady=5).pack(side='left', padx=3)

        table_frame = tk.Frame(right_panel, bg='white')
        table_frame.pack(fill='both', expand=True, padx=15, pady=(0, 10))

        columns = ('ID', 'Cliente', 'Número de orden', 'Prioridad', 'Estado', 'Fecha Vencimiento')
        self.orders_tree = ttk.Treeview(table_frame, columns=columns, show='headings', height=18)

        col_widths = {'ID': 50, 'Cliente': 200, 'Número de orden': 300, 'Prioridad': 100,
                      'Estado': 100, 'Fecha Vencimiento': 150}
        for col in columns:
            self.orders_tree.heading(col, text=col)
            self.orders_tree.column(col, width=col_widths.get(col, 100), anchor='center')

        scrollbar = ttk.Scrollbar(table_frame, orient='vertical', command=self.orders_tree.yview)
        self.orders_tree.configure(yscrollcommand=scrollbar.set)
        self.orders_tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')

        self.orders_tree.bind('<ButtonRelease-1>', self.on_order_select)
        self.orders_tree.bind('<Double-1>', self.on_order_double_click)
        self.load_orders()

    def update_hours_label(self):
        """Actualiza el texto visual de horas estimadas"""
        try:
            value = float(self.hours_var.get() or 0)
        except (TypeError, ValueError):
            value = 0

        total_minutes = int(round(value * 60))
        hours = total_minutes // 60
        minutes = total_minutes % 60
        self.hours_value_label.config(text=f"{hours}h {minutes:02d}m")

    def load_customers_to_combo(self):
        """Carga clientes para el combobox del formulario y deja lista la búsqueda instantánea"""
        if not hasattr(self, 'customer_combo'):
            return

        customers = self.customer_service.get_all_customers()
        values = []
        for customer in customers:
            if customer.get('customer_type') == 'company':
                name = customer.get('company_name', customer.get('full_name', 'Sin nombre'))
                doc = customer.get('rnc') or customer.get('tax_id') or customer.get('document_number') or 'Sin documento'
            else:
                name = customer.get('full_name', 'Sin nombre')
                doc = customer.get('document_number') or customer.get('cedula') or customer.get('id_number') or 'Sin documento'
            values.append(f"{name} | {doc}")

        self.customer_search_values = values
        self.customer_combo['values'] = values

    def on_customer_search(self, event=None):
        """Filtra clientes mientras se escribe el nombre desde la primera letra"""
        query = self.customer_var.get().strip().lower()
        if not query:
            self.customer_combo['values'] = self.customer_search_values
            return

        filtered = [value for value in self.customer_search_values if value.lower().startswith(query)]
        if filtered:
            self.customer_combo['values'] = filtered
        else:
            self.customer_combo['values'] = ['No se encontraron clientes']

    def on_customer_selected(self, event=None):
        """Se ejecuta cuando se elige un cliente de la lista sugerida"""
        value = self.customer_var.get().strip()
        if value == 'No se encontraron clientes':
            self.customer_var.set('')
            self.customer_combo['values'] = self.customer_search_values

    def create_order_from_tab(self):
        """Crea la orden desde el formulario de la pestaña"""
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
                    doc = customer.get('rnc') or customer.get('tax_id') or customer.get('document_number') or 'Sin documento'
                else:
                    name = customer.get('full_name', 'Sin nombre')
                    doc = customer.get('document_number') or customer.get('cedula') or customer.get('id_number') or 'Sin documento'
                if f"{name} | {doc}" == customer_selection:
                    customer_id = customer['id']
                    break

        due_date = self.due_date_entry.get_date().isoformat() if self.due_date_entry else None
        try:
            self.task_service.validate_task_data(
                title=title,
                customer_id=customer_id,
                priority=self.priority_var.get(),
                due_date=due_date,
                description=self.desc_text.get('1.0', 'end').strip(),
            )
        except ValueError as exc:
            messagebox.showwarning("Validación", str(exc))
            return

        try:
            self.task_service.create_task(
                title=title,
                description=self.desc_text.get('1.0', 'end').strip(),
                priority=self.priority_var.get(),
                estimated_hours=float(self.hours_var.get()) if self.hours_var.get() else 0,
                due_date=due_date,
                assigned_to=None,
                assigned_by=self.current_user['id'],
                customer_id=customer_id,
                created_by=self.current_user['id']
            )
            self.status_bar.config(text="✅ Orden creada")
            self.load_orders()
            self.title_entry.delete(0, tk.END)
            self.desc_text.delete('1.0', tk.END)
            self.priority_var.set('medium')
            self.hours_var.set(0.0)
            self.update_hours_label()
            self.due_date_var.set(datetime.now().strftime('%Y-%m-%d'))
            self.customer_var.set('')
            messagebox.showinfo("Éxito", "Orden creada correctamente")
        except Exception as e:
            messagebox.showerror("Error", f"Error al crear orden: {str(e)}")
    
    def setup_customers_tab(self):
        """Configura la pestaña de clientes con el mismo patrón visual del admin"""
        main_frame = tk.Frame(self.customers_tab, bg='white', padx=15, pady=15,
                              highlightthickness=1, highlightbackground='#e0e0e0')
        main_frame.pack(fill='both', expand=True)

        header = tk.Frame(main_frame, bg='white', height=45)
        header.pack(fill='x', pady=(0, 10))
        header.pack_propagate(False)

        tk.Label(header, text="👥 CLIENTES", font=('Arial', 14, 'bold'),
                bg='white', fg='#4e73df').pack(side='left')

        tk.Button(header, text="🔄 Refrescar", command=self._reload_customer_lists,
                 bg='#f59e0b', fg='white', font=('Arial', 10, 'bold'),
                 relief='flat', cursor='hand2', padx=12, pady=5).pack(side='right', padx=5)

        tk.Button(header, text="➕ Nuevo Cliente", command=self.create_new_customer,
                 bg='#4e73df', fg='white', font=('Arial', 10, 'bold'),
                 relief='flat', cursor='hand2', padx=15, pady=5).pack(side='right')

        search_frame = tk.Frame(main_frame, bg='white')
        search_frame.pack(fill='x', pady=(0, 10))

        tk.Label(search_frame, text="🔍 Buscar:", font=('Arial', 10), bg='white').pack(side='left', padx=(0, 8))

        self.customer_search_var = tk.StringVar()
        self.customer_search_entry = tk.Entry(search_frame, textvariable=self.customer_search_var,
                                             font=('Arial', 10), width=35, relief='solid', bd=1,
                                             bg='#ffffff', fg='#333333')
        self.customer_search_entry.pack(side='left', padx=(0, 8))
        self.customer_search_entry.bind('<KeyRelease>', self.filter_customers)

        tk.Button(search_frame, text="Buscar", command=self.search_customers,
                 bg='#4e73df', fg='white', font=('Arial', 9, 'bold'),
                 relief='flat', cursor='hand2', padx=12, pady=5).pack(side='left', padx=(0, 12))

        toggle_frame = tk.Frame(main_frame, bg='white')
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

        tables_frame = tk.Frame(main_frame, bg='white')
        tables_frame.pack(fill='both', expand=True)

        self.person_customer_container = tk.Frame(tables_frame, bg='white')
        self.company_customer_container = tk.Frame(tables_frame, bg='white')

        individual_frame = tk.Frame(self.person_customer_container, bg='white')
        individual_frame.pack(fill='both', expand=True)
        tk.Label(individual_frame, text='👤 PERSONAS', font=('Arial', 11, 'bold'), bg='white', fg='#4e73df').pack(anchor='w', pady=(0, 8))
        individual_cols = ('ID', 'Nombre', 'Email', 'Teléfono', 'Ciudad')
        self.customers_tree = ttk.Treeview(individual_frame, columns=individual_cols, show='headings', height=20)
        self.customers_tree.tag_configure('match', background='#f8d7da', foreground='#7f1d1d', font=('Arial', 9, 'bold'))
        individual_widths = {'ID': 50, 'Nombre': 220, 'Email': 180, 'Teléfono': 120, 'Ciudad': 150}
        for col in individual_cols:
            self.customers_tree.heading(col, text=col)
            self.customers_tree.column(col, width=individual_widths.get(col, 100), anchor='center')
        ind_scrollbar = ttk.Scrollbar(individual_frame, orient='vertical', command=self.customers_tree.yview)
        self.customers_tree.configure(yscrollcommand=ind_scrollbar.set)
        self.customers_tree.pack(side='left', fill='both', expand=True)
        ind_scrollbar.pack(side='right', fill='y')
        self.customers_tree.bind('<ButtonRelease-1>', self.on_customer_select)
        self.customers_tree.bind('<Double-1>', self.edit_customer)

        company_frame = tk.Frame(self.company_customer_container, bg='white')
        company_frame.pack(fill='both', expand=True)
        tk.Label(company_frame, text='🏢 EMPRESAS', font=('Arial', 11, 'bold'), bg='white', fg='#4e73df').pack(anchor='w', pady=(0, 8))
        company_cols = ('ID', 'Empresa', 'Email', 'Teléfono', 'Ciudad')
        self.company_customers_tree = ttk.Treeview(company_frame, columns=company_cols, show='headings', height=20)
        company_widths = {'ID': 50, 'Empresa': 220, 'Email': 180, 'Teléfono': 120, 'Ciudad': 150}
        for col in company_cols:
            self.company_customers_tree.heading(col, text=col)
            self.company_customers_tree.column(col, width=company_widths.get(col, 100), anchor='center')
        company_scrollbar = ttk.Scrollbar(company_frame, orient='vertical', command=self.company_customers_tree.yview)
        self.company_customers_tree.configure(yscrollcommand=company_scrollbar.set)
        self.company_customers_tree.pack(side='left', fill='both', expand=True)
        company_scrollbar.pack(side='right', fill='y')
        self.company_customers_tree.bind('<Double-1>', self.edit_customer)

        self._show_customer_view('individual')

        btn_frame = tk.Frame(main_frame, bg='white')
        btn_frame.pack(fill='x', pady=(10, 0))

        tk.Button(btn_frame, text='✏️ Editar Cliente', command=self.edit_customer,
                 bg='#4e73df', fg='white', font=('Arial', 10, 'bold'),
                 relief='flat', cursor='hand2', padx=15, pady=5).pack(side='left', padx=5)
    
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
        if hasattr(self, 'customer_search_var'):
            self.customer_search_var.set('')
        self.load_customers()
        self._show_customer_view(current_view)
        self._focus_latest_customer_in_active_view()

    def _focus_latest_customer_in_active_view(self):
        try:
            tree = self.company_customers_tree if self.customer_view_var.get() == 'company' else self.customers_tree
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

    def setup_completed_tab(self):
        """Configura la pestaña de órdenes completadas igual que en admin/gerencia."""
        frame = tk.Frame(self.completed_tab, bg='white', padx=15, pady=15,
                        highlightthickness=1, highlightbackground='#e0e0e0')
        frame.pack(fill='both', expand=True)

        toolbar = tk.Frame(frame, bg='white', height=45)
        toolbar.pack(fill='x', pady=(0, 10))
        toolbar.pack_propagate(False)

        tk.Label(toolbar, text="📦 ÓRDENES LISTAS", font=('Arial', 14, 'bold'),
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

        created_by_name = self.auth_service.get_user_by_id(task.get('created_by'))['full_name'] if hasattr(self.auth_service, 'get_user_by_id') and task.get('created_by') else 'Sistema'
        if not created_by_name and task.get('created_by'):
            created_by_name = f"ID {task.get('created_by')}"

        assigned_to_name = self.auth_service.get_user_by_id(task.get('assigned_to'))['full_name'] if hasattr(self.auth_service, 'get_user_by_id') and task.get('assigned_to') else 'Sin asignar'
        if not assigned_to_name and task.get('assigned_to'):
            assigned_to_name = f"ID {task.get('assigned_to')}"

        priority_display = {'critical': '🔴 Crítica', 'urgent': '🟠 Urgente',
                            'high': '🟡 Alta', 'medium': '🟢 Media', 'low': '🔵 Baja'}
        return customer_name, created_by_name, assigned_to_name, priority_display.get(task.get('priority'), '🟢 Media')

    def load_completed_tasks(self):
        try:
            for widget in self.completed_content_frame.winfo_children():
                widget.destroy()

            tasks = self.task_service.get_completed_tasks()
            if not tasks:
                tk.Label(self.completed_content_frame, text="No hay órdenes listas aún.",
                         bg='white', fg='#6c757d', font=('Arial', 11)).pack(anchor='w', pady=10)
                return

            grouped = self._get_completed_tasks_grouped(tasks)
            tk.Label(self.completed_content_frame,
                     text="📅 Las órdenes se organizan por año, mes y día como en gerencia/admin.",
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
                        body.pack_forget(); btn.config(text='▶')
                    else:
                        body.pack(fill='x', padx=8, pady=(0, 8)); btn.config(text='▼')
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
                            body.pack_forget(); btn.config(text='▶')
                        else:
                            body.pack(fill='x', padx=10, pady=(0, 8)); btn.config(text='▼')
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
                                body.pack_forget(); btn.config(text='▶')
                            else:
                                body.pack(fill='x', padx=10, pady=(0, 8)); btn.config(text='▼')
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

    def _month_order(self, month_name):
        order = {
            'Enero': 1, 'Febrero': 2, 'Marzo': 3, 'Abril': 4, 'Mayo': 5, 'Junio': 6,
            'Julio': 7, 'Agosto': 8, 'Septiembre': 9, 'Octubre': 10, 'Noviembre': 11, 'Diciembre': 12,
            'Sin fecha': 13
        }
        return order.get(month_name, 99)

    def setup_reports_tab(self):
        """Configura la pestaña de reportes igual que en admin/gerencia."""
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
    
    def load_data(self):
        """Carga datos de órdenes y clientes"""
        self.load_orders()
        self.load_customers()
    
    def load_orders(self):
        """Carga la lista de órdenes"""
        self.orders_tree.delete(*self.orders_tree.get_children())

        try:
            user_role = self.current_user.get('role') if self.current_user else None
            orders = self.task_service.get_visible_tasks(self.current_user['id'], user_role)

            for order in orders:
                customer_name = "Sin cliente"
                if order.get('customer_id'):
                    try:
                        customer = self.customer_service.get_customer(order['customer_id'])
                        if customer:
                            if customer.get('customer_type') == 'company':
                                customer_name = customer.get('company_name', customer.get('full_name', 'Sin cliente'))
                            else:
                                customer_name = customer.get('full_name', 'Sin cliente')
                    except:
                        pass
                
                priority_icon = {
                    'critical': '🔴', 'urgent': '🟠', 'high': '🟡', 'medium': '🟢', 'low': '🔵'
                }.get(order.get('priority', 'medium'), '🟢')
                
                status_display = {
                    'pending': '⏳ Pendiente',
                    'design': '🎨 En diseño',
                    'machine': '⚙️ En máquina',
                    'cleaning': '🧼 En limpieza',
                    'transit': '🚚 En tránsito',
                    'completed': '✅ Lista',
                    'in_progress': '⚙️ En progreso',
                    'cancelled': '❌ Cancelada'
                }.get(order.get('status', 'pending'), order.get('status', 'Desconocido'))
                
                self.orders_tree.insert('', 'end', values=(
                    order['id'],
                    customer_name,
                    order.get('title', ''),
                    f"{priority_icon} {order.get('priority', 'medium').upper()}",
                    status_display,
                    order.get('due_date', '')
                ))
        except Exception as e:
            messagebox.showerror("Error", f"Error al cargar órdenes: {str(e)}")
    
    def load_customers(self):
        """Carga la lista de clientes en dos tablas separadas por tipo."""
        self.customers_tree.delete(*self.customers_tree.get_children())
        self.company_customers_tree.delete(*self.company_customers_tree.get_children())

        try:
            customers = self.customer_service.get_all_customers()

            for customer in customers:
                if customer.get('customer_type') == 'company':
                    name = customer.get('company_name') or customer.get('full_name', 'Sin nombre')
                    self.company_customers_tree.insert('', 'end', values=(
                        customer['id'],
                        name,
                        customer.get('email', ''),
                        customer.get('company_phone') or customer.get('phone', ''),
                        customer.get('city', '')
                    ))
                else:
                    name = customer.get('full_name', '')
                    self.customers_tree.insert('', 'end', values=(
                        customer['id'],
                        name,
                        customer.get('email', ''),
                        customer.get('phone', ''),
                        customer.get('city', '')
                    ))

            self.filter_customers()
            self._focus_latest_customer_in_active_view()
        except Exception as e:
            messagebox.showerror("Error", f"Error al cargar clientes: {str(e)}")

    def search_customers(self):
        """Busca clientes con el estilo del admin."""
        self.filter_customers()

    def filter_customers(self, event=None):
        """Resalta los clientes que coincidan con la búsqueda y deja el resto normales."""
        if not hasattr(self, 'customers_tree'):
            return

        query = self.customer_search_var.get().strip().lower() if hasattr(self, 'customer_search_var') else ''
        for item in self.customers_tree.get_children():
            values = self.customers_tree.item(item, 'values')
            row_text = ' '.join(str(v) for v in values if v is not None).lower()
            if not query:
                self.customers_tree.item(item, tags=())
                continue

            if row_text.startswith(query):
                self.customers_tree.item(item, tags=())
            else:
                self.customers_tree.item(item, tags=('match',))

        for item in self.customers_tree.get_children():
            current_tags = list(self.customers_tree.item(item, 'tags'))
            if 'match' in current_tags:
                self.customers_tree.item(item, tags=('match',))
            else:
                self.customers_tree.item(item, tags=())
    
    def on_order_double_click(self, event=None):
        """Permite editar una orden con doble clic en servicio al cliente."""
        if not hasattr(self, 'orders_tree') or not self.orders_tree:
            return
        row_id = self.orders_tree.identify_row(event.y) if event else None
        if not row_id:
            return
        item_data = self.orders_tree.item(row_id, 'values')
        task_id = item_data[0] if item_data else None
        if task_id is not None:
            self.edit_order(task_id)

    def edit_order(self, task_id=None):
        """Edita una orden desde servicio al cliente usando el mismo flujo que admin."""
        if task_id is None:
            selection = self.tree.selection()
            if not selection:
                messagebox.showwarning('Advertencia', 'Seleccione una orden para editar')
                return
            task_id = self.tree.item(selection[0], 'values')[0]

        task = self.task_service.get_task(task_id)
        if not task:
            messagebox.showwarning('Advertencia', 'No se encontró la orden seleccionada')
            return

        dialog = tk.Toplevel(self.parent)
        dialog.title(f'Editar orden #{task_id}')
        dialog.geometry('650x640')
        dialog.configure(bg='white')
        dialog.transient(self.parent)
        dialog.grab_set()

        frame = tk.Frame(dialog, bg='white', padx=18, pady=18)
        frame.pack(fill='both', expand=True)

        tk.Label(frame, text=f'Editar Orden #{task_id}', font=('Arial', 14, 'bold'), bg='white', fg='#4e73df').pack(anchor='w', pady=(0, 18))

        tk.Label(frame, text='Número de orden *', bg='white', font=('Arial', 10, 'bold')).pack(anchor='w')
        title_var = tk.StringVar(value=task.get('title', ''))
        tk.Entry(frame, textvariable=title_var, width=60, font=('Arial', 10)).pack(fill='x', pady=(0, 12))

        tk.Label(frame, text='Cliente *', bg='white', font=('Arial', 10, 'bold')).pack(anchor='w')
        customers = self.customer_service.get_all_customers()
        customer_names = []
        current_customer_value = ''
        for c in customers:
            if c.get('customer_type') == 'company':
                name = c.get('company_name') or c.get('full_name') or 'Sin nombre'
                doc = '-'
            else:
                name = c.get('full_name') or 'Sin nombre'
                doc = c.get('document_id') or c.get('document_number') or c.get('cedula') or c.get('id_number') or 'Sin documento'
            entry_text = f"{name} | {doc}"
            customer_names.append(entry_text)
            if c['id'] == task.get('customer_id'):
                current_customer_value = entry_text
        customer_var = tk.StringVar(value=current_customer_value)
        ttk.Combobox(frame, textvariable=customer_var, values=customer_names, width=60, state='readonly', font=('Arial', 10)).pack(fill='x', pady=(0, 12))

        tk.Label(frame, text='Descripción', bg='white', font=('Arial', 10, 'bold')).pack(anchor='w')
        description_text = tk.Text(frame, height=5, width=60, font=('Arial', 10))
        description_text.pack(fill='x', pady=(0, 12))
        if task.get('description'):
            description_text.insert('1.0', task.get('description', ''))

        tk.Label(frame, text='Prioridad *', bg='white', font=('Arial', 10, 'bold')).pack(anchor='w')
        priority_var = tk.StringVar(value=task.get('priority', 'medium'))
        ttk.Combobox(frame, textvariable=priority_var, values=['critical', 'urgent', 'high', 'medium', 'low'], width=60, state='readonly', font=('Arial', 10)).pack(fill='x', pady=(0, 12))

        tk.Label(frame, text='Fecha de vencimiento *', bg='white', font=('Arial', 10, 'bold')).pack(anchor='w')
        due_date_entry = DateEntry(frame, width=48, background='#4e73df', foreground='white', borderwidth=2, date_pattern='yyyy-mm-dd')
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
            self.load_orders()

        tk.Button(btn_frame, text='💾 Guardar cambios', command=save_task, bg='#1cc88a', fg='white', font=('Arial', 10, 'bold'), relief='flat', padx=16, pady=8).pack(side='left')
        tk.Button(btn_frame, text='❌ Cancelar', command=dialog.destroy, bg='#d1d3e2', fg='#333333', font=('Arial', 10), relief='flat', padx=16, pady=8).pack(side='right')

    def create_new_order(self):
        """Abre diálogo para crear una nueva orden"""
        dialog = tk.Toplevel(self.parent)
        dialog.title("Nueva Orden")
        dialog.geometry("600x600")
        dialog.configure(bg='white')
        
        dialog_frame = tk.Frame(dialog, bg='white', padx=20, pady=20)
        dialog_frame.pack(fill='both', expand=True)
        
        tk.Label(dialog_frame, text="Nueva Orden de Trabajo", font=('Arial', 14, 'bold'),
                bg='white', fg='#4e73df').pack(anchor='w', pady=(0, 20))
        
        # Cliente
        tk.Label(dialog_frame, text="Cliente *", bg='white', font=('Arial', 10, 'bold')).pack(anchor='w')
        customers = self.customer_service.get_all_customers()
        customer_names = [f"{c.get('company_name') if c.get('customer_type') == 'company' else c.get('full_name')} (ID: {c['id']})" 
                         for c in customers]
        customer_var = tk.StringVar()
        ttk.Combobox(dialog_frame, textvariable=customer_var, values=customer_names,
                    width=50, state='readonly', font=('Arial', 10)).pack(fill='x', pady=(0, 15))
        
        # Número de orden
        tk.Label(dialog_frame, text="Número de orden *", bg='white', font=('Arial', 10, 'bold')).pack(anchor='w')
        title_var = tk.StringVar()
        tk.Entry(dialog_frame, textvariable=title_var, width=50, font=('Arial', 10)).pack(fill='x', pady=(0, 15))
        
        # Descripción
        tk.Label(dialog_frame, text="Descripción", bg='white', font=('Arial', 10, 'bold')).pack(anchor='w')
        description_text = tk.Text(dialog_frame, height=5, width=50, font=('Arial', 10))
        description_text.pack(fill='x', pady=(0, 15))
        
        # Prioridad
        tk.Label(dialog_frame, text="Prioridad *", bg='white', font=('Arial', 10, 'bold')).pack(anchor='w')
        priority_var = tk.StringVar(value='medium')
        ttk.Combobox(dialog_frame, textvariable=priority_var, 
                    values=['critical', 'urgent', 'high', 'medium', 'low'],
                    width=50, state='readonly', font=('Arial', 10)).pack(fill='x', pady=(0, 15))
        
        # Horas estimadas
        tk.Label(dialog_frame, text="Horas Estimadas", bg='white', font=('Arial', 10, 'bold')).pack(anchor='w')
        hours_var = tk.StringVar(value='0')
        tk.Entry(dialog_frame, textvariable=hours_var, width=50, font=('Arial', 10)).pack(fill='x', pady=(0, 15))
        
        # Fecha de vencimiento
        tk.Label(dialog_frame, text="Fecha de Vencimiento", bg='white', font=('Arial', 10, 'bold')).pack(anchor='w')
        date_entry = DateEntry(dialog_frame, width=48, background='darkblue',
                              foreground='white', borderwidth=2, font=('Arial', 10))
        date_entry.pack(fill='x', pady=(0, 20))
        
        # Botones
        btn_frame = tk.Frame(dialog_frame, bg='white')
        btn_frame.pack(fill='x', pady=(20, 0))
        
        def save_order():
            if not customer_var.get() or not title_var.get():
                messagebox.showwarning("Validación", "Por favor complete los campos obligatorios (*)")
                return

            try:
                customer_id = int(customer_var.get().split('ID: ')[-1].rstrip(')'))
                due_date = date_entry.get_date().isoformat() if date_entry else None
                self.task_service.validate_task_data(
                    title=title_var.get(),
                    customer_id=customer_id,
                    priority=priority_var.get(),
                    due_date=due_date,
                    description=description_text.get('1.0', 'end').strip(),
                )
                self.task_service.create_task(
                    title=title_var.get(),
                    description=description_text.get('1.0', 'end').strip(),
                    priority=priority_var.get(),
                    estimated_hours=float(hours_var.get()) if hours_var.get() else 0,
                    due_date=due_date,
                    assigned_to=None,
                    assigned_by=self.current_user['id'],
                    customer_id=customer_id,
                    created_by=self.current_user['id']
                )

                messagebox.showinfo("Éxito", "Orden creada correctamente")
                dialog.destroy()
                self.load_orders()
                self.status_bar.config(text="✅ Nueva orden creada")
            except ValueError as exc:
                messagebox.showwarning("Validación", str(exc))
            except Exception as e:
                messagebox.showerror("Error", f"Error al crear orden: {str(e)}")
        
        tk.Button(btn_frame, text="💾 Crear Orden", command=save_order,
                 bg='#4e73df', fg='white', relief='flat', cursor='hand2',
                 font=('Arial', 10, 'bold'), padx=15, pady=8).pack(side='left')
        
        tk.Button(btn_frame, text="❌ Cancelar", command=dialog.destroy,
                 bg='#d1d3e2', fg='#333333', relief='flat', cursor='hand2',
                 font=('Arial', 10), padx=15, pady=8).pack(side='right')
    
    def create_new_customer(self):
        """Abre diálogo para crear un nuevo cliente"""
        if hasattr(self, 'customer_search_var'):
            self.customer_search_var.set('')
        CustomerDialog(self.parent, self.customer_service, self._reload_customer_lists)
    
    def on_order_select(self, event):
        """Maneja la selección de una orden"""
        selection = self.orders_tree.selection()
        if selection:
            self.selected_order_id = int(self.orders_tree.item(selection[0])['values'][0])
    
    def on_customer_select(self, event):
        """Maneja la selección de un cliente"""
        for tree in [self.customers_tree, self.company_customers_tree]:
            selection = tree.selection()
            if selection:
                self.selected_customer_id = int(tree.item(selection[0])['values'][0])
                return

    def edit_customer(self, event=None):
        """Edita un cliente desde servicio al cliente usando el diálogo compartido."""
        for tree in [self.customers_tree, self.company_customers_tree]:
            selection = tree.selection()
            if selection:
                customer_id = tree.item(selection[0])['values'][0]
                customer = self.customer_service.get_customer(customer_id)
                if customer:
                    CustomerDialog(self.parent, self.customer_service, self.load_customers, customer)
                return
        messagebox.showwarning('Advertencia', 'Seleccione un cliente para editar')
    
    def update_reports(self):
        """Actualiza el reporte simple igual que en admin/gerencia."""
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
    
    def logout(self):
        """Cierra sesión del usuario y vuelve a la pantalla de login."""
        if messagebox.askyesno("Confirmar", "¿Desea cerrar sesión?"):
            if hasattr(self.parent, '_logout_to_login'):
                self.parent._logout_to_login()
            else:
                self.auth_service.logout()
                self.parent.destroy()

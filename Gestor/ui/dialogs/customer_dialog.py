import tkinter as tk
from tkinter import ttk, messagebox

RD_CITIES = [
    'Azua', 'Bahoruco', 'Barahona', 'Baní', 'Bonao', 'Constanza', 'Dajabón',
    'Distrito Nacional', 'Duarte', 'Elías Piña', 'El Seibo', 'Espaillat', 'Hato Mayor',
    'Hato Mayor del Rey', 'Hermanas Mirabal', 'Higüey', 'Independencia', 'Jarabacoa',
    'Jimaní', 'La Altagracia', 'La Romana', 'La Vega', 'Las Terrenas',
    'María Trinidad Sánchez', 'Monseñor Nouel', 'Monte Cristi', 'Monte Plata',
    'Moca', 'Nagua', 'Neyba', 'Pedernales', 'Peravia', 'Puerto Plata',
    'Samaná', 'San Cristóbal', 'San Felipe de Puerto Plata', 'San Francisco de Macorís',
    'San Ignacio de Sabaneta', 'San Isidro', 'San José de Ocoa', 'San Juan',
    'San Pedro de Macorís', 'Sánchez Ramírez', 'Santiago', 'Santiago Rodríguez',
    'Santo Domingo', 'Valverde', 'Valverde Mao', 'Villa Vásquez'
]

RNC_TYPES = [
    'RNC de 9 dígitos - Personas Jurídicas',
    'RNC de 11 dígitos - Personas Físicas nacionales',
    'Cédula de 11 dígitos - Empresa con cédula'
]

INDIVIDUAL_DOCUMENT_TYPES = [
    'Cédula de 11 dígitos - Nacional',
    'Pasaporte',
    'Permiso de residencia',
    'Licencia de conducir'
]

# Estilos personalizados
COLORS = {
    'primary': '#2563eb',
    'success': '#10b981',
    'danger': '#ef4444',
    'border': '#cbd5e1',
    'text': '#334155',
    'label': '#1e293b',
    'bg_light': '#f8fafc',
    'white': '#ffffff'
}

class ModernEntry(tk.Entry):
    """Entry personalizado con estilo moderno"""
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.config(
            font=('Segoe UI', 10),
            bg=COLORS['white'],
            fg=COLORS['text'],
            relief='solid',
            bd=1,
            highlightthickness=0,
            insertbackground=COLORS['primary']
        )
        # Aplicar borde sutil
        self.update_idletasks()
        self.tk.call('tk', 'scaling', '-displayof', self, 2.0)

class CustomerDialog:
    @staticmethod
    def validate_customer_data(customer_type, values):
        """Valida que todos los datos obligatorios del cliente estén completos."""
        if customer_type == 'individual':
            full_name = (values.get('full_name') or '').strip()
            document_type = (values.get('document_type') or '').strip()
            document_id = (values.get('document_id') or '').strip()
            email = (values.get('email') or '').strip()
            phone = (values.get('phone') or '').strip()
            city = (values.get('city') or '').strip()
            address = (values.get('address') or '').strip()

            if not full_name:
                raise ValueError('El nombre completo es obligatorio')
            if not document_type:
                raise ValueError('Debe seleccionar el tipo de documento')
            if not document_id:
                raise ValueError('El número de documento es obligatorio')
            if not email:
                raise ValueError('El email es obligatorio')
            if not phone:
                raise ValueError('El teléfono es obligatorio')
            if not phone.isdigit():
                raise ValueError('El teléfono debe contener solo números')
            if not city:
                raise ValueError('La ciudad es obligatoria')
            if not address:
                raise ValueError('La dirección es obligatoria')
            return True

        company_name = (values.get('company_name') or '').strip()
        company_ruc_type = (values.get('company_ruc_type') or '').strip()
        company_ruc = (values.get('company_ruc') or '').strip()
        email = (values.get('email') or '').strip()
        company_phone = (values.get('company_phone') or '').strip()
        city = (values.get('city') or '').strip()
        company_address = (values.get('company_address') or '').strip()
        contact_phone = (values.get('contact_phone') or '').strip()

        # En ediciones antiguas o casos legacy puede no venir company_name. La validación
        # de la forma UI lo exige, pero la capa central debe aceptar ambos escenarios.
        if 'company_name' in values and not company_name:
            raise ValueError('El nombre de la empresa es obligatorio')
        if not company_ruc_type:
            raise ValueError('Debe seleccionar el tipo de RNC')
        if not company_ruc:
            raise ValueError('El número de RNC es obligatorio')
        if not email:
            raise ValueError('El email es obligatorio')
        if not company_phone:
            raise ValueError('El teléfono comercial es obligatorio')
        if not company_phone.isdigit():
            raise ValueError('El teléfono comercial debe contener solo números')
        if not contact_phone:
            raise ValueError('El número de la persona de contacto es obligatorio')
        if not contact_phone.isdigit():
            raise ValueError('El número de la persona de contacto debe contener solo números')
        if not city:
            raise ValueError('La ciudad es obligatoria')
        if not company_address:
            raise ValueError('La dirección de facturación es obligatoria')
        return True

    def __init__(self, parent, customer_service, on_save_callback, customer=None):
        self.parent = parent
        self.customer_service = customer_service
        self.on_save_callback = on_save_callback
        self.customer = customer
        self.show()
    
    def show(self):
        title = "Cliente"
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title(title)
        self.dialog.geometry("1000x750")
        self.dialog.configure(bg=COLORS['white'])
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
        
        # Centrar
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (1000 // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (750 // 2)
        self.dialog.geometry(f'1000x750+{x}+{y}')
        
        # Encabezado con estilo moderno
        header_frame = tk.Frame(self.dialog, bg=COLORS['white'])
        header_frame.pack(fill='x', padx=30, pady=(20, 10))
        
        tk.Label(header_frame, text=title, font=('Segoe UI', 20, 'bold'),
                bg=COLORS['white'], fg=COLORS['primary']).pack(anchor='w')
        
        # Línea divisora
        ttk.Separator(self.dialog, orient='horizontal').pack(fill='x', pady=(0, 20))
        
        # Frame con scroll para el contenido
        canvas = tk.Canvas(self.dialog, bg=COLORS['white'], highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.dialog, orient='vertical', command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=COLORS['white'])
        
        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set, bg=COLORS['white'], highlightthickness=0)
        
        canvas.pack(side="left", fill="both", expand=True, padx=20)
        scrollbar.pack(side="right", fill="y", padx=(0, 10))
        
        # Tipo de cliente (fila completa)
        type_frame = tk.Frame(scrollable_frame, bg=COLORS['white'])
        type_frame.pack(fill='x', pady=(0, 25))
        
        tk.Label(type_frame, text="Tipo de cliente:", font=('Segoe UI', 11, 'bold'),
                bg=COLORS['white'], fg=COLORS['label']).pack(anchor='w', pady=(0, 10))
        
        rb_frame = tk.Frame(type_frame, bg=COLORS['white'])
        rb_frame.pack(anchor='w')
        
        self.type_var = tk.StringVar(value=self.customer.get('customer_type', 'individual') if self.customer else 'individual')
        
        rb_individual = tk.Radiobutton(rb_frame, text="Persona Particular", 
                                       variable=self.type_var, value='individual',
                                       bg=COLORS['white'], fg=COLORS['text'], font=('Segoe UI', 10),
                                       command=self.toggle_type, selectcolor=COLORS['white'],
                                       activebackground=COLORS['white'], activeforeground=COLORS['primary'])
        rb_individual.pack(side='left', padx=(0, 30))
        
        rb_company = tk.Radiobutton(rb_frame, text="Empresa", 
                                    variable=self.type_var, value='company',
                                    bg=COLORS['white'], fg=COLORS['text'], font=('Segoe UI', 10),
                                    command=self.toggle_type, selectcolor=COLORS['white'],
                                    activebackground=COLORS['white'], activeforeground=COLORS['primary'])
        rb_company.pack(side='left')
        
        # Frame dinámico para campos (grid de 2 columnas)
        self.dynamic_frame = tk.Frame(scrollable_frame, bg=COLORS['white'])
        self.dynamic_frame.pack(fill='both', expand=True)
        
        self.build_form()
        
        # Espacio antes de botones
        tk.Frame(scrollable_frame, bg=COLORS['white'], height=10).pack()
        
        # Botones con estilo moderno
        btn_frame = tk.Frame(scrollable_frame, bg=COLORS['white'])
        btn_frame.pack(fill='x', pady=(10, 0))
        
        save_btn = tk.Button(btn_frame, text="💾 Guardar", command=self.save,
                            bg=COLORS['success'], fg=COLORS['white'], font=('Segoe UI', 10, 'bold'),
                            relief='flat', padx=30, pady=10, cursor='hand2',
                            activebackground='#059669', activeforeground=COLORS['white'])
        save_btn.pack(side='left', padx=(0, 10))
        
        cancel_btn = tk.Button(btn_frame, text="✕ Cancelar", command=self.dialog.destroy,
                              bg=COLORS['danger'], fg=COLORS['white'], font=('Segoe UI', 10, 'bold'),
                              relief='flat', padx=25, pady=10, cursor='hand2',
                              activebackground='#dc2626', activeforeground=COLORS['white'])
        cancel_btn.pack(side='left')
    
    def build_form(self):
        """Construye el formulario según el tipo de cliente con una grilla estable."""
        for widget in self.dynamic_frame.winfo_children():
            widget.destroy()

        self.entries = {}
        customer_type = self.type_var.get()

        def infer_document_type(doc_value):
            if not doc_value:
                return 'Cédula de 11 dígitos - Nacional'
            digits = ''.join(ch for ch in str(doc_value) if ch.isdigit())
            if any(ch.isalpha() for ch in str(doc_value)):
                return 'Pasaporte'
            return 'Cédula de 11 dígitos - Nacional' if len(digits) == 11 else 'Pasaporte'

        def infer_company_rnc_type(rnc_value):
            if not rnc_value:
                return 'RNC de 9 dígitos - Personas Jurídicas'
            digits = ''.join(ch for ch in str(rnc_value) if ch.isdigit())
            return 'RNC de 11 dígitos - Personas Físicas nacionales' if len(digits) == 11 else 'RNC de 9 dígitos - Personas Jurídicas'

        self.dynamic_frame.grid_columnconfigure(0, weight=1, minsize=300)
        self.dynamic_frame.grid_columnconfigure(1, weight=1, minsize=300)

        row_index = 0

        if customer_type == 'individual':
            self._create_form_field("Nombre completo", "full_name", 0, row_index, span=2, required=True)
            row_index += 1

            self._create_form_field("Tipo de documento", "document_type", 0, row_index, required=True)
            self._create_form_field("Documento", "document_id", 1, row_index, required=True)
            row_index += 1

            self._create_form_field("Email", "email", 0, row_index, required=True)
            self._create_form_field("Teléfono", "phone", 1, row_index, required=True)
            row_index += 1

            self._create_form_field("Ciudad", "city", 0, row_index, span=2, required=True)
            row_index += 1

            self._create_form_field("Dirección", "address", 0, row_index, span=2, required=True)
            row_index += 1

            if self.customer and self.customer.get('customer_type') == 'individual':
                if self.customer.get('full_name'):
                    self.entries['full_name'].insert(0, self.customer['full_name'])
                if self.customer.get('document_id'):
                    self.entries['document_id'].configure(state='normal')
                    self.entries['document_id'].insert(0, self.customer['document_id'])
                if self.customer.get('email'):
                    self.entries['email'].insert(0, self.customer['email'])
                if self.customer.get('phone'):
                    self.entries['phone'].insert(0, self.customer['phone'])
                if self.customer.get('city'):
                    self.entries['city'].set(self.customer['city'])
                if self.customer.get('address'):
                    self.entries['address'].insert(0, self.customer['address'])

                selected_document_type = self.customer.get('document_type') or infer_document_type(self.customer.get('document_id'))
                self.entries['document_type'].set(selected_document_type)
                self._last_document_type_selection = selected_document_type
                self.update_document_field_state()
        else:
            self._create_form_field("Nombre de la empresa", "company_name", 0, row_index, required=True)
            self._create_form_field("Tipo de documento", "company_ruc_type", 1, row_index, required=True)
            row_index += 1

            self._create_form_field("RNC / Cédula", "company_ruc", 0, row_index, required=True)
            self._create_form_field("Actividad Comercial", "business_type", 1, row_index)
            row_index += 1

            self._create_form_field("Teléfono Comercial", "company_phone", 0, row_index, required=True)
            self._create_form_field("Correo Electrónico", "email", 1, row_index, required=True)
            row_index += 1

            self._create_form_field("Persona de Contacto", "contact_person", 0, row_index)
            self._create_form_field("Número de Contacto", "contact_phone", 1, row_index, required=True)
            row_index += 1

            self._create_form_field("Ciudad", "city", 0, row_index, span=2, required=True)
            row_index += 1

            self._create_form_field("Dirección de Facturación", "company_address", 0, row_index, span=2, required=True)
            row_index += 1

            self._create_form_field("Notas", "notes", 0, row_index, span=2, is_multiline=True)
            row_index += 1

            if self.customer and self.customer.get('customer_type') == 'company':
                if self.customer.get('company_name'):
                    self.entries['company_name'].insert(0, self.customer['company_name'])
                if self.customer.get('contact_person'):
                    self.entries['contact_person'].insert(0, self.customer['contact_person'])
                if self.customer.get('business_type'):
                    self.entries['business_type'].insert(0, self.customer['business_type'])
                if self.customer.get('company_phone'):
                    self.entries['company_phone'].insert(0, self.customer['company_phone'])
                if self.customer.get('email'):
                    self.entries['email'].insert(0, self.customer['email'])
                if self.customer.get('contact_phone'):
                    self.entries['contact_phone'].insert(0, self.customer['contact_phone'])
                if self.customer.get('city'):
                    self.entries['city'].set(self.customer['city'])
                if self.customer.get('company_address'):
                    self.entries['company_address'].insert(0, self.customer['company_address'])
                if self.customer.get('document_id'):
                    self.entries['company_ruc'].configure(state='normal')
                    self.entries['company_ruc'].insert(0, self.customer['document_id'])
                if self.customer.get('notes'):
                    self.entries['notes'].insert('1.0', self.customer['notes'])

                selected_rnc_type = self.customer.get('document_type') or infer_company_rnc_type(self.customer.get('document_id'))
                self.entries['company_ruc_type'].set(selected_rnc_type)
                self._last_rnc_type_selection = selected_rnc_type
                self.update_rnc_field_state()
    
    def _create_form_field(self, label, key, col, row, span=1, is_multiline=False, required=False):
        """Crea un campo del formulario con etiqueta"""
        # Frame del campo
        field_frame = tk.Frame(self.dynamic_frame, bg=COLORS['white'])
        field_frame.grid(row=row, column=col, columnspan=span, sticky='ew', padx=(0 if col == 0 else 15), pady=(0, 20))

        label_text = f"{label} *" if required else label
        label_color = COLORS['label']
        tk.Label(field_frame, text=label_text, font=('Segoe UI', 9, 'bold'),
                bg=COLORS['white'], fg=label_color).pack(anchor='w', pady=(0, 6))

        # Campo de entrada
        if is_multiline:
            entry = tk.Text(field_frame, height=4, font=('Segoe UI', 10), width=50,
                           bg=COLORS['white'], fg=COLORS['text'], relief='solid', bd=1,
                           insertbackground=COLORS['primary'], highlightthickness=0)
            entry.pack(fill='both', expand=True)
        elif key == 'city':
            # Combobox de ciudad con todas las ciudades RD
            entry = ttk.Combobox(field_frame, font=('Segoe UI', 10), width=47,
                                values=sorted(RD_CITIES), state='normal')
            entry.pack(fill='x')
            entry.bind('<KeyRelease>', lambda event, combo=entry: self.filter_combo(combo, sorted(RD_CITIES)))
        elif key == 'company_ruc_type':
            entry = ttk.Combobox(field_frame, font=('Segoe UI', 10), width=47,
                                values=RNC_TYPES, state='readonly')
            entry.pack(fill='x')
            entry.bind('<KeyRelease>', lambda event, combo=entry: self.filter_combo(combo, RNC_TYPES))
            entry.bind('<<ComboboxSelected>>', lambda event: self.update_rnc_field_state())
        elif key == 'company_ruc':
            entry = ModernEntry(field_frame, font=('Segoe UI', 10), width=50)
            entry.pack(fill='x')
            entry.configure(state='disabled')
            entry.bind('<KeyRelease>', lambda event: self.limit_rnc_input())
        elif key == 'document_type':
            entry = ttk.Combobox(field_frame, font=('Segoe UI', 10), width=47,
                                values=INDIVIDUAL_DOCUMENT_TYPES, state='readonly')
            entry.pack(fill='x')
            entry.bind('<KeyRelease>', lambda event, combo=entry: self.filter_combo(combo, INDIVIDUAL_DOCUMENT_TYPES))
            entry.bind('<<ComboboxSelected>>', lambda event: self.update_document_field_state())
        elif key == 'document_id':
            entry = ModernEntry(field_frame, font=('Segoe UI', 10), width=50)
            entry.pack(fill='x')
            entry.configure(state='disabled')
            entry.bind('<KeyRelease>', lambda event: self.limit_document_input())
        elif key in {'phone', 'company_phone'}:
            entry = ModernEntry(field_frame, font=('Segoe UI', 10), width=50)
            entry.pack(fill='x')
            entry.bind('<KeyRelease>', lambda event, field_key=key: self.limit_phone_input(field_key))
        else:
            entry = ModernEntry(field_frame, font=('Segoe UI', 10), width=50)
            entry.pack(fill='x')

        if required:
            self._apply_required_style(entry, True)

        self.entries[key] = entry

    def update_rnc_field_state(self):
        rnc_combo = self.entries.get('company_ruc_type')
        rnc_entry = self.entries.get('company_ruc')
        if not rnc_combo or not rnc_entry:
            return

        selected = rnc_combo.get().strip()
        previous = getattr(self, '_last_rnc_type_selection', None)
        current_value = rnc_entry.get().strip()

        if previous is not None and previous != selected and current_value:
            is_valid, _ = self.validate_rnc_type(selected, current_value)
            if not is_valid:
                rnc_entry.delete(0, tk.END)

        self._last_rnc_type_selection = selected

        if not selected:
            rnc_entry.configure(state='disabled')
            return

        if '9 dígitos' in selected:
            expected = 9
        elif '11 dígitos' in selected or 'Cédula' in selected:
            expected = 11
        else:
            expected = None

        if expected is None:
            rnc_entry.configure(state='disabled')
            return

        rnc_entry.configure(state='normal')
        value = rnc_entry.get().strip()
        digits = ''.join(ch for ch in value if ch.isdigit())[:expected]
        if digits != value:
            rnc_entry.delete(0, tk.END)
            rnc_entry.insert(0, digits)

    def update_document_field_state(self):
        doc_combo = self.entries.get('document_type')
        doc_entry = self.entries.get('document_id')
        if not doc_combo or not doc_entry:
            return

        selected = doc_combo.get().strip()
        previous = getattr(self, '_last_document_type_selection', None)
        current_value = doc_entry.get().strip()

        if previous is not None and previous != selected and current_value:
            is_valid, _ = self.validate_document_type(selected, current_value)
            if not is_valid:
                doc_entry.delete(0, tk.END)
                if hasattr(self, 'parent') and self.parent is not None:
                    try:
                        self.parent.update_idletasks()
                    except Exception:
                        pass

        self._last_document_type_selection = selected

        if not selected:
            doc_entry.configure(state='disabled')
            return

        doc_entry.configure(state='normal')

        if 'Cédula' in selected:
            value = doc_entry.get().strip()
            digits = ''.join(ch for ch in value if ch.isdigit())[:11]
            if digits != value:
                doc_entry.delete(0, tk.END)
                doc_entry.insert(0, digits)
        elif 'Licencia' in selected:
            value = doc_entry.get().strip()
            digits = ''.join(ch for ch in value if ch.isdigit())[:11]
            if digits != value:
                doc_entry.delete(0, tk.END)
                doc_entry.insert(0, digits)
        elif 'Pasaporte' in selected or 'Permiso' in selected:
            value = doc_entry.get().strip()
            cleaned = ''.join(ch for ch in value if ch.isalnum())
            if cleaned != value:
                doc_entry.delete(0, tk.END)
                doc_entry.insert(0, cleaned)

    def limit_rnc_input(self):
        rnc_combo = self.entries.get('company_ruc_type')
        rnc_entry = self.entries.get('company_ruc')
        if not rnc_combo or not rnc_entry:
            return

        selected = rnc_combo.get().strip()
        if not selected:
            rnc_entry.configure(state='disabled')
            return

        if '9 dígitos' in selected:
            expected = 9
        elif '11 dígitos' in selected or 'Cédula' in selected:
            expected = 11
        else:
            rnc_entry.configure(state='disabled')
            return

        value = rnc_entry.get().strip()
        digits = ''.join(ch for ch in value if ch.isdigit())[:expected]
        if digits != value:
            rnc_entry.delete(0, tk.END)
            rnc_entry.insert(0, digits)

    def limit_phone_input(self, key):
        entry = self.entries.get(key)
        if not entry:
            return

        value = entry.get()
        digits = ''.join(ch for ch in value if ch.isdigit())
        if digits != value:
            entry.delete(0, tk.END)
            entry.insert(0, digits)

    def limit_document_input(self):
        doc_combo = self.entries.get('document_type')
        doc_entry = self.entries.get('document_id')
        if not doc_combo or not doc_entry:
            return

        selected = doc_combo.get().strip()
        if not selected:
            doc_entry.configure(state='disabled')
            return

        if 'Cédula' in selected:
            value = doc_entry.get().strip()
            digits = ''.join(ch for ch in value if ch.isdigit())[:11]
            if digits != value:
                doc_entry.delete(0, tk.END)
                doc_entry.insert(0, digits)
        elif 'Licencia' in selected:
            value = doc_entry.get().strip()
            digits = ''.join(ch for ch in value if ch.isdigit())[:11]
            if digits != value:
                doc_entry.delete(0, tk.END)
                doc_entry.insert(0, digits)
        elif 'Pasaporte' in selected or 'Permiso' in selected:
            value = doc_entry.get().strip()
            cleaned = ''.join(ch for ch in value if ch.isalnum())
            if cleaned != value:
                doc_entry.delete(0, tk.END)
                doc_entry.insert(0, cleaned)

    def _apply_required_style(self, widget, is_required):
        bg = COLORS['white']
        if isinstance(widget, tk.Text):
            widget.configure(bg=bg, highlightthickness=0,
                            highlightbackground=COLORS['border'],
                            highlightcolor=COLORS['border'])
        elif isinstance(widget, ttk.Combobox):
            try:
                widget.configure(style='TCombobox')
            except Exception:
                widget.configure(background=bg)
        else:
            widget.configure(bg=bg, highlightthickness=0,
                            highlightbackground=COLORS['border'],
                            highlightcolor=COLORS['border'])

    def _reset_required_styles(self):
        for key, widget in self.entries.items():
            is_required = key in {'full_name', 'document_type', 'document_id', 'email', 'phone', 'city', 'address',
                                  'company_ruc_type', 'company_ruc', 'company_phone', 'company_address', 'contact_phone'}
            self._apply_required_style(widget, is_required)

    def _mark_missing_required(self, missing_keys):
        for key in self.entries:
            self._apply_required_style(self.entries[key], key in missing_keys)

    def toggle_type(self):
        if self.customer is not None:
            current_type = self.customer.get('customer_type')
            new_type = self.type_var.get()
            if current_type and new_type != current_type:
                if not messagebox.askyesno(
                    'Confirmar cambio de tipo de cliente',
                    f"¿Está seguro que desea cambiar este cliente de {('Persona Particular' if current_type == 'individual' else 'Empresa')} a {('Empresa' if new_type == 'company' else 'Persona Particular')}?\n\nEste cambio puede afectar los datos del formulario."
                ):
                    self.type_var.set(current_type)
                    return
        self.build_form()

    def validate_rnc(self, rnc_value, customer_type):
        """
        Valida el RNC/Cédula según el tipo de cliente
        - Personas Físicas (individual): 11 dígitos
        - Personas Jurídicas (company): 9 dígitos
        """
        if not rnc_value:
            return True, None  # Campo opcional
        
        # Remover espacios y caracteres especiales
        clean_rnc = ''.join(c for c in rnc_value if c.isdigit())
        
        if customer_type == 'individual':
            # Personas Físicas: 11 dígitos
            if len(clean_rnc) != 11:
                return False, f"La Cédula debe tener 11 dígitos. Usted ingresó {len(clean_rnc)} dígitos."
            return True, None
        else:  # company
            # Personas Jurídicas: 9 dígitos
            if len(clean_rnc) != 9:
                return False, f"El RNC debe tener 9 dígitos. Usted ingresó {len(clean_rnc)} dígitos."
            return True, None

    def filter_combo(self, combo, options):
        value = combo.get().strip().lower()
        if value:
            filtered = [item for item in options if value in item.lower()]
        else:
            filtered = list(options)
        combo.configure(values=filtered)
        if filtered:
            try:
                combo.event_generate('<Down>')
            except Exception:
                pass

    def validate_rnc_type(self, selected_type, value):
        """Valida el RNC según el tipo seleccionado."""
        if not selected_type:
            return False, "Debe seleccionar el tipo de RNC antes de ingresar el número."

        clean_value = ''.join(ch for ch in value if ch.isdigit())

        if '9 dígitos' in selected_type:
            if len(clean_value) != 9:
                return False, f"El RNC de Personas Jurídicas debe tener 9 dígitos. Ingresó {len(clean_value)}."
        elif '11 dígitos' in selected_type or 'Cédula' in selected_type:
            if len(clean_value) != 11:
                if 'Cédula' in selected_type:
                    return False, f"La Cédula de la empresa debe tener 11 dígitos. Ingresó {len(clean_value)}."
                return False, f"El RNC de Personas Físicas nacionales debe tener 11 dígitos. Ingresó {len(clean_value)}."

        return True, None

    def validate_document_type(self, selected_type, value):
        """Valida el tipo de documento según el tipo seleccionado."""
        if not selected_type:
            return False, "Debe seleccionar el tipo de documento antes de ingresar el número."

        if not value or not value.strip():
            return False, "El número de documento es obligatorio."

        clean_value = value.strip()
        only_digits = ''.join(ch for ch in clean_value if ch.isdigit())
        alphanumeric = ''.join(ch for ch in clean_value if ch.isalnum())

        if 'Cédula' in selected_type:
            if len(only_digits) != 11:
                return False, f"La cédula debe tener 11 dígitos. Ingresó {len(only_digits)}."
            return True, None

        if 'Licencia' in selected_type:
            if len(only_digits) != 11:
                return False, f"La licencia debe tener 11 dígitos. Ingresó {len(only_digits)}."
            return True, None

        if 'Pasaporte' in selected_type:
            if not alphanumeric or len(alphanumeric) < 6:
                return False, "El pasaporte debe tener al menos 6 caracteres alfanuméricos."
            return True, None

        if 'Permiso' in selected_type:
            if not only_digits or len(only_digits) < 6:
                return False, "El permiso debe contener solo números y tener al menos 6 dígitos."
            return True, None

        return True, None

    def save(self):
        customer_type = self.type_var.get()
        self._reset_required_styles()

        if customer_type == 'individual':
            values = {
                'full_name': self.entries['full_name'].get().strip(),
                'document_type': self.entries['document_type'].get().strip(),
                'document_id': self.entries['document_id'].get().strip(),
                'email': self.entries['email'].get().strip(),
                'phone': self.entries['phone'].get().strip(),
                'city': self.entries['city'].get().strip(),
                'address': self.entries['address'].get().strip(),
            }
            missing = [key for key, value in values.items() if not value or not str(value).strip()]
            if missing:
                self._mark_missing_required(missing)
                missing_labels = {
                    'full_name': 'Nombre completo',
                    'document_type': 'Tipo de documento',
                    'document_id': 'Documento',
                    'email': 'Correo electrónico',
                    'phone': 'Teléfono',
                    'city': 'Ciudad',
                    'address': 'Dirección',
                }
                label_list = ', '.join(missing_labels.get(key, key) for key in missing)
                messagebox.showerror('Error', f'Faltan campos obligatorios: {label_list}')
                return
            try:
                self.validate_customer_data(customer_type, values)
            except ValueError as exc:
                messagebox.showerror("Error", str(exc))
                return

            document_type = values['document_type']
            document_id = values['document_id']
            is_valid, error_msg = self.validate_document_type(document_type, document_id)
            if not is_valid:
                self._mark_missing_required(['document_type', 'document_id'])
                messagebox.showerror("Error en documento", error_msg)
                return

            data = {
                'customer_type': 'individual',
                'full_name': values['full_name'],
                'document_type': document_type,
                'document_id': document_id or None,
                'email': values['email'] or None,
                'phone': values['phone'] or None,
                'address': values['address'] or None,
                'city': values['city'] or None,
                'company_name': None,
                'company_phone': None,
                'company_address': None,
                'contact_person': None,
                'contact_phone': None,
                'business_type': None,
                'notes': None,
                'company_ruc_type': None,
                'company_ruc': None,
            }
        else:  # company
            values = {
                'company_name': self.entries['company_name'].get().strip(),
                'company_ruc_type': self.entries['company_ruc_type'].get().strip(),
                'company_ruc': self.entries['company_ruc'].get().strip(),
                'email': self.entries['email'].get().strip(),
                'company_phone': self.entries['company_phone'].get().strip(),
                'contact_phone': self.entries['contact_phone'].get().strip(),
                'city': self.entries['city'].get().strip(),
                'company_address': self.entries['company_address'].get().strip(),
            }
            missing = [key for key, value in values.items() if not value or not str(value).strip()]
            if missing:
                self._mark_missing_required(missing)
                missing_labels = {
                    'company_name': 'Nombre de la empresa',
                    'company_ruc_type': 'Tipo de RNC',
                    'company_ruc': 'RNC / Cédula',
                    'email': 'Correo electrónico',
                    'company_phone': 'Teléfono comercial',
                    'contact_phone': 'Número de contacto',
                    'city': 'Ciudad',
                    'company_address': 'Dirección de facturación',
                }
                label_list = ', '.join(missing_labels.get(key, key) for key in missing)
                messagebox.showerror('Error', f'Faltan campos obligatorios: {label_list}')
                return
            try:
                self.validate_customer_data(customer_type, values)
            except ValueError as exc:
                messagebox.showerror("Error", str(exc))
                return

            company_ruc_type = values['company_ruc_type']
            company_ruc = values['company_ruc']

            is_valid, error_msg = self.validate_rnc_type(company_ruc_type, company_ruc)
            if not is_valid:
                self._mark_missing_required(['company_ruc_type', 'company_ruc'])
                messagebox.showerror("Error en RNC", error_msg)
                return

            company_name_value = values['company_name'] or 'Empresa'
            contact_field = self.entries.get('contact_person')
            if contact_field:
                if isinstance(contact_field, tk.Text):
                    contact_person_value = contact_field.get("1.0", tk.END).strip() or None
                else:
                    contact_person_value = contact_field.get().strip() or None
            else:
                contact_person_value = None

            contact_phone_value = values['contact_phone'] or None
            company_phone_value = values['company_phone'] or None

            data = {
                'customer_type': 'company',
                'full_name': company_name_value,
                'company_name': company_name_value,
                'company_phone': company_phone_value,
                'company_address': values['company_address'] or None,
                'contact_person': contact_person_value,
                'contact_phone': contact_phone_value,
                'business_type': self.entries['business_type'].get().strip() or None,
                'email': values['email'] or None,
                'city': values['city'] or None,
                'notes': self.entries['notes'].get("1.0", tk.END).strip() or None,
                'document_type': company_ruc_type,
                'document_id': company_ruc,
                'phone': None,
                'address': None,
            }

        if self.customer:
            if self.customer_service.customer_exists(data, exclude_id=self.customer['id']):
                if not messagebox.askyesno(
                    "Cliente duplicado",
                    "Se encontró otro cliente con datos similares.\n\n¿Desea continuar y guardar los cambios de todas formas?"
                ):
                    return
            success = self.customer_service.update_customer(self.customer['id'], **data)
            if not success:
                messagebox.showerror("Error", "No se pudo actualizar el cliente. Verifique los datos e intente nuevamente.")
                return
        else:
            if self.customer_service.customer_exists(data):
                if not messagebox.askyesno(
                    "Cliente duplicado",
                    "Se encontró un cliente con datos similares.\n\n¿Desea continuar y guardar este cliente de todas formas?"
                ):
                    return
            created_id = self.customer_service.create_customer(**data)
            if created_id is None:
                messagebox.showerror("Error", "No se pudo guardar el cliente. Verifique los datos e intente nuevamente.")
                return
        
        self.dialog.destroy()
        if self.on_save_callback:
            self.parent.after(50, self.on_save_callback)

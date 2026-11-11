import tkinter as tk
from tkinter import messagebox
# from PIL import Image, ImageTk  ← AGREGA EL # AL INICIO
import hashlib

class LoginView:
    def __init__(self, parent, auth_service, on_success):
        self.parent = parent
        self.auth_service = auth_service
        self.on_success = on_success
        self.animation_id = None
        self.username_placeholder = "Usuario"
        self.password_placeholder = "Contraseña"
        self.setup_ui()
    
    def setup_ui(self):
        # Configurar ventana con fondo profundo
        self.parent.configure(bg='#020b1f')
        
        # Frame principal
        self.main_frame = tk.Frame(self.parent, bg='#020b1f')
        self.main_frame.pack(fill='both', expand=True)
        
        # Canvas para efectos visuales
        self.canvas = tk.Canvas(self.main_frame, bg='#020b1f', highlightthickness=0)
        self.canvas.pack(fill='both', expand=True)
        
        # Crear efecto de partículas (estrellas)
        self.particles = []
        self.create_particles()
        self.animate_particles()
        
        # Tarjeta de login premium
        self.card = tk.Frame(self.canvas, bg='#0f172a', padx=40, pady=32,
                            highlightthickness=2, highlightbackground='#4f46e5',
                            highlightcolor='#4f46e5', relief='flat')

        # Posicionar tarjeta centrada
        self.center_card()
        self.parent.after(50, self.center_card)

        # === LOGO / ICONO ===
        logo_frame = tk.Frame(self.card, bg='#0f172a')
        logo_frame.pack(pady=(0, 18))

        logo_bg = tk.Frame(logo_frame, bg='#4f46e5', padx=20, pady=16, relief='flat')
        logo_bg.pack()

        tk.Label(logo_bg, text="⚡", font=('Arial', 32, 'bold'),
                fg='white', bg='#4f46e5').pack()

        tk.Label(logo_frame, text="BR CORP", font=('Arial', 26, 'bold'),
                fg='#e0e7ff', bg='#0f172a').pack(pady=(12, 0))

        tk.Label(logo_frame, text="Gestión empresarial inteligente",
                font=('Arial', 11), fg='#818cf8', bg='#0f172a').pack(pady=(4, 0))
        
        # === FORMULARIO ===
        
        # Campo Usuario con icono
        user_frame = tk.Frame(self.card, bg='#111827')
        user_frame.pack(fill='x', pady=(18, 10))

        tk.Label(user_frame, text="👤", font=('Arial', 14),
                bg='#111827', fg='#a78bfa').pack(side='left', padx=(0, 10))

        self.username_entry = tk.Entry(user_frame, font=('Arial', 12),
                                      bg='#1f2937', fg='#e5e7eb',
                                      insertbackground='white',
                                      relief='flat', bd=0,
                                      highlightthickness=1,
                                      highlightcolor='#8b5cf6',
                                      highlightbackground='#374151',
                                      width=30)
        self.username_entry.pack(fill='x', expand=True, ipady=11)
        
        # Placeholder
        self.username_entry.insert(0, self.username_placeholder)
        self.username_entry.bind('<FocusIn>', self.on_user_focus_in)
        self.username_entry.bind('<FocusOut>', self.on_user_focus_out)
        
        # Campo Contraseña con icono
        pass_frame = tk.Frame(self.card, bg='#0f172a')
        pass_frame.pack(fill='x', pady=(15, 12))

        tk.Label(pass_frame, text="🔒", font=('Arial', 14),
                bg='#0f172a', fg='#a78bfa').pack(side='left', padx=(0, 12))

        self.password_entry = tk.Entry(pass_frame, font=('Arial', 12),
                                      bg='#1e293b', fg='#e0e7ff',
                                      insertbackground='#818cf8',
                                      show='', relief='flat', bd=0,
                                      highlightthickness=2,
                                      highlightcolor='#4f46e5',
                                      highlightbackground='#334155',
                                      width=30)
        self.password_entry.pack(fill='x', expand=True, ipady=12)
        
        self.password_entry.insert(0, self.password_placeholder)
        self.password_entry.bind('<FocusIn>', self.on_pass_focus_in)
        self.password_entry.bind('<FocusOut>', self.on_pass_focus_out)
        
        # === BOTÓN DE LOGIN ===
        self.login_btn = tk.Button(self.card, text="INICIAR SESIÓN",
                                  command=self.login,
                                  bg='#4f46e5', fg='white',
                                  font=('Arial', 13, 'bold'),
                                  relief='flat', cursor='hand2',
                                  padx=20, pady=14,
                                  highlightthickness=0,
                                  activebackground='#4338ca',
                                  activeforeground='white')
        self.login_btn.pack(fill='x', pady=(28, 14), ipady=2)

        # Efectos hover
        self.login_btn.bind('<Enter>', self.on_btn_hover)
        self.login_btn.bind('<Leave>', self.on_btn_leave)

        # === INFORMACIÓN DE PRUEBA ===
        info_frame = tk.Frame(self.card, bg='#0f172a')
        info_frame.pack(fill='x', pady=(8, 0))

        tk.Label(info_frame, text="🔑 Credenciales de prueba",
                font=('Arial', 9), fg='#818cf8', bg='#0f172a').pack()

        tk.Label(info_frame, text="admin / admin123",
                font=('Arial', 9, 'bold'), fg='#a78bfa', bg='#0f172a').pack()

        # === FOOTER ===
        footer = tk.Frame(self.card, bg='#0f172a')
        footer.pack(fill='x', pady=(28, 0))

        tk.Label(footer, text="© 2024 BR Corp - Todos los derechos reservados",
                font=('Arial', 8), fg='#64748b', bg='#0f172a').pack()
        
        # Bind eventos de redimension
        self.canvas.bind('<Configure>', self.on_resize)
        
        # Animación de entrada
        self.animate_card_entrance()
        
        # Bind tecla Enter
        self.username_entry.bind('<Return>', lambda e: self.password_entry.focus())
        self.password_entry.bind('<Return>', lambda e: self.login())
    
    def create_particles(self):
        """Crea partículas flotantes (estrellas) más visibles"""
        import random
        for _ in range(80):
            x = random.randint(0, 2000)
            y = random.randint(0, 1000)
            size = random.randint(1, 4)
            speed = random.uniform(0.3, 1.5)
            brightness = random.randint(80, 255)
            self.particles.append({
                'x': x, 'y': y, 'size': size, 'speed': speed,
                'brightness': brightness
            })
    
    def animate_particles(self):
        """Anima las partículas flotantes con efecto de parpadeo"""
        self.canvas.delete("particle")
        
        width = self.canvas.winfo_width()
        height = self.canvas.winfo_height()
        
        for p in self.particles:
            p['y'] -= p['speed']
            if p['y'] < 0:
                p['y'] = height
                import random
                p['x'] = random.randint(0, width)
            
            # Color más brillante para estrellas visibles
            b = p['brightness']
            color = f"#{min(b+50, 255):02x}{min(b+30, 255):02x}ff"
            self.canvas.create_oval(p['x'], p['y'], 
                                    p['x'] + p['size'], 
                                    p['y'] + p['size'],
                                    fill=color, outline='', tags="particle")
        
        self.animation_id = self.canvas.after(40, self.animate_particles)
    
    def center_card(self):
        """Recentrar la tarjeta con respecto al tamaño actual de la ventana."""
        self.canvas.update_idletasks()
        width = max(self.canvas.winfo_width(), self.parent.winfo_width())
        height = max(self.canvas.winfo_height(), self.parent.winfo_height())

        card_width = 460
        card_height = 560

        x = (width - card_width) // 2
        y = (height - card_height) // 2

        self.card.place(x=x, y=y, width=card_width, height=card_height)

    def on_resize(self, event):
        """Re-centrar tarjeta cuando se redimensiona"""
        self.center_card()
    
    def animate_card_entrance(self):
        """Animación de entrada de la tarjeta"""
        self.card.place_forget()
        
        width = self.canvas.winfo_width()
        height = self.canvas.winfo_height()
        
        card_width = 460
        card_height = 560
        
        x_initial = width
        y_initial = (height - card_height) // 2
        
        self.card.place(x=x_initial, y=y_initial, width=card_width, height=card_height)
        
        def animate(step=0):
            if step <= 30:
                new_x = x_initial - (step * (width - (width - card_width)//2) / 30)
                self.card.place(x=int(new_x), y=y_initial)
                self.canvas.after(10, lambda: animate(step + 1))
        
        animate()
    
    def on_user_focus_in(self, event):
        if self.username_entry.get() == self.username_placeholder:
            self.username_entry.delete(0, tk.END)
            self.username_entry.config(fg='white')
    
    def on_user_focus_out(self, event):
        if not self.username_entry.get():
            self.username_entry.insert(0, self.username_placeholder)
            self.username_entry.config(fg='#94a3b8')
    
    def on_pass_focus_in(self, event):
        if self.password_entry.get() == self.password_placeholder:
            self.password_entry.delete(0, tk.END)
            self.password_entry.config(show='•', fg='white')
    
    def on_pass_focus_out(self, event):
        if not self.password_entry.get():
            self.password_entry.insert(0, self.password_placeholder)
            self.password_entry.config(show='', fg='#94a3b8')
    
    def on_btn_hover(self, event):
        self.login_btn.config(bg='#3b5ab9')
        self.login_btn.config(padx=22, pady=14)
    
    def on_btn_leave(self, event):
        self.login_btn.config(bg='#4e73df')
        self.login_btn.config(padx=20, pady=12)
    
    def login(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()
        
        # Validar campos vacíos
        if username == self.username_placeholder or not username:
            messagebox.showerror("Error", "Por favor ingrese su usuario")
            self.shake_widget(self.username_entry)
            return
        
        if password == self.password_placeholder or not password:
            messagebox.showerror("Error", "Por favor ingrese su contraseña")
            self.shake_widget(self.password_entry)
            return
        
        # Efecto de carga en el botón
        original_text = self.login_btn.cget('text')
        self.login_btn.config(text="🔄 INICIANDO...", state='disabled')
        self.parent.update()
        
        # Intentar login
        self.parent.after(500, lambda: self.do_login(username, password, original_text))
    
    def do_login(self, username, password, original_text):
        success, message = self.auth_service.login(username, password)
        
        if success:
            self.login_btn.config(text="✅ ÉXITO", bg='#1cc88a')
            self.parent.after(500, self.on_success)
        else:
            self.login_btn.config(text=original_text, bg='#4e73df', state='normal')
            messagebox.showerror("Error", message)
            # Mantener la contraseña ingresada para corregir el error sin reescribirla
            self.password_entry.config(show='•')
            self.password_entry.focus()
            self.shake_widget(self.password_entry)
    
    def shake_widget(self, widget):
        """Efecto visual para errores sin alterar el tamaño del campo."""
        original_highlight = widget.cget('highlightbackground')
        original_color = widget.cget('highlightcolor')

        for _ in range(3):
            widget.configure(highlightbackground='#ef4444', highlightcolor='#ef4444')
            widget.update_idletasks()
            widget.after(70)
            widget.configure(highlightbackground=original_highlight, highlightcolor=original_color)
            widget.update_idletasks()
            widget.after(70)
    
    def __del__(self):
        if self.animation_id:
            self.canvas.after_cancel(self.animation_id)
import sys
from pathlib import Path

if __package__ in (None, ""):
    project_root = Path(__file__).resolve().parents[1]
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

import tkinter as tk
from tkinter import messagebox
import threading
from business.auth_service import AuthService
from business.task_service import TaskService
from ui.login_view import LoginView

class MainWindow:
    def __init__(self, root):
        self.root = root
        self.root.title("Gestor Empresarial - BR CORP")
        self.root.configure(bg='#f0f0f0')
        self.root.update_idletasks()
        self.root.state("zoomed")
        self.root.update_idletasks()
        self.root.bind("<Escape>", lambda event: self.root.state("normal"))
        
        self.auth_service = AuthService()
        self.task_service = TaskService()
        self.inactivity_timer = None

        self.setup_global_mouse_wheel()
        
        # Configurar detección de inactividad
        self.setup_inactivity_detection()
        
        self.show_login()
    
    def setup_global_mouse_wheel(self):
        """Activa el scroll con la rueda del ratón en toda la aplicación."""
        self.root.bind_all('<MouseWheel>', self._on_mouse_wheel)
        self.root.bind_all('<Shift-MouseWheel>', self._on_mouse_wheel)
        self.root.bind_all('<Button-4>', self._on_mouse_wheel_linux)
        self.root.bind_all('<Button-5>', self._on_mouse_wheel_linux)

    def _on_mouse_wheel(self, event):
        widget = event.widget
        delta = int(event.delta / 120)
        if delta == 0:
            return
        self._scroll_widget(widget, delta * 2)

    def _on_mouse_wheel_linux(self, event):
        widget = event.widget
        if event.num == 4:
            self._scroll_widget(widget, -2)
        elif event.num == 5:
            self._scroll_widget(widget, 2)

    def _scroll_widget(self, widget, direction):
        current = widget
        while current is not None:
            if hasattr(current, 'yview') and callable(current.yview):
                try:
                    current.yview_scroll(direction, 'units')
                    return
                except Exception:
                    pass
            current = getattr(current, 'master', None)

    def setup_inactivity_detection(self):
        """Configura los eventos que reinician el timer de inactividad"""
        # Bindear eventos del teclado
        self.root.bind_all('<Key>', lambda e: self.reset_inactivity_timer())
        # Bindear eventos del mouse (clic)
        self.root.bind_all('<Button>', lambda e: self.reset_inactivity_timer())
        # Bindear movimiento del mouse (opcional)
        self.root.bind_all('<Motion>', lambda e: self.reset_inactivity_timer())
    
    def reset_inactivity_timer(self):
        """Reinicia el contador de inactividad"""
        if self.inactivity_timer:
            self.inactivity_timer.cancel()
        
        # Solo iniciar timer si hay un usuario logueado
        if self.auth_service.get_current_user():
            self.inactivity_timer = threading.Timer(1800, self.auto_logout)  # 30 minutos = 1800 segundos
            self.inactivity_timer.daemon = True
            self.inactivity_timer.start()
    
    def auto_logout(self):
        """Cierra sesión automáticamente por inactividad"""
        if self.auth_service.get_current_user():
            # Mostrar mensaje de advertencia
            messagebox.showwarning("Sesión expirada", 
                                  "Su sesión ha sido cerrada por inactividad.\n\nPor favor, inicie sesión nuevamente.")
            
            # Cerrar sesión y volver al login
            self.auth_service.logout()
            
            # Cancelar timer
            if self.inactivity_timer:
                self.inactivity_timer.cancel()
                self.inactivity_timer = None
            
            # Volver a la pantalla de login en el hilo principal
            self.root.after(0, self.show_login)
    
    def cancel_inactivity_timer(self):
        """Cancela el timer de inactividad"""
        if self.inactivity_timer:
            self.inactivity_timer.cancel()
            self.inactivity_timer = None
    
    def show_login(self):
        """Muestra la pantalla de login"""
        self.cancel_inactivity_timer()

        for widget in self.root.winfo_children():
            widget.destroy()
        self.root.configure(bg='#020b1f')
        LoginView(self.root, self.auth_service, self.on_login_success)

    def _logout_to_login(self):
        """Vuelve al login sin cerrar la aplicación ni destruir la ventana raíz."""
        self.cancel_inactivity_timer()
        self.auth_service.logout()
        self.show_login()
    
    def on_login_success(self):
        """Callback cuando el login es exitoso"""
        print("=== LOGIN EXITOSO ===")
        # Reiniciar timer de inactividad
        self.reset_inactivity_timer()
        self.show_main_app()

    def bind_root_logout(self):
        """Expone la función de logout del MainWindow en la ventana raíz."""
        self.root._logout_to_login = self._logout_to_login
    
    def show_main_app(self):
        """Muestra la aplicación principal según el rol"""
        self.bind_root_logout()
        for widget in self.root.winfo_children():
            widget.destroy()

        user = self.auth_service.get_current_user()
        print(f"Usuario logueado: {user}")

        if user['role'] == 'admin':
            print("Abriendo AdminView")
            from ui.admin_view import AdminView
            AdminView(self.root, self.auth_service, self.task_service, is_manager_mode=False)
        elif user['role'] == 'manager':
            print("Abriendo Gerente (vista de admin sin gestión de usuarios)")
            from ui.admin_view import AdminView
            AdminView(self.root, self.auth_service, self.task_service, is_manager_mode=True)
        elif user['role'] == 'service_client':
            print("Abriendo CustomerSupportView (Servicio al cliente)")
            from ui.customer_support_view import CustomerSupportView
            CustomerSupportView(self.root, self.auth_service, self.task_service, mode='service_client')
        elif user['role'] == 'taller':
            print("Abriendo EmployeeView (Taller)")
            from ui.employee_view import EmployeeView
            EmployeeView(self.root, self.auth_service, self.task_service, mode='taller')
        else:
            print("Rol no reconocido, se abre vista de Taller por defecto")
            from ui.employee_view import EmployeeView
            EmployeeView(self.root, self.auth_service, self.task_service, mode='taller')
    
    def on_closing(self):
        """Maneja el cierre de la aplicación"""
        self.cancel_inactivity_timer()
        self.root.destroy()
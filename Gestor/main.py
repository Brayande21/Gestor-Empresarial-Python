import tkinter as tk
from database.connection import init_db
from ui.main_window import MainWindow
from utils.backup import backup_database
import threading

if __name__ == "__main__":
    # Inicializar base de datos
    init_db()

    # Crear backup inicial (solo una vez)
    try:
        backup_database()
        print("✅ Backup inicial creado")
    except Exception as e:
        print(f"⚠️ Error en backup: {e}")

    # Programar backups automáticos
    def schedule_backup():
        try:
            backup_database()
        except Exception as e:
            print(f"⚠️ Error en backup programado: {e}")
        # Volver a programar después de 24 horas
        threading.Timer(86400, schedule_backup).start()
 
    # Iniciar el timer
    backup_timer = threading.Timer(86400, schedule_backup)
    backup_timer.daemon = True
    backup_timer.start()
    
    # Iniciar aplicación
    root = tk.Tk()
    app = MainWindow(root)
    
    # Al cerrar
    root.protocol("WM_DELETE_WINDOW", lambda: (backup_timer.cancel(), root.destroy()))
    
    root.mainloop()   
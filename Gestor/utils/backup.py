import shutil
import os
from datetime import datetime
from pathlib import Path

def backup_database():
    """Crea un backup de la base de datos"""
    source = "database/empresa.db"
    backup_dir = "backups"
    
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    dest = f"{backup_dir}/empresa_backup_{timestamp}.db"
    
    try:
        shutil.copy2(source, dest)
        print(f"✅ Backup creado: {dest}")
        
        # Eliminar backups antiguos (más de 30 días)
        for file in os.listdir(backup_dir):
            file_path = os.path.join(backup_dir, file)
            if os.path.getctime(file_path) < (datetime.now().timestamp() - 30*24*3600):
                os.remove(file_path)
        
        return dest
    except Exception as e:
        print(f"❌ Error en backup: {e}")
        return None
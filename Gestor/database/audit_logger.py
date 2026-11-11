from database.connection import get_connection
from datetime import datetime

class AuditLogger:
    @staticmethod
    def log(user_id, action, details):
        conn = get_connection()
        cursor = conn.cursor()
        
        # Crear tabla si no existe
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                username TEXT,
                action TEXT,
                details TEXT,
                ip_address TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            INSERT INTO audit_log (user_id, username, action, details, created_at)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, 'Sistema', action, details, datetime.now().strftime("%Y-%Y-%m-%d %H:%M:%S")))
        
        conn.commit()
        conn.close()
    
    @staticmethod
    def get_logs(limit=100):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM audit_log ORDER BY created_at DESC LIMIT ?", (limit,))
        logs = cursor.fetchall()
        conn.close()
        return [dict(l) for l in logs]
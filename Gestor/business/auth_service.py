import hashlib
import time
from database.connection import get_connection

class AuthService:
    def __init__(self):
        self.current_user = None
        # Diccionario para rastrear intentos de login: {username: {'count': int, 'blocked_until': timestamp}}
        self.login_attempts = {}
    
    def hash_password(self, password):
        return hashlib.sha256(password.encode()).hexdigest()
    
    def is_blocked(self, username):
        """Verifica si un usuario está bloqueado"""
        if username in self.login_attempts:
            data = self.login_attempts[username]
            if data.get('blocked_until') and time.time() < data['blocked_until']:
                return True, data['blocked_until']
            elif data.get('blocked_until') and time.time() >= data['blocked_until']:
                # Reiniciar intentos si ya pasó el tiempo de bloqueo
                self.login_attempts[username] = {'count': 0, 'blocked_until': None}
        return False, None
    
    def register_failed_attempt(self, username):
        """Registra un intento fallido y devuelve si quedó bloqueado"""
        if username not in self.login_attempts:
            self.login_attempts[username] = {'count': 0, 'blocked_until': None}
        
        self.login_attempts[username]['count'] += 1
        
        # Bloquear después de 3 intentos fallidos
        if self.login_attempts[username]['count'] >= 3:
            self.login_attempts[username]['blocked_until'] = time.time() + 300  # 5 minutos
            return True  # Bloqueado
        return False
    
    def get_remaining_attempts(self, username):
        """Devuelve los intentos restantes antes del bloqueo"""
        if username in self.login_attempts:
            data = self.login_attempts[username]
            if data.get('blocked_until'):
                return 0
            return max(0, 3 - data.get('count', 0))
        return 3
    
    def login(self, username, password):
        # Verificar bloqueo
        blocked, blocked_until = self.is_blocked(username)
        if blocked:
            minutes_left = int((blocked_until - time.time()) / 60) + 1
            return False, f"Usuario bloqueado. Intente nuevamente en {minutes_left} minuto(s)"
        
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM users WHERE username = ? AND is_active = 1", (username,))
        user = cursor.fetchone()
        conn.close()
        
        if user and user['password_hash'] == self.hash_password(password):
            # Login exitoso: reiniciar intentos
            self.login_attempts[username] = {'count': 0, 'blocked_until': None}
            self.current_user = dict(user)
            return True, "Login exitoso"
        else:
            # Registrar intento fallido
            was_blocked = self.register_failed_attempt(username)
            remaining = self.get_remaining_attempts(username)
            
            if was_blocked:
                return False, "Demasiados intentos fallidos. Usuario bloqueado por 5 minutos"
            else:
                return False, f"Credenciales incorrectas. Le quedan {remaining} intento(s)"
    
    def logout(self):
        self.current_user = None
    
    def get_current_user(self):
        return self.current_user
    
    def get_all_users(self):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, username, full_name, email, role, department, position, is_active FROM users")
        users = cursor.fetchall()
        conn.close()
        return [dict(u) for u in users]

    def get_assignable_users(self):
        """Devuelve solo los usuarios que pueden recibir tareas asignadas.
        La operación de trabajo solo la realizan los usuarios del taller/producción.
        """
        users = self.get_all_users()
        return [user for user in users if user.get('role') == 'taller']
    
    def create_user(self, username, password, full_name, email, role, department='', position=''):
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        if cursor.fetchone():
            conn.close()
            return False
        
        password_hash = self.hash_password(password)
        cursor.execute('''
            INSERT INTO users (username, password_hash, full_name, email, role, department, position)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (username, password_hash, full_name, email, role, department, position))
        
        conn.commit()
        conn.close()
        return True
    
    def update_user_role(self, user_id, new_role):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET role = ? WHERE id = ?", (new_role, user_id))
        conn.commit()
        conn.close()
        return True
    
    def delete_user(self, user_id):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
        conn.commit()
        conn.close()
        return True
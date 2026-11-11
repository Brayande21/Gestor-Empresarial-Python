import sqlite3
from pathlib import Path
import config


def _connect_raw():
    return sqlite3.connect(config.DATABASE_PATH)


def get_connection():
    """Retorna conexión a la base de datos, asegurando que el esquema esté actualizado."""
    init_db()
    conn = _connect_raw()
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Inicializa la base de datos con todas las tablas"""
    conn = _connect_raw()
    cursor = conn.cursor()
    
    # Tabla de usuarios
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            full_name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            role TEXT CHECK(role IN ('admin', 'manager', 'taller', 'service_client')) NOT NULL,
            department TEXT,
            position TEXT,
            is_active BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Migración de permisos/roles para soportar la nueva estructura final
    cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='users'")
    user_schema_sql = cursor.fetchone()
    if user_schema_sql:
        schema_sql = user_schema_sql[0].lower()
        if 'taller' not in schema_sql or 'service_client' not in schema_sql:
            try:
                cursor.execute("ALTER TABLE users RENAME TO users_legacy")
                cursor.execute('''
                    CREATE TABLE users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT UNIQUE NOT NULL,
                        password_hash TEXT NOT NULL,
                        full_name TEXT NOT NULL,
                        email TEXT UNIQUE NOT NULL,
                        role TEXT CHECK(role IN ('admin', 'manager', 'taller', 'service_client')) NOT NULL,
                        department TEXT,
                        position TEXT,
                        is_active BOOLEAN DEFAULT 1,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                cursor.execute('''
                    INSERT INTO users (id, username, password_hash, full_name, email, role, department, position, is_active, created_at)
                    SELECT
                        id,
                        username,
                        password_hash,
                        full_name,
                        email,
                        CASE role
                            WHEN 'employee' THEN 'taller'
                            WHEN 'customer_support' THEN 'service_client'
                            ELSE role
                        END,
                        department,
                        position,
                        is_active,
                        created_at
                    FROM users_legacy
                ''')
                cursor.execute("DROP TABLE users_legacy")
                print("✅ Roles migrados a la estructura final")
            except Exception as e:
                print(f"⚠️ No fue necesario migrar roles: {e}")
    
    # Tabla de tareas
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            priority TEXT DEFAULT 'medium',
            status TEXT DEFAULT 'pending',
            estimated_hours REAL DEFAULT 0,
            actual_hours REAL DEFAULT 0,
            due_date DATE,
            assigned_to INTEGER,
            assigned_by INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP,
            completed_at TIMESTAMP,
            FOREIGN KEY (assigned_to) REFERENCES users(id),
            FOREIGN KEY (assigned_by) REFERENCES users(id)
        )
    ''')
    
    # Tabla de clientes
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_type TEXT CHECK(customer_type IN ('individual', 'company')) NOT NULL DEFAULT 'individual',
            full_name TEXT NOT NULL,
            document_type TEXT,
            document_id TEXT,
            email TEXT,
            phone TEXT,
            address TEXT,
            city TEXT,
            company_name TEXT,
            company_phone TEXT,
            company_address TEXT,
            contact_person TEXT,
            contact_phone TEXT,
            business_type TEXT,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP
        )
    ''')

    # Si la BD antigua quedó con document_id UNIQUE, reconstruimos la tabla sin esa restricción.
    cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='customers'")
    customer_schema = cursor.fetchone()
    if customer_schema and 'document_id' in (customer_schema[0] or '').lower() and 'unique' in (customer_schema[0] or '').lower():
        cursor.execute("ALTER TABLE customers RENAME TO customers_legacy")
        cursor.execute('''
            CREATE TABLE customers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_type TEXT CHECK(customer_type IN ('individual', 'company')) NOT NULL DEFAULT 'individual',
                full_name TEXT NOT NULL,
                document_type TEXT,
                document_id TEXT,
                email TEXT,
                phone TEXT,
                address TEXT,
                city TEXT,
                company_name TEXT,
                company_phone TEXT,
                company_address TEXT,
                contact_person TEXT,
                contact_phone TEXT,
                business_type TEXT,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP
            )
        ''')
        select_columns = [
            'id', 'customer_type', 'full_name', 'document_type', 'document_id', 'email', 'phone', 'address', 'city',
            'company_name', 'company_phone', 'company_address', 'contact_person', 'contact_phone', 'business_type', 'notes',
            'created_at', 'updated_at'
        ]
        cursor.execute(f"INSERT INTO customers ({', '.join(select_columns)}) SELECT {', '.join(select_columns)} FROM customers_legacy")
        cursor.execute("DROP TABLE customers_legacy")
        print("✅ Unicidad de document_id removida para permitir separar personas y empresas")

    # Migración para quitar columnas legacy de RUC/empresa que ya no forman parte del modelo
    cursor.execute("PRAGMA table_info(customers)")
    columns = [col[1] for col in cursor.fetchall()]
    legacy_columns = ['company_ruc', 'company_ruc_type']
    if any(col in columns for col in legacy_columns):
        cursor.execute("ALTER TABLE customers RENAME TO customers_legacy")
        cursor.execute('''
            CREATE TABLE customers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_type TEXT CHECK(customer_type IN ('individual', 'company')) NOT NULL DEFAULT 'individual',
                full_name TEXT NOT NULL,
                document_type TEXT,
                document_id TEXT,
                email TEXT,
                phone TEXT,
                address TEXT,
                city TEXT,
                company_name TEXT,
                company_phone TEXT,
                company_address TEXT,
                contact_person TEXT,
                contact_phone TEXT,
                business_type TEXT,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP
            )
        ''')
        select_columns = [
            'id', 'customer_type', 'full_name', 'document_type', 'document_id', 'email', 'phone', 'address', 'city',
            'company_name', 'company_phone', 'company_address', 'contact_person', 'contact_phone', 'business_type', 'notes',
            'created_at', 'updated_at'
        ]
        cursor.execute(f'''
            INSERT INTO customers ({', '.join(select_columns)})
            SELECT {', '.join(select_columns)} FROM customers_legacy
        ''')
        cursor.execute("DROP TABLE customers_legacy")
        print("✅ Columnas legacy de RUC eliminadas de customers")
    
    # Migración para tabla customers existente: agregar columnas nuevas si no existen
    cursor.execute("PRAGMA table_info(customers)")
    columns = [col[1] for col in cursor.fetchall()]
    new_columns = ['customer_type', 'city', 'company_name', 'company_phone', 'company_address', 'contact_person', 'contact_phone', 'business_type', 'document_type', 'notes']
    for col in new_columns:
        if col not in columns:
            cursor.execute(f'ALTER TABLE customers ADD COLUMN {col} TEXT')
            print(f"✅ Columna {col} agregada a customers")
    
    # Verificar si las columnas necesarias existen, si no, agregarlas
    cursor.execute("PRAGMA table_info(tasks)")
    columns = [col[1] for col in cursor.fetchall()]
    if 'customer_id' not in columns:
        cursor.execute('ALTER TABLE tasks ADD COLUMN customer_id INTEGER REFERENCES customers(id)')
        print("✅ Columna customer_id agregada a tasks")
    if 'created_by' not in columns:
        cursor.execute('ALTER TABLE tasks ADD COLUMN created_by INTEGER REFERENCES users(id)')
        print("✅ Columna created_by agregada a tasks")
    if 'assigned_by' not in columns:
        cursor.execute('ALTER TABLE tasks ADD COLUMN assigned_by INTEGER REFERENCES users(id)')
        print("✅ Columna assigned_by agregada a tasks")
    
    # Insertar admin por defecto si no existe
    cursor.execute("SELECT * FROM users WHERE username = 'admin'")
    if not cursor.fetchone():
        import hashlib
        password_hash = hashlib.sha256('admin123'.encode()).hexdigest()
        cursor.execute('''
            INSERT INTO users (username, password_hash, full_name, email, role, department, position)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', ('admin', password_hash, 'Administrador', 'admin@empresa.com', 'admin', 'Sistemas', 'Administrador'))
        print("✅ Usuario admin creado")
    
    conn.commit()
    conn.close()
    print("✅ Base de datos inicializada correctamente")
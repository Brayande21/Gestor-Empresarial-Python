from database.connection import get_connection
from datetime import datetime

class CustomerService:
    def __init__(self):
        pass

    def _normalize_text(self, value):
        return (value or "").strip().lower()

    def customer_exists(self, data, exclude_id=None):
        """Chequea si existe un cliente con identificadores coincidentes.
        El document_id no choca entre tipos de cliente; solo se controla dentro del mismo tipo.
        """
        conn = get_connection()
        cursor = conn.cursor()

        try:
            customer_type = (data.get('customer_type') or 'individual').strip()

            # Document ID (cedula) - único solo dentro del mismo tipo de cliente
            document_id = (data.get('document_id') or '').strip()
            if document_id:
                params = [document_id, customer_type]
                query = "SELECT id FROM customers WHERE document_id = ? AND customer_type = ?"
                if exclude_id is not None:
                    query += " AND id != ?"
                    params.append(exclude_id)
                cursor.execute(query, params)
                if cursor.fetchone():
                    return True

            # Email (case-insensitive)
            email = (data.get('email') or '').strip()
            if email:
                params = [self._normalize_text(email)]
                query = "SELECT id FROM customers WHERE lower(email) = ?"
                if exclude_id is not None:
                    query += " AND id != ?"
                    params.append(exclude_id)
                cursor.execute(query, params)
                if cursor.fetchone():
                    return True

            # Phone (may be in phone or company_phone)
            phone = (data.get('phone') or '').strip()
            company_phone = (data.get('company_phone') or '').strip()
            if phone:
                params = [phone]
                query = "SELECT id FROM customers WHERE phone = ?"
                if exclude_id is not None:
                    query += " AND id != ?"
                    params.append(exclude_id)
                cursor.execute(query, params)
                if cursor.fetchone():
                    return True
            if company_phone:
                params = [company_phone]
                query = "SELECT id FROM customers WHERE company_phone = ?"
                if exclude_id is not None:
                    query += " AND id != ?"
                    params.append(exclude_id)
                cursor.execute(query, params)
                if cursor.fetchone():
                    return True

            # Nombre exacto, solo dentro del mismo tipo de cliente: evita falsos positivos entre persona y empresa.
            if customer_type == 'individual':
                full_name = (data.get('full_name') or '').strip()
                if full_name:
                    normalized_name = self._normalize_text(full_name)
                    query = "SELECT id FROM customers WHERE lower(full_name) = ? AND customer_type = ?"
                    params = [normalized_name, customer_type]
                    if exclude_id is not None:
                        query += " AND id != ?"
                        params.append(exclude_id)
                    cursor.execute(query, params)
                    if cursor.fetchone():
                        return True
            else:
                company_name = (data.get('company_name') or '').strip()
                if company_name:
                    normalized_company = self._normalize_text(company_name)
                    query = "SELECT id FROM customers WHERE lower(company_name) = ? AND customer_type = ?"
                    params = [normalized_company, customer_type]
                    if exclude_id is not None:
                        query += " AND id != ?"
                        params.append(exclude_id)
                    cursor.execute(query, params)
                    if cursor.fetchone():
                        return True

            return False
        finally:
            conn.close()
    
    def _normalize_customer_payload(self, customer_type, data):
        """Limpia los campos cruzados para que cada cliente solo guarde su tipo real."""
        clean = dict(data or {})
        customer_type = (customer_type or 'individual').strip()
        previous_type = (clean.get('customer_type') or 'individual').strip()

        if customer_type == 'individual':
            clean['customer_type'] = 'individual'
            clean['phone'] = clean.get('phone') or None
            clean['address'] = clean.get('address') or None

            if previous_type != 'individual':
                clean['company_name'] = None
                clean['company_phone'] = None
                clean['company_address'] = None
                clean['contact_person'] = None
                clean['contact_phone'] = None
                clean['business_type'] = None
                clean['notes'] = None

            if 'document_type' not in clean or clean.get('document_type') is None:
                clean['document_type'] = None
            if 'document_id' not in clean or clean.get('document_id') is None:
                clean['document_id'] = None

            if 'full_name' not in clean or not clean.get('full_name'):
                clean['full_name'] = clean.get('company_name') or clean.get('full_name') or ''
        else:
            clean['customer_type'] = 'company'
            clean['phone'] = None
            clean['address'] = None

            if previous_type != 'company':
                clean['company_name'] = clean.get('company_name') or clean.get('full_name') or ''
                clean['company_phone'] = clean.get('company_phone') or None
                clean['company_address'] = clean.get('company_address') or None
                clean['contact_person'] = clean.get('contact_person') or None
                clean['contact_phone'] = clean.get('contact_phone') or None
                clean['business_type'] = clean.get('business_type') or None
                clean['notes'] = clean.get('notes') or None
            else:
                clean['company_name'] = clean.get('company_name') or clean.get('full_name') or ''

            clean['full_name'] = clean.get('company_name') or clean.get('full_name') or ''

        # Evitar espacios vacíos y dejar None para los valores faltantes.
        for key in ['full_name', 'document_type', 'document_id', 'email', 'phone', 'address', 'city',
                    'company_name', 'company_phone', 'company_address', 'contact_person', 'contact_phone',
                    'business_type', 'notes']:
            value = clean.get(key)
            if isinstance(value, str):
                cleaned = value.strip()
                clean[key] = cleaned or None
            elif value is not None and value == '':
                clean[key] = None

        return clean

    def create_customer(self, **kwargs):
        conn = get_connection()
        cursor = conn.cursor()
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Eliminar columnas legacy que ya no existen en la tabla.
        kwargs = {key: value for key, value in kwargs.items() if key not in {'company_ruc', 'company_ruc_type'}}

        defaults = {
            'customer_type': 'individual',
            'full_name': '', 'document_type': None, 'document_id': None, 'email': None, 'phone': None,
            'address': None, 'city': None, 'company_name': None, 'company_phone': None,
            'company_address': None, 'contact_person': None, 'contact_phone': None,
            'business_type': None, 'notes': None
        }
        defaults.update(kwargs)
        defaults = self._normalize_customer_payload(defaults.get('customer_type'), defaults)

        try:
            cursor.execute('''
                INSERT INTO customers (
                    customer_type, full_name, document_type, document_id, email, phone, address, city,
                    company_name, company_phone, company_address, contact_person, contact_phone, business_type,
                    notes, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                defaults['customer_type'], defaults['full_name'], defaults['document_type'], defaults['document_id'],
                defaults['email'], defaults['phone'], defaults['address'], defaults['city'],
                defaults['company_name'], defaults['company_phone'], defaults['company_address'],
                defaults['contact_person'], defaults['contact_phone'], defaults['business_type'],
                defaults['notes'], now, now
            ))
            conn.commit()
            customer_id = cursor.lastrowid
            conn.close()
            return customer_id
        except Exception:
            conn.close()
            return None
    
    def get_all_customers(self):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM customers ORDER BY full_name")
        customers = cursor.fetchall()
        conn.close()
        
        result = []
        for c in customers:
            c_dict = dict(c)
            if c_dict.get('customer_type') == 'individual':
                c_dict['display_name'] = c_dict.get('full_name')
                c_dict['display_doc'] = c_dict.get('document_id') or '-'
            else:
                c_dict['display_name'] = c_dict.get('company_name') or c_dict.get('full_name') or 'Empresa'
                c_dict['display_doc'] = '-'
            result.append(c_dict)
        
        return result
    
    def get_customer(self, customer_id):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM customers WHERE id = ?", (customer_id,))
        customer = cursor.fetchone()
        conn.close()
        return dict(customer) if customer else None
    
    def update_customer(self, customer_id, **kwargs):
        # Eliminar columnas legacy que ya no existen en la tabla.
        kwargs = {key: value for key, value in kwargs.items() if key not in {'company_ruc', 'company_ruc_type'}}

        current = self.get_customer(customer_id) or {}
        target_type = (kwargs.get('customer_type') or current.get('customer_type') or 'individual').strip()

        if current.get('customer_type') != target_type:
            if target_type == 'individual':
                kwargs['company_name'] = None
                kwargs['company_phone'] = None
                kwargs['company_address'] = None
                kwargs['contact_person'] = None
                kwargs['contact_phone'] = None
                kwargs['business_type'] = None
                kwargs['notes'] = None
            else:
                kwargs['phone'] = None
                kwargs['address'] = None

        payload = self._normalize_customer_payload(target_type, {**current, **kwargs})

        conn = get_connection()
        cursor = conn.cursor()

        fields = []
        values = []
        for key, value in payload.items():
            if key in {'id', 'created_at'}:
                continue
            fields.append(f"{key} = ?")
            values.append(value)

        if not fields:
            conn.close()
            return True

        values.append(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        values.append(customer_id)

        query = f"UPDATE customers SET {', '.join(fields)}, updated_at = ? WHERE id = ?"
        cursor.execute(query, values)
        conn.commit()
        conn.close()
        return True
    
    def delete_customer(self, customer_id):
        conn = get_connection()
        cursor = conn.cursor()
        try:
            # Mantener las órdenes, pero desvincularlas del cliente eliminado.
            cursor.execute("UPDATE tasks SET customer_id = NULL WHERE customer_id = ?", (customer_id,))
            cursor.execute("DELETE FROM customers WHERE id = ?", (customer_id,))
            deleted = cursor.rowcount > 0
            conn.commit()
            return deleted
        finally:
            conn.close()

    def delete_all_customers(self):
        """Elimina todos los clientes y conserva las órdenes sin cliente asociado."""
        conn = get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("UPDATE tasks SET customer_id = NULL WHERE customer_id IS NOT NULL")
            cursor.execute("DELETE FROM customers")
            deleted = cursor.rowcount
            conn.commit()
            return deleted
        finally:
            conn.close()
    
    def search_customers(self, term):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM customers 
            WHERE full_name LIKE ?
               OR company_name LIKE ?
               OR document_id LIKE ?
               OR email LIKE ?
               OR phone LIKE ?
               OR city LIKE ?
               OR notes LIKE ?
            ORDER BY full_name
        ''', (f'%{term}%', f'%{term}%', f'%{term}%', f'%{term}%', f'%{term}%', f'%{term}%', f'%{term}%'))
        customers = cursor.fetchall()
        conn.close()
        return [dict(c) for c in customers]

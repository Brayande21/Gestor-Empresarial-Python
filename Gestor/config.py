import os
from pathlib import Path

BASE_DIR = Path(__file__).parent
DATABASE_PATH = BASE_DIR / "database" / "empresa.db"

# Colores por prioridad
PRIORITY_COLORS = {
    'critical': '#FF0000',
    'urgent': '#FF4500',
    'high': '#FFA500',
    'medium': '#90EE90',
    'low': '#4A90E2'
}

# Roles activos del sistema
ROLES = {
    'admin': 1,
    'manager': 2,
    'taller': 3,
    'service_client': 4
}
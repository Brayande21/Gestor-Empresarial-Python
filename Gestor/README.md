# Gestor Empresarial — Gestión de órdenes de trabajo

Aplicación de escritorio en **Python, Tkinter y SQLite** para organizar tareas u órdenes de trabajo, clientes y usuarios dentro de una empresa.

## Funcionalidades implementadas

- Inicio de sesión y administración de usuarios con roles.
- Gestión de tareas u órdenes de trabajo, prioridades y asignaciones.
- Gestión de clientes.
- Interfaces diferenciadas para administración, personal de taller y servicio al cliente.
- Notificaciones y registro de auditoría.
- Copias de seguridad de la base de datos.
- Validaciones y pruebas automatizadas.

## Tecnologías

Python 3, Tkinter, SQLite, `unittest`/`pytest` (pruebas según los archivos del proyecto).

## Estructura

- `business/`: lógica de negocio y servicios.
- `database/`: conexión, esquema y auditoría.
- `ui/`: pantallas y diálogos.
- `utils/`: funciones auxiliares y copias de seguridad.
- `tests/`: pruebas.
- `main.py`: punto de entrada.

## Ejecución

1. Instala Python 3 en Windows.
2. Abre una terminal en la carpeta del proyecto.
3. Ejecuta `python main.py`.

La aplicación crea o inicializa su base de datos SQLite local. No se incluye ninguna base de datos real ni copia de seguridad en este repositorio.

## Seguridad y alcance

Proyecto demostrativo de portafolio. El código de autenticación utiliza SHA-256 sin un esquema moderno de derivación de contraseñas; **no debe utilizarse en producción sin reforzar la seguridad**. No se incluye el archivo de datos iniciales con credenciales de demostración.

## Autor

Brayan — Proyecto personal de desarrollo de software.

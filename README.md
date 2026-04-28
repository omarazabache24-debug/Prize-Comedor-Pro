# Sistema Comedor PRIZE - Render

Usuarios administradores totales:
- admin1 / admin123
- admin2 / admin123

Usuarios operativos demo:
- comedor / comedor123
- rrhh / rrhh123

En celular el menú se convierte en barra superior compacta y se oculta el panel derecho.
Los usuarios operativos solo ven Consumos, Entregas y Cerrar día.
El administrador puede crear, actualizar y eliminar usuarios desde Usuarios/Config.

## Render
Build command:
pip install -r requirements.txt

Start command:
gunicorn app:app

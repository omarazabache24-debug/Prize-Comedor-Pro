# Sistema Comedor PRIZE - Render

Paquete listo para subir a GitHub y conectar con Render.

## Archivos incluidos
- app.py
- requirements.txt
- Procfile
- runtime.txt
- carpetas necesarias para carga y reportes

## Usuarios demo
- admin / admin123
- rrhh / rrhh123
- comedor / comedor123

## Configuración en Render
- Build Command: pip install -r requirements.txt
- Start Command: gunicorn app:app

## Variables opcionales SMTP
SECRET_KEY, SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, SMTP_FROM

Nota: para producción real, usar base de datos externa porque los archivos locales de Render pueden reiniciarse.

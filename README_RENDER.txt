SISTEMA COMEDOR PRIZE - LISTO PARA RENDER

1) Subir estos archivos a GitHub.
2) En Render: New > Web Service > conectar repositorio.
3) Build Command: pip install -r requirements.txt
4) Start Command: gunicorn app:app
5) Variables opcionales para correo:
   SMTP_HOST=smtp.tudominio.com
   SMTP_PORT=587
   SMTP_USER=usuario@dominio.com
   SMTP_PASSWORD=clave
   SMTP_FROM=usuario@dominio.com
   REPORTE_DESTINO=administracion@prize.pe
6) Usuarios demo:
   admin / admin123
   rrhh / rrhh123
   comedor / comedor123

Nota: El cierre del día genera Excel en la carpeta reportes_cierre.
En Render con disco efímero, para guardar archivos permanentemente usa PostgreSQL y/o Render Disk.

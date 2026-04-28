# Solución para que Render tome las imágenes

Este paquete usa imágenes en `static/`:
- `static/logo.png`
- `static/logo_prize.jpeg`
- `static/login_referencia.png`
- `static/panel_referencia.png`

En Render:
1. Sube todos los archivos y la carpeta `static`.
2. En Render usa **Manual Deploy > Clear build cache & deploy**.
3. Si sigue saliendo imagen rota, revisa que en GitHub exista `static/logo.png`.
4. No subas solo `app.py`; debes subir todo el ZIP descomprimido.

Comandos Render:
- Build: `pip install -r requirements.txt`
- Start: `gunicorn app:app`

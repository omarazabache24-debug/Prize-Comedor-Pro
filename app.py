import os
import re
from io import BytesIO
from datetime import datetime, date
from functools import wraps

import pandas as pd
from flask import Flask, request, redirect, url_for, session, send_file, render_template_string, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")
os.makedirs(STATIC_DIR, exist_ok=True)

app = Flask(__name__, static_folder="static")
app.secret_key = os.getenv("SECRET_KEY", "prize-superfruits-render-dev")

DATABASE_URL = os.getenv("DATABASE_URL", "").strip()
if DATABASE_URL:
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL
else:
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///comedor_local.db"

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["MAX_CONTENT_LENGTH"] = 20 * 1024 * 1024

db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="comedor")
    active = db.Column(db.Boolean, default=True)

class Trabajador(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    empresa = db.Column(db.String(120), default="PRIZE")
    dni = db.Column(db.String(20), unique=True, nullable=False, index=True)
    nombre = db.Column(db.String(180), nullable=False, index=True)
    cargo = db.Column(db.String(120), default="")
    area = db.Column(db.String(120), default="", index=True)
    activo = db.Column(db.Boolean, default=True, index=True)
    actualizado = db.Column(db.DateTime, default=datetime.utcnow)
    creado = db.Column(db.DateTime, default=datetime.utcnow)

class Consumo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    dni = db.Column(db.String(20), nullable=False, index=True)
    trabajador = db.Column(db.String(180), nullable=False)
    empresa = db.Column(db.String(120), default="PRIZE")
    area = db.Column(db.String(120), default="")
    fecha = db.Column(db.Date, nullable=False, default=date.today, index=True)
    tipo = db.Column(db.String(50), default="Almuerzo")
    cantidad = db.Column(db.Integer, default=1)
    precio_unitario = db.Column(db.Float, default=0.0)
    total = db.Column(db.Float, default=0.0)
    observacion = db.Column(db.String(250), default="")
    creado_por = db.Column(db.String(50), default="")
    creado = db.Column(db.DateTime, default=datetime.utcnow)

# -------------------- helpers --------------------
def seed():
    users = [("admin", "admin123", "admin"), ("rrhh", "rrhh123", "rrhh"), ("comedor", "comedor123", "comedor")]
    for username, password, role in users:
        if not User.query.filter_by(username=username).first():
            db.session.add(User(username=username, password_hash=generate_password_hash(password), role=role))
    db.session.commit()

def clean_text(v):
    if pd.isna(v):
        return ""
    return str(v).strip()

def clean_dni(v):
    if pd.isna(v):
        return ""
    s = str(v).strip()
    s = re.sub(r"\.0$", "", s)
    s = re.sub(r"\D", "", s)
    return s.zfill(8) if 1 <= len(s) < 8 else s

def normalize_columns(cols):
    out = []
    for c in cols:
        x = str(c).strip().upper()
        x = x.replace("Á", "A").replace("É", "E").replace("Í", "I").replace("Ó", "O").replace("Ú", "U")
        x = x.replace("Ñ", "N")
        x = re.sub(r"\s+", "_", x)
        out.append(x)
    return out

def money(v):
    return f"S/ {float(v or 0):,.2f}"

app.jinja_env.filters["money"] = money

def login_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not session.get("user"):
            return redirect(url_for("login"))
        return fn(*args, **kwargs)
    return wrapper

def roles_required(*roles):
    def deco(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            if session.get("role") not in roles and session.get("role") != "admin":
                flash("No tienes permiso para esta opción.", "error")
                return redirect(url_for("dashboard"))
            return fn(*args, **kwargs)
        return wrapper
    return deco

BASE_HTML = """
<!doctype html><html lang="es"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>PRIZE ERP Comedor</title>
<style>
:root{--green:#2f8f3a;--green2:#184d2a;--dark:#071d29;--blue:#2f6f95;--orange:#e66b19;--bg:#eef6f8;--card:#fff;--muted:#64748b;--line:#dbe8eb;--danger:#dc2626;--ok:#16a34a}
*{box-sizing:border-box}body{margin:0;font-family:Segoe UI,Arial,sans-serif;background:linear-gradient(135deg,#eef8f3,#f8fbff);color:#08142a}a{text-decoration:none;color:inherit}.layout{display:grid;grid-template-columns:265px 1fr;min-height:100vh}.side{background:linear-gradient(180deg,#08202c,#061821);color:#fff;padding:22px;position:sticky;top:0;height:100vh}.brand{text-align:center;border-bottom:1px solid rgba(255,255,255,.14);padding-bottom:18px;margin-bottom:18px}.brand img{width:82px;height:82px;object-fit:contain;background:#fff;border-radius:999px;padding:8px}.brand h2{font-size:16px;margin:10px 0 0}.brand small{color:#dbeafe}.nav a{display:flex;gap:10px;align-items:center;padding:13px 14px;border-radius:15px;margin:7px 0;color:#dbeafe;font-weight:650}.nav a:hover,.nav .on{background:linear-gradient(90deg,rgba(47,143,58,.55),rgba(47,111,149,.22));color:#fff}.main{padding:26px}.top{display:flex;justify-content:space-between;align-items:center;margin-bottom:18px;gap:12px}.top h1{margin:0;font-size:30px}.muted{color:var(--muted)}.pill{background:#fff;border:1px solid var(--line);border-radius:999px;padding:9px 14px;color:#334155;box-shadow:0 6px 16px rgba(15,23,42,.06)}.grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:16px}.card{background:#fff;border:1px solid var(--line);border-radius:24px;padding:20px;box-shadow:0 12px 28px rgba(15,23,42,.08)}.kpi b{font-size:28px}.kpi span{display:block;color:var(--muted);font-size:13px;margin-top:5px}.form{display:grid;grid-template-columns:repeat(4,1fr);gap:12px}.form.full{grid-template-columns:repeat(3,1fr)}input,select,textarea{width:100%;padding:12px;border:1px solid #cbd5e1;border-radius:14px;background:#fff;font-size:14px}button,.btn{border:0;border-radius:14px;padding:12px 16px;background:var(--green);color:#fff;font-weight:800;cursor:pointer;display:inline-block}.btn2{background:#2f6f95}.btn3{background:#e66b19}.btn-danger{background:var(--danger)}.table-wrap{overflow:auto;border-radius:17px;border:1px solid var(--line)}table{width:100%;border-collapse:collapse;background:#fff}th,td{padding:12px;border-bottom:1px solid #e2e8f0;text-align:left;font-size:14px;white-space:nowrap}th{background:#f1f7f5;color:#0f172a;position:sticky;top:0}.flash{padding:13px 15px;border-radius:14px;margin-bottom:12px;border:1px solid #fde68a;background:#fffbeb}.flash.error{border-color:#fecaca;background:#fef2f2;color:#991b1b}.flash.ok{border-color:#bbf7d0;background:#f0fdf4;color:#166534}.login{max-width:430px;margin:7vh auto}.login .card{text-align:center}.login img{max-width:230px;margin-bottom:15px}.filters{display:grid;grid-template-columns:2fr 1fr 1fr 1fr auto;gap:10px;margin-bottom:14px}.badge{display:inline-flex;align-items:center;border-radius:999px;padding:5px 10px;font-size:12px;font-weight:800}.badge.ok{background:#dcfce7;color:#166534}.badge.off{background:#fee2e2;color:#991b1b}.actions{display:flex;gap:8px;flex-wrap:wrap}.notice{border-left:5px solid var(--green);padding:10px 12px;background:#f0fdf4;border-radius:12px;margin:10px 0}.mini{font-size:12px;color:#64748b}@media(max-width:1050px){.layout{grid-template-columns:1fr}.side{position:relative;height:auto}.grid{grid-template-columns:1fr 1fr}.form,.form.full,.filters{grid-template-columns:1fr}.main{padding:16px}.top{align-items:flex-start;flex-direction:column}}
</style></head><body>
{% if session.get('user') %}<div class="layout"><aside class="side"><div class="brand"><img src="{{ url_for('static', filename='logo.jpeg') }}"><h2>ERP Comedor</h2><small>{{session.get('user')}} · {{session.get('role')}}</small></div><nav class="nav">
<a class="{{'on' if page=='dashboard'}}" href="{{url_for('dashboard')}}">📊 Dashboard</a>
<a class="{{'on' if page=='consumos'}}" href="{{url_for('consumos')}}">🍽️ Consumos</a>
<a class="{{'on' if page=='trabajadores'}}" href="{{url_for('trabajadores')}}">👥 Trabajadores</a>
<a class="{{'on' if page=='reportes'}}" href="{{url_for('reportes')}}">📁 Reportes Planilla</a>
<a href="{{url_for('logout')}}">🚪 Salir</a></nav></aside><main class="main">{% endif %}
{% with messages=get_flashed_messages(with_categories=true) %}{% for c,m in messages %}<div class="flash {{c}}">{{m}}</div>{% endfor %}{% endwith %}
{{content|safe}}
{% if session.get('user') %}</main></div>{% endif %}
</body></html>
"""

def render_page(content, page=""):
    return render_template_string(BASE_HTML, content=content, page=page)

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = User.query.filter_by(username=request.form.get("username", "").strip()).first()
        if user and user.active and check_password_hash(user.password_hash, request.form.get("password", "")):
            session["user"] = user.username
            session["role"] = user.role
            return redirect(url_for("dashboard"))
        flash("Usuario o clave incorrecta.", "error")
    return render_page("""
    <div class='login'><div class='card'><img src='/static/logo.jpeg'><h2>Sistema Comedor PRIZE</h2><p class='muted'>Acceso ERP en Render</p>
    <form method='post'><input name='username' placeholder='Usuario' required><br><br><input name='password' type='password' placeholder='Clave' required><br><br><button style='width:100%'>Ingresar</button></form>
    <p class='muted'>admin/admin123 · rrhh/rrhh123 · comedor/comedor123</p></div></div>
    """)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/")
@login_required
def dashboard():
    today = date.today()
    mes, anio = today.month, today.year
    total_dia = db.session.query(db.func.sum(Consumo.total)).filter(Consumo.fecha == today).scalar() or 0
    total_mes = db.session.query(db.func.sum(Consumo.total)).filter(db.extract('month', Consumo.fecha) == mes, db.extract('year', Consumo.fecha) == anio).scalar() or 0
    cant_mes = db.session.query(db.func.sum(Consumo.cantidad)).filter(db.extract('month', Consumo.fecha) == mes, db.extract('year', Consumo.fecha) == anio).scalar() or 0
    trabajadores_activos = Trabajador.query.filter_by(activo=True).count()
    ultimos = Consumo.query.order_by(Consumo.creado.desc()).limit(12).all()
    rows = "".join([f"<tr><td>{c.fecha}</td><td>{c.dni}</td><td>{c.trabajador}</td><td>{c.tipo}</td><td>{c.cantidad}</td><td>{money(c.total)}</td></tr>" for c in ultimos]) or "<tr><td colspan='6'>Sin consumos registrados.</td></tr>"
    return render_page(f"""
    <div class='top'><div><h1>Dashboard Comedor</h1><p class='muted'>Control de consumos, planilla y trabajadores.</p></div><div class='pill'>Render + PostgreSQL</div></div>
    <div class='grid'><div class='card kpi'><b>{money(total_dia)}</b><span>Consumo de hoy</span></div><div class='card kpi'><b>{money(total_mes)}</b><span>Consumo mensual</span></div><div class='card kpi'><b>{int(cant_mes)}</b><span>Raciones del mes</span></div><div class='card kpi'><b>{trabajadores_activos}</b><span>Trabajadores activos</span></div></div><br>
    <div class='card'><h3>Últimos consumos</h3><div class='table-wrap'><table><tr><th>Fecha</th><th>DNI</th><th>Trabajador</th><th>Tipo</th><th>Cant.</th><th>Total</th></tr>{rows}</table></div></div>
    """, "dashboard")

@app.route("/consumos", methods=["GET", "POST"])
@login_required
@roles_required("admin", "rrhh", "comedor")
def consumos():
    if request.method == "POST":
        dni = clean_dni(request.form.get("dni", ""))
        t = Trabajador.query.filter_by(dni=dni).first()
        if not t or not t.activo:
            flash("DNI no encontrado o trabajador inactivo. Cárgalo primero en Trabajadores.", "error")
            return redirect(url_for("consumos"))
        try:
            cantidad = int(request.form.get("cantidad") or 1)
            precio = float(request.form.get("precio_unitario") or 0)
            fecha = datetime.strptime(request.form.get("fecha"), "%Y-%m-%d").date() if request.form.get("fecha") else date.today()
        except Exception:
            flash("Revisa fecha, cantidad o precio unitario.", "error")
            return redirect(url_for("consumos"))
        c = Consumo(dni=dni, trabajador=t.nombre, empresa=t.empresa, area=t.area, fecha=fecha, tipo=request.form.get("tipo", "Almuerzo"), cantidad=cantidad, precio_unitario=precio, total=cantidad * precio, observacion=request.form.get("observacion", ""), creado_por=session.get("user", ""))
        db.session.add(c); db.session.commit()
        flash(f"Consumo registrado: {t.nombre} - {money(c.total)}", "ok")
        return redirect(url_for("consumos"))
    qtxt = request.args.get("q", "").strip()
    tipo = request.args.get("tipo", "").strip()
    query = Consumo.query
    if qtxt:
        like = f"%{qtxt}%"
        query = query.filter(db.or_(Consumo.dni.ilike(like), Consumo.trabajador.ilike(like), Consumo.area.ilike(like)))
    if tipo:
        query = query.filter(Consumo.tipo == tipo)
    data = query.order_by(Consumo.fecha.desc(), Consumo.id.desc()).limit(300).all()
    rows = "".join([f"<tr><td>{c.fecha}</td><td>{c.dni}</td><td>{c.trabajador}</td><td>{c.area}</td><td>{c.tipo}</td><td>{c.cantidad}</td><td>{money(c.precio_unitario)}</td><td>{money(c.total)}</td></tr>" for c in data]) or "<tr><td colspan='8'>Sin registros.</td></tr>"
    return render_page(f"""
    <div class='top'><h1>Registro de Consumos</h1><a class='btn btn2' href='{url_for('exportar_consumos')}'>Exportar Excel</a></div>
    <div class='card'><form method='post' class='form'><input name='fecha' type='date' value='{date.today()}'><input name='dni' placeholder='DNI trabajador' required><select name='tipo'><option>Desayuno</option><option selected>Almuerzo</option><option>Cena</option><option>Otros</option></select><input name='cantidad' type='number' value='1' min='1'><input name='precio_unitario' type='number' step='0.01' value='0.00' placeholder='Precio unitario'><input name='observacion' placeholder='Observación'><button>Registrar consumo</button></form></div><br>
    <div class='card'><form method='get' class='filters'><input name='q' value='{qtxt}' placeholder='Buscar DNI, trabajador o área'><select name='tipo'><option value=''>Todos los tipos</option><option {'selected' if tipo=='Desayuno' else ''}>Desayuno</option><option {'selected' if tipo=='Almuerzo' else ''}>Almuerzo</option><option {'selected' if tipo=='Cena' else ''}>Cena</option><option {'selected' if tipo=='Otros' else ''}>Otros</option></select><button class='btn2'>Filtrar</button><a class='btn' href='{url_for('consumos')}'>Limpiar</a></form><div class='table-wrap'><table><tr><th>Fecha</th><th>DNI</th><th>Trabajador</th><th>Área</th><th>Tipo</th><th>Cant.</th><th>P. Unit.</th><th>Total</th></tr>{rows}</table></div></div>
    """, "consumos")

@app.route("/trabajadores", methods=["GET", "POST"])
@login_required
@roles_required("admin", "rrhh")
def trabajadores():
    if request.method == "POST" and request.form.get("manual") == "1":
        dni = clean_dni(request.form.get("dni", ""))
        if not dni:
            flash("DNI inválido.", "error"); return redirect(url_for("trabajadores"))
        t = Trabajador.query.filter_by(dni=dni).first() or Trabajador(dni=dni)
        t.empresa = clean_text(request.form.get("empresa", "PRIZE")) or "PRIZE"
        t.nombre = clean_text(request.form.get("nombre", ""))
        t.cargo = clean_text(request.form.get("cargo", ""))
        t.area = clean_text(request.form.get("area", ""))
        t.activo = True
        t.actualizado = datetime.utcnow()
        db.session.add(t); db.session.commit()
        flash("Trabajador guardado/actualizado correctamente.", "ok")
        return redirect(url_for("trabajadores"))

    if request.method == "POST" and "excel" in request.files:
        f = request.files.get("excel")
        if not f or not f.filename.lower().endswith((".xlsx", ".xls")):
            flash("Sube un archivo Excel .xlsx o .xls.", "error"); return redirect(url_for("trabajadores"))
        try:
            df = pd.read_excel(f, dtype=str).fillna("")
            df.columns = normalize_columns(df.columns)
        except Exception as e:
            flash(f"No se pudo leer el Excel: {e}", "error"); return redirect(url_for("trabajadores"))
        required = ["DNI", "NOMBRE"]
        missing = [c for c in required if c not in df.columns]
        if missing:
            flash("Faltan columnas obligatorias: " + ", ".join(missing) + ". Usa EMPRESA, DNI, NOMBRE, CARGO, AREA.", "error")
            return redirect(url_for("trabajadores"))
        inserted = updated = skipped = 0
        errores = []
        for idx, r in df.iterrows():
            dni = clean_dni(r.get("DNI", ""))
            nombre = clean_text(r.get("NOMBRE", ""))
            if not dni or not nombre:
                skipped += 1
                if len(errores) < 5: errores.append(f"Fila {idx+2}: DNI o NOMBRE vacío")
                continue
            t = Trabajador.query.filter_by(dni=dni).first()
            if t:
                updated += 1
            else:
                t = Trabajador(dni=dni)
                inserted += 1
            t.empresa = clean_text(r.get("EMPRESA", "PRIZE")) or "PRIZE"
            t.nombre = nombre
            t.cargo = clean_text(r.get("CARGO", ""))
            t.area = clean_text(r.get("AREA", ""))
            t.activo = True
            t.actualizado = datetime.utcnow()
            db.session.add(t)
        db.session.commit()
        msg = f"Excel importado: {inserted} nuevos, {updated} actualizados, {skipped} omitidos."
        if errores: msg += " | " + " ; ".join(errores)
        flash(msg, "ok" if skipped == 0 else "error")
        return redirect(url_for("trabajadores"))

    qtxt = request.args.get("q", "").strip()
    empresa = request.args.get("empresa", "").strip()
    area = request.args.get("area", "").strip()
    estado = request.args.get("estado", "").strip()
    query = Trabajador.query
    if qtxt:
        like = f"%{qtxt}%"
        query = query.filter(db.or_(Trabajador.dni.ilike(like), Trabajador.nombre.ilike(like), Trabajador.cargo.ilike(like)))
    if empresa:
        query = query.filter(Trabajador.empresa == empresa)
    if area:
        query = query.filter(Trabajador.area == area)
    if estado == "activo": query = query.filter(Trabajador.activo == True)
    if estado == "inactivo": query = query.filter(Trabajador.activo == False)
    data = query.order_by(Trabajador.nombre.asc()).limit(800).all()
    empresas = [x[0] for x in db.session.query(Trabajador.empresa).distinct().order_by(Trabajador.empresa).all() if x[0]]
    areas = [x[0] for x in db.session.query(Trabajador.area).distinct().order_by(Trabajador.area).all() if x[0]]
    rows = "".join([f"<tr><td>{t.empresa}</td><td>{t.dni}</td><td>{t.nombre}</td><td>{t.cargo}</td><td>{t.area}</td><td><span class='badge {'ok' if t.activo else 'off'}'>{'Activo' if t.activo else 'Inactivo'}</span></td></tr>" for t in data]) or "<tr><td colspan='6'>No hay trabajadores para mostrar.</td></tr>"
    opt_emp = "".join([f"<option value='{e}' {'selected' if e==empresa else ''}>{e}</option>" for e in empresas])
    opt_area = "".join([f"<option value='{a}' {'selected' if a==area else ''}>{a}</option>" for a in areas])
    return render_page(f"""
    <div class='top'><div><h1>Trabajadores</h1><p class='muted'>Carga masiva, actualización automática y búsqueda rápida.</p></div><div class='actions'><a class='btn btn2' href='{url_for('plantilla_trabajadores')}'>Descargar plantilla</a><a class='btn' href='{url_for('exportar_trabajadores')}'>Exportar base</a></div></div>
    <div class='card'><h3>Registro manual</h3><form method='post' class='form'><input type='hidden' name='manual' value='1'><input name='empresa' placeholder='Empresa' value='PRIZE'><input name='dni' placeholder='DNI' required><input name='nombre' placeholder='Nombre completo' required><input name='cargo' placeholder='Cargo'><input name='area' placeholder='Área'><button>Guardar / Actualizar</button></form></div><br>
    <div class='card'><h3>Carga masiva Excel</h3><div class='notice'>Formato aceptado: <b>EMPRESA, DNI, NOMBRE, CARGO, AREA</b>. Si el DNI ya existe, se actualiza; si no existe, se crea.</div><form method='post' enctype='multipart/form-data'><input type='file' name='excel' accept='.xlsx,.xls' required><br><br><button class='btn3'>Importar trabajadores</button></form></div><br>
    <div class='card'><h3>Base de trabajadores</h3><form method='get' class='filters'><input name='q' value='{qtxt}' placeholder='Buscar DNI, nombre o cargo'><select name='empresa'><option value=''>Todas las empresas</option>{opt_emp}</select><select name='area'><option value=''>Todas las áreas</option>{opt_area}</select><select name='estado'><option value=''>Todos</option><option value='activo' {'selected' if estado=='activo' else ''}>Activos</option><option value='inactivo' {'selected' if estado=='inactivo' else ''}>Inactivos</option></select><button class='btn2'>Filtrar</button></form><p class='mini'>Mostrando {len(data)} registro(s).</p><div class='table-wrap'><table><tr><th>Empresa</th><th>DNI</th><th>Nombre</th><th>Cargo</th><th>Área</th><th>Estado</th></tr>{rows}</table></div></div>
    """, "trabajadores")

@app.route("/reportes")
@login_required
@roles_required("admin", "rrhh")
def reportes():
    return render_page(f"""
    <div class='top'><h1>Reportes para Planilla</h1></div>
    <div class='card'><form method='get' action='{url_for('reporte_mensual')}' class='form full'><select name='mes'>{''.join([f'<option value={i} '+('selected' if i==date.today().month else '')+f'>{i:02d}</option>' for i in range(1,13)])}</select><input name='anio' type='number' value='{date.today().year}'><button>Descargar reporte mensual</button></form></div>
    <br><div class='card'><h3>Integración ERP</h3><p class='muted'>El Excel contiene DNI, trabajador, empresa, área, cantidad de consumos y total para descuento o control de planilla.</p></div>
    """, "reportes")

@app.route("/reporte_mensual")
@login_required
@roles_required("admin", "rrhh")
def reporte_mensual():
    mes = int(request.args.get("mes", date.today().month)); anio = int(request.args.get("anio", date.today().year))
    q = Consumo.query.filter(db.extract('month', Consumo.fecha) == mes, db.extract('year', Consumo.fecha) == anio).all()
    rows = [{"DNI": c.dni, "TRABAJADOR": c.trabajador, "EMPRESA": c.empresa, "AREA": c.area, "TIPO": c.tipo, "FECHA": c.fecha, "CANTIDAD": c.cantidad, "PRECIO_UNITARIO": c.precio_unitario, "TOTAL": c.total} for c in q]
    df = pd.DataFrame(rows)
    if not df.empty:
        resumen = df.groupby(["DNI", "TRABAJADOR", "EMPRESA", "AREA"], as_index=False).agg(CONSUMOS=("CANTIDAD", "sum"), TOTAL_PLANILLA=("TOTAL", "sum"))
    else:
        resumen = pd.DataFrame(columns=["DNI", "TRABAJADOR", "EMPRESA", "AREA", "CONSUMOS", "TOTAL_PLANILLA"])
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        resumen.to_excel(writer, sheet_name="RESUMEN_PLANILLA", index=False)
        df.to_excel(writer, sheet_name="DETALLE_CONSUMOS", index=False)
    output.seek(0)
    return send_file(output, as_attachment=True, download_name=f"reporte_planilla_comedor_{anio}_{mes:02d}.xlsx", mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

@app.route("/exportar_consumos")
@login_required
def exportar_consumos():
    q = Consumo.query.order_by(Consumo.fecha.desc()).all()
    df = pd.DataFrame([{"FECHA": c.fecha, "DNI": c.dni, "TRABAJADOR": c.trabajador, "EMPRESA": c.empresa, "AREA": c.area, "TIPO": c.tipo, "CANTIDAD": c.cantidad, "PRECIO_UNITARIO": c.precio_unitario, "TOTAL": c.total, "OBSERVACION": c.observacion} for c in q])
    output = BytesIO(); df.to_excel(output, index=False); output.seek(0)
    return send_file(output, as_attachment=True, download_name="consumos_comedor.xlsx", mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

@app.route("/exportar_trabajadores")
@login_required
@roles_required("admin", "rrhh")
def exportar_trabajadores():
    q = Trabajador.query.order_by(Trabajador.empresa, Trabajador.nombre).all()
    df = pd.DataFrame([{"EMPRESA": t.empresa, "DNI": t.dni, "NOMBRE": t.nombre, "CARGO": t.cargo, "AREA": t.area, "ESTADO": "ACTIVO" if t.activo else "INACTIVO"} for t in q])
    output = BytesIO(); df.to_excel(output, index=False); output.seek(0)
    return send_file(output, as_attachment=True, download_name="base_trabajadores_comedor.xlsx", mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

@app.route("/plantilla_trabajadores")
@login_required
def plantilla_trabajadores():
    df = pd.DataFrame([{"EMPRESA": "AQU ANQA II", "DNI": "12345678", "NOMBRE": "APELLIDOS Y NOMBRES", "CARGO": "OPERARIO", "AREA": "PRODUCCION"}])
    output = BytesIO(); df.to_excel(output, index=False); output.seek(0)
    return send_file(output, as_attachment=True, download_name="plantilla_trabajadores_comedor.xlsx", mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

with app.app_context():
    db.create_all()
    seed()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)), debug=True)

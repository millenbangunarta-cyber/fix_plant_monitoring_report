import os
from datetime import date, datetime
from io import BytesIO
from flask import Flask, request, redirect, session, flash, send_file, render_template_string
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet

COMPANY = "PT EQUALINDO MAKMUR ALAM SEJAHTERA"
APP_NAME = "FIX PLANT MONITORING REPORT"
PLANTS = ["BLC", "CPP BANGLADESH", "CPP JEPANG BESAR", "CPP JEPANG KECIL"]

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "replace-this-secret-key")
url = os.environ.get("DATABASE_URL", "sqlite:///fix_plant_monitoring.db")
if url.startswith("postgres://"):
    url = url.replace("postgres://", "postgresql://", 1)
app.config["SQLALCHEMY_DATABASE_URI"] = url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

class Equipment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    plant = db.Column(db.String(60), nullable=False)
    code = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(140), nullable=False)
    area = db.Column(db.String(100), default="")
    category = db.Column(db.String(80), default="")
    criticality = db.Column(db.String(20), default="Medium")
    status = db.Column(db.String(20), default="RFU")

class WorkOrder(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    wo_no = db.Column(db.String(50), unique=True, nullable=False)
    reported = db.Column(db.Date, default=date.today)
    plant = db.Column(db.String(60), nullable=False)
    equipment_code = db.Column(db.String(50), nullable=False)
    problem = db.Column(db.Text, nullable=False)
    priority = db.Column(db.String(20), default="Medium")
    status = db.Column(db.String(30), default="Open")
    action = db.Column(db.Text, default="")
    technician = db.Column(db.String(100), default="")
    downtime = db.Column(db.Float, default=0)
    closed = db.Column(db.Date, nullable=True)

class PMPlan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    plant = db.Column(db.String(60), nullable=False)
    equipment_code = db.Column(db.String(50), nullable=False)
    task = db.Column(db.String(220), nullable=False)
    frequency = db.Column(db.String(40), default="Monthly")
    due_date = db.Column(db.Date, nullable=False)
    pic = db.Column(db.String(100), default="")
    status = db.Column(db.String(30), default="Scheduled")
    remarks = db.Column(db.Text, default="")

class Inventory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    plant = db.Column(db.String(60), nullable=False)
    item = db.Column(db.String(150), nullable=False)
    part_no = db.Column(db.String(80), default="")
    unit = db.Column(db.String(30), default="pcs")
    stock = db.Column(db.Float, default=0)
    min_stock = db.Column(db.Float, default=0)
    location = db.Column(db.String(100), default="")

class StockTransaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey("inventory.id"), nullable=False)
    trx_type = db.Column(db.String(10), nullable=False)
    qty = db.Column(db.Float, nullable=False)
    person = db.Column(db.String(100), default="")
    reference = db.Column(db.String(100), default="")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Supplier(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    contact = db.Column(db.String(100), default="")
    phone = db.Column(db.String(50), default="")
    email = db.Column(db.String(120), default="")
    address = db.Column(db.Text, default="")

class Activity(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    activity_date = db.Column(db.Date, default=date.today)
    plant = db.Column(db.String(60), nullable=False)
    equipment_code = db.Column(db.String(50), default="")
    description = db.Column(db.Text, nullable=False)
    person = db.Column(db.String(100), default="")
    remarks = db.Column(db.Text, default="")

def auth():
    return session.get("auth") is True

@app.before_request
def guard():
    if request.endpoint not in ("login", "health", "static") and not auth():
        return redirect("/login")

@app.route("/health")
def health():
    return {"status": "ok", "application": APP_NAME}

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = os.environ.get("ADMIN_USERNAME", "admin")
        password = os.environ.get("ADMIN_PASSWORD", "ChangeMe123!")
        if request.form.get("username") == username and request.form.get("password") == password:
            session["auth"] = True
            return redirect("/")
        flash("Username atau password tidak sesuai.")
    return render_template_string(TEMPLATE, title="Login", body=LOGIN_BODY)

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

TEMPLATE = r"""
<!doctype html><html lang="id"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{{title}} | FIX PLANT MONITORING REPORT</title>
<style>
:root{--navy:#14243a;--blue:#2563eb;--bg:#f3f6fa;--line:#e2e8f0;--muted:#64748b}
*{box-sizing:border-box}body{margin:0;font-family:Arial,sans-serif;background:var(--bg);color:#172033}
header{background:var(--navy);color:white;padding:15px 22px;display:flex;justify-content:space-between;align-items:center;gap:12px}
.brand{font-weight:800;letter-spacing:.4px}.sub{font-size:11px;color:#cbd5e1;margin-top:4px}
.layout{display:flex;min-height:calc(100vh - 58px)}nav{width:235px;background:#1d314d;padding:14px 10px;flex-shrink:0}
nav a{display:block;color:#dbeafe;text-decoration:none;padding:10px 12px;border-radius:7px;margin:3px 0;font-size:13px}nav a:hover{background:#304968}
main{padding:24px;flex:1;min-width:0}.muted{color:var(--muted);font-size:12px}.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(155px,1fr));gap:13px;margin:18px 0}
.card,.panel{background:white;border:1px solid var(--line);border-radius:11px;padding:16px;box-shadow:0 2px 8px #14243a08}
.metric{font-size:27px;font-weight:800;margin-top:8px}h1{font-size:23px;margin:0 0 6px}h2{font-size:17px;margin:0 0 13px}
.btn{display:inline-block;background:var(--blue);color:white;border:0;padding:10px 13px;border-radius:7px;text-decoration:none;cursor:pointer;font-size:13px}
.btn.gray{background:#475569}.actions{display:flex;gap:8px;align-items:center;margin:14px 0;flex-wrap:wrap}
table{width:100%;border-collapse:collapse;background:white;font-size:12px}th,td{padding:10px;border-bottom:1px solid var(--line);text-align:left;vertical-align:top}th{background:#f8fafc;color:#475569}
label{font-size:12px;color:#475569;display:block;margin-bottom:5px}input,select,textarea{width:100%;padding:10px;border:1px solid #cbd5e1;border-radius:7px;background:white}textarea{min-height:75px}
form.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(205px,1fr));gap:12px}
.flash{padding:10px 12px;background:#eff6ff;border:1px solid #bfdbfe;border-radius:7px;margin-bottom:12px}
.low{color:#b91c1c;font-weight:bold}.plant-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:12px}
.plant-card{border-left:4px solid #2563eb;background:#fff;padding:14px;border-radius:9px;border:1px solid var(--line)}
@media(max-width:780px){.layout{display:block}nav{width:100%;display:flex;overflow:auto;padding:6px}nav a{white-space:nowrap}main{padding:14px}header{padding:12px}}
</style></head><body>
<header><div><div class="brand">⚙ FIX PLANT MONITORING REPORT</div><div class="sub">PT EQUALINDO MAKMUR ALAM SEJAHTERA</div></div>
<div style="font-size:12px">{% if session.get('auth') %}<a href="/logout" style="color:white">Logout</a>{% endif %}</div></header>
<div class="layout">{% if session.get('auth') %}<nav>
<a href="/">▦ Dashboard</a><a href="/plant-monitoring">▣ Plant Monitoring</a><a href="/equipment">⚙ Equipment</a><a href="/workorders">🔧 Work Orders</a><a href="/pm">◷ Preventive Maintenance</a><a href="/inventory">▤ Inventory</a><a href="/suppliers">♙ Suppliers</a><a href="/activities">☷ Activity Log</a><a href="/analytics">▥ Maintenance Analytics</a><a href="/report">⇩ PDF Report</a>
</nav>{% endif %}<main>
{% with messages=get_flashed_messages() %}{% for m in messages %}<div class="flash">{{m}}</div>{% endfor %}{% endwith %}
{{body|safe}}</main></div></body></html>
"""
LOGIN_BODY = r"""<div class="panel" style="max-width:390px;margin:7vh auto"><h1>FIX PLANT MONITORING REPORT</h1><p class="muted">PT EQUALINDO MAKMUR ALAM SEJAHTERA</p><form method="post"><label>Username</label><input name="username" required><br><br><label>Password</label><input type="password" name="password" required><br><br><button class="btn">Login</button></form></div>"""

def render(title, body):
    return render_template_string(TEMPLATE, title=title, body=body)

def plant_select(name="plant", selected=None):
    return '<div><label>Plant</label><select name="%s" required>%s</select></div>' % (name, ''.join(f'<option {"selected" if p==selected else ""}>{p}</option>' for p in PLANTS))

def field(label, name, typ="text", required=False, value="", options=None):
    req = "required" if required else ""
    if options:
        control = f'<select name="{name}" {req}>' + ''.join(f'<option value="{v}" {"selected" if str(v)==str(value) else ""}>{v}</option>' for v in options) + '</select>'
    elif typ == "textarea":
        control = f'<textarea name="{name}" {req}>{value}</textarea>'
    else:
        control = f'<input type="{typ}" name="{name}" value="{value}" {req}>'
    return f'<div><label>{label}</label>{control}</div>'

def form_page(title, fields, back):
    body=f'<h1>{title}</h1><div class="panel"><form method="post" class="grid">{fields}<div><button class="btn">Simpan</button> <a class="btn gray" href="{back}">Kembali</a></div></form></div>'
    return render(title, body)

def table_page(title, headers, rows, add_url, add_text="Tambah Data", extra=""):
    head=''.join(f'<th>{h}</th>' for h in headers)
    trs=''.join('<tr>'+''.join(f'<td>{v}</td>' for v in row)+'</tr>' for row in rows)
    body=f'<h1>{title}</h1>{extra}<div class="actions"><a class="btn" href="{add_url}">+ {add_text}</a></div><div class="panel" style="overflow:auto"><table><thead><tr>{head}</tr></thead><tbody>{trs or "<tr><td colspan=20>Belum ada data.</td></tr>"}</tbody></table></div>'
    return render(title, body)

@app.route("/")
def dashboard():
    wos=WorkOrder.query
    total_eq=Equipment.query.count()
    wo_count=wos.count()
    open_count=wos.filter(WorkOrder.status!="Closed").count()
    down=float(db.session.query(func.coalesce(func.sum(WorkOrder.downtime),0)).scalar() or 0)
    pm_count=PMPlan.query.filter(PMPlan.status=="Scheduled").count()
    low=Inventory.query.filter(Inventory.stock<=Inventory.min_stock).count()
    cards=[("Equipment Terdaftar",total_eq),("Total Work Order",wo_count),("Open Work Order",open_count),("Downtime (jam)",f"{down:.1f}"),("PM Terjadwal",pm_count),("Stok Minimum",low)]
    card_html=''.join(f'<div class="card">{k}<div class="metric">{v}</div></div>' for k,v in cards)
    plants=[]
    for p in PLANTS:
        p_eq=Equipment.query.filter_by(plant=p).count()
        p_wo=WorkOrder.query.filter_by(plant=p).count()
        p_open=WorkOrder.query.filter_by(plant=p).filter(WorkOrder.status!="Closed").count()
        plants.append(f'<div class="plant-card"><b>{p}</b><p class="muted">Equipment: {p_eq} · WO: {p_wo} · Open: {p_open}</p><a href="/plant-monitoring?plant={p}" class="btn gray">Lihat Monitoring</a></div>')
    body=f'<h1>Dashboard Management</h1><div class="muted">Monitoring terpusat empat plant PT EQUALINDO MAKMUR ALAM SEJAHTERA</div><div class="cards">{card_html}</div><h2>Plant Overview</h2><div class="plant-grid">{"".join(plants)}</div><div class="actions"><a class="btn" href="/workorders/new">+ Buat Work Order</a><a class="btn gray" href="/equipment/new">+ Tambah Equipment</a><a class="btn gray" href="/pm/new">+ Jadwalkan PM</a></div>'
    return render("Dashboard",body)

@app.route("/plant-monitoring")
def plant_monitoring():
    selected=request.args.get("plant","ALL")
    if selected not in PLANTS and selected!="ALL": selected="ALL"
    eq=Equipment.query if selected=="ALL" else Equipment.query.filter_by(plant=selected)
    wo=WorkOrder.query if selected=="ALL" else WorkOrder.query.filter_by(plant=selected)
    pm=PMPlan.query if selected=="ALL" else PMPlan.query.filter_by(plant=selected)
    rows=[]
    for p in ([selected] if selected!="ALL" else PLANTS):
        nwo=WorkOrder.query.filter_by(plant=p).count()
        op=WorkOrder.query.filter_by(plant=p).filter(WorkOrder.status!="Closed").count()
        hrs=db.session.query(func.coalesce(func.sum(WorkOrder.downtime),0)).filter_by(plant=p).scalar() or 0
        rows.append([p,Equipment.query.filter_by(plant=p).count(),nwo,op,f"{float(hrs):.1f}",PMPlan.query.filter_by(plant=p).filter_by(status="Scheduled").count()])
    opts='<option value="ALL">SEMUA PLANT</option>'+''.join(f'<option {"selected" if selected==p else ""}>{p}</option>' for p in PLANTS)
    extra=f'<form method="get" class="actions"><select name="plant" style="max-width:260px">{opts}</select><button class="btn">Filter Plant</button></form>'
    return table_page("Plant Monitoring",["Plant","Equipment","Total WO","Open WO","Downtime (jam)","PM Scheduled"],rows,"/workorders/new","Buat Work Order",extra)

@app.route("/equipment")
def equipment():
    rows=[[e.plant,e.code,e.name,e.area,e.category,e.criticality,e.status] for e in Equipment.query.order_by(Equipment.plant,Equipment.code).all()]
    return table_page("Equipment Database",["Plant","Code","Equipment","Area","Category","Criticality","Status"],rows,"/equipment/new")
@app.route("/equipment/new",methods=["GET","POST"])
def equipment_new():
    if request.method=="POST":
        try:
            db.session.add(Equipment(plant=request.form["plant"],code=request.form["code"],name=request.form["name"],area=request.form.get("area",""),category=request.form.get("category",""),criticality=request.form.get("criticality","Medium"),status=request.form.get("status","RFU")))
            db.session.commit(); flash("Equipment berhasil ditambahkan."); return redirect("/equipment")
        except Exception: db.session.rollback(); flash("Gagal menyimpan. Pastikan Equipment Code unik.")
    f=plant_select()+field("Equipment Code","code",required=True)+field("Equipment Name","name",required=True)+field("Area","area")+field("Category","category")+field("Criticality","criticality",options=["Low","Medium","High","Critical"])+field("Status","status",options=["RFU","BD","Standby"])
    return form_page("Tambah Equipment",f,"/equipment")

@app.route("/workorders")
def workorders():
    rows=[[w.wo_no,str(w.reported),w.plant,w.equipment_code,w.problem,w.priority,w.status,f"{w.downtime:.1f}",w.technician] for w in WorkOrder.query.order_by(WorkOrder.id.desc()).all()]
    return table_page("Work Orders / Breakdown",["WO No","Date","Plant","Equipment","Problem","Priority","Status","Downtime h","PIC"],rows,"/workorders/new","Buat Work Order")
@app.route("/workorders/new",methods=["GET","POST"])
def wo_new():
    if request.method=="POST":
        try:
            w=WorkOrder(wo_no=request.form["wo_no"],reported=date.fromisoformat(request.form["reported"]),plant=request.form["plant"],equipment_code=request.form["equipment_code"],problem=request.form["problem"],priority=request.form.get("priority","Medium"),status=request.form.get("status","Open"),action=request.form.get("action",""),technician=request.form.get("technician",""),downtime=float(request.form.get("downtime") or 0))
            db.session.add(w); db.session.commit(); flash("Work Order tersimpan."); return redirect("/workorders")
        except Exception: db.session.rollback(); flash("Gagal menyimpan. Pastikan WO No unik dan data benar.")
    f=field("WO Number","wo_no",required=True)+field("Tanggal Laporan","reported","date",True,date.today().isoformat())+plant_select()+field("Equipment Code","equipment_code",required=True)+field("Problem / Kerusakan","problem","textarea",True)+field("Priority","priority",options=["Low","Medium","High","Critical"])+field("Status","status",options=["Open","In Progress","Waiting Spare Part","Closed"])+field("Technician / PIC","technician")+field("Downtime (jam)","downtime","number")+field("Action Taken","action","textarea")
    return form_page("Buat Work Order",f,"/workorders")

@app.route("/pm")
def pm():
    rows=[[p.plant,p.equipment_code,p.task,p.frequency,str(p.due_date),p.pic,p.status] for p in PMPlan.query.order_by(PMPlan.due_date).all()]
    return table_page("Preventive Maintenance",["Plant","Equipment","Task","Frequency","Due Date","PIC","Status"],rows,"/pm/new","Tambah Jadwal PM")
@app.route("/pm/new",methods=["GET","POST"])
def pm_new():
    if request.method=="POST":
        try:
            db.session.add(PMPlan(plant=request.form["plant"],equipment_code=request.form["equipment_code"],task=request.form["task"],frequency=request.form.get("frequency","Monthly"),due_date=date.fromisoformat(request.form["due_date"]),pic=request.form.get("pic",""),status=request.form.get("status","Scheduled"),remarks=request.form.get("remarks","")))
            db.session.commit(); flash("Jadwal PM tersimpan."); return redirect("/pm")
        except Exception: db.session.rollback(); flash("Gagal menyimpan PM.")
    f=plant_select()+field("Equipment Code","equipment_code",required=True)+field("PM Task","task",required=True)+field("Frequency","frequency",options=["Daily","Weekly","Monthly","Quarterly","Semiannual","Annual"])+field("Due Date","due_date","date",True,date.today().isoformat())+field("PIC","pic")+field("Status","status",options=["Scheduled","Completed","Overdue"])+field("Remarks","remarks","textarea")
    return form_page("Tambah Jadwal PM",f,"/pm")

@app.route("/inventory")
def inventory():
    rows=[]
    for i in Inventory.query.order_by(Inventory.plant,Inventory.item).all():
        qty=f'<span class="{"low" if i.stock<=i.min_stock else ""}">{i.stock:g}</span>'
        rows.append([i.plant,i.item,i.part_no,i.unit,qty,f"{i.min_stock:g}",i.location])
    extra='<div class="actions"><a class="btn gray" href="/inventory/transaction">Transaksi IN / OUT</a></div>'
    return table_page("Inventory / Spare Part",["Plant","Item","Part No","Unit","Stock","Min Stock","Location"],rows,"/inventory/new","Tambah Item",extra)
@app.route("/inventory/new",methods=["GET","POST"])
def inv_new():
    if request.method=="POST":
        try:
            db.session.add(Inventory(plant=request.form["plant"],item=request.form["item"],part_no=request.form.get("part_no",""),unit=request.form.get("unit","pcs"),stock=float(request.form.get("stock") or 0),min_stock=float(request.form.get("min_stock") or 0),location=request.form.get("location","")))
            db.session.commit(); flash("Item inventory tersimpan."); return redirect("/inventory")
        except Exception: db.session.rollback(); flash("Gagal menyimpan item.")
    f=plant_select()+field("Nama Barang","item",required=True)+field("Part Number","part_no")+field("Unit","unit")+field("Initial Stock","stock","number")+field("Minimum Stock","min_stock","number")+field("Storage Location","location")
    return form_page("Tambah Spare Part",f,"/inventory")
@app.route("/inventory/transaction",methods=["GET","POST"])
def inv_trx():
    items=Inventory.query.order_by(Inventory.plant,Inventory.item).all()
    if request.method=="POST":
        try:
            item=Inventory.query.get(int(request.form["item_id"])); qty=float(request.form["qty"]); typ=request.form["trx_type"]
            if typ=="OUT" and item.stock<qty: flash("Stok tidak mencukupi."); return redirect("/inventory/transaction")
            item.stock += qty if typ=="IN" else -qty
            db.session.add(StockTransaction(item_id=item.id,trx_type=typ,qty=qty,person=request.form.get("person",""),reference=request.form.get("reference","")))
            db.session.commit(); flash("Transaksi stok berhasil."); return redirect("/inventory")
        except Exception: db.session.rollback(); flash("Transaksi gagal.")
    opts=''.join(f'<option value="{i.id}">{i.plant} — {i.item} (stok {i.stock:g})</option>' for i in items)
    f=f'<div><label>Item</label><select name="item_id">{opts}</select></div>'+field("Jenis","trx_type",options=["IN","OUT"])+field("Quantity","qty","number",True)+field("Person","person")+field("Reference / WO","reference")
    return form_page("Transaksi Spare Part",f,"/inventory")

@app.route("/suppliers")
def suppliers():
    rows=[[s.name,s.contact,s.phone,s.email,s.address] for s in Supplier.query.order_by(Supplier.name).all()]
    return table_page("Supplier Database",["Supplier","Contact","Phone","Email","Address"],rows,"/suppliers/new")
@app.route("/suppliers/new",methods=["GET","POST"])
def supplier_new():
    if request.method=="POST":
        db.session.add(Supplier(name=request.form["name"],contact=request.form.get("contact",""),phone=request.form.get("phone",""),email=request.form.get("email",""),address=request.form.get("address",""))); db.session.commit(); flash("Supplier tersimpan."); return redirect("/suppliers")
    f=field("Supplier Name","name",required=True)+field("Contact Person","contact")+field("Phone","phone")+field("Email","email","email")+field("Address","address","textarea")
    return form_page("Tambah Supplier",f,"/suppliers")

@app.route("/activities")
def activities():
    rows=[[str(a.activity_date),a.plant,a.equipment_code,a.description,a.person,a.remarks] for a in Activity.query.order_by(Activity.id.desc()).all()]
    return table_page("Maintenance Activity Log",["Date","Plant","Equipment","Activity","Person","Remarks"],rows,"/activities/new")
@app.route("/activities/new",methods=["GET","POST"])
def activity_new():
    if request.method=="POST":
        db.session.add(Activity(activity_date=date.fromisoformat(request.form["activity_date"]),plant=request.form["plant"],equipment_code=request.form.get("equipment_code",""),description=request.form["description"],person=request.form.get("person",""),remarks=request.form.get("remarks",""))); db.session.commit(); flash("Activity tersimpan."); return redirect("/activities")
    f=field("Date","activity_date","date",True,date.today().isoformat())+plant_select()+field("Equipment Code","equipment_code")+field("Activity Description","description","textarea",True)+field("Person","person")+field("Remarks","remarks","textarea")
    return form_page("Tambah Activity",f,"/activities")

@app.route("/analytics")
def analytics():
    total=WorkOrder.query.count()
    downtime=float(db.session.query(func.coalesce(func.sum(WorkOrder.downtime),0)).scalar() or 0)
    rows=[]
    for p in PLANTS:
        count=WorkOrder.query.filter_by(plant=p).count()
        hours=float(db.session.query(func.coalesce(func.sum(WorkOrder.downtime),0)).filter_by(plant=p).scalar() or 0)
        rows.append([p,count,f"{hours:.1f}",f"{(hours/count):.2f}" if count else "0.00"])
    body=f'<h1>Maintenance Analytics</h1><div class="muted">Ringkasan berdasarkan Work Order yang tercatat. MTTR sederhana = total downtime / jumlah WO; MTBF memerlukan data jam operasi equipment.</div><div class="cards"><div class="card">Total WO<div class="metric">{total}</div></div><div class="card">Total Downtime<div class="metric">{downtime:.1f} jam</div></div></div><div class="panel" style="overflow:auto"><h2>Perbandingan Antar Plant</h2><table><tr><th>Plant</th><th>Breakdown / WO</th><th>Downtime (jam)</th><th>Rata-rata downtime per WO (jam)</th></tr>{''.join(f"<tr>{''.join(f'<td>{v}</td>' for v in r)}</tr>" for r in rows)}</table></div>'
    return render("Analytics",body)

@app.route("/report")
def report():
    plant=request.args.get("plant","ALL")
    q=WorkOrder.query
    if plant in PLANTS: q=q.filter_by(plant=plant)
    data=q.order_by(WorkOrder.reported.desc()).all()
    buf=BytesIO(); doc=SimpleDocTemplate(buf,pagesize=landscape(A4))
    styles=getSampleStyleSheet()
    story=[Paragraph(APP_NAME,styles["Title"]),Paragraph(COMPANY,styles["Heading2"]),Paragraph("Work Order Report — "+plant,styles["Normal"]),Spacer(1,12)]
    rows=[["WO No","Date","Plant","Equipment","Problem","Priority","Status","Downtime h","PIC"]]
    for w in data: rows.append([w.wo_no,str(w.reported),w.plant,w.equipment_code,w.problem[:65],w.priority,w.status,str(w.downtime),w.technician])
    t=Table(rows,repeatRows=1,colWidths=[60,55,95,65,185,55,70,65,75])
    t.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),colors.HexColor("#1d314d")),("TEXTCOLOR",(0,0),(-1,0),colors.white),("GRID",(0,0),(-1,-1),.4,colors.grey),("FONTSIZE",(0,0),(-1,-1),7),("VALIGN",(0,0),(-1,-1),"TOP"),("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.white,colors.HexColor("#f1f5f9")])]))
    story.append(t); doc.build(story); buf.seek(0)
    return send_file(buf,as_attachment=True,download_name="Fix_Plant_Monitoring_Report.pdf",mimetype="application/pdf")

with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT",5000)))

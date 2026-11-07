"""CENTER OF EXCELLENCE - School Management System (Flask + SQLite)."""
import io
import os
import re
import secrets
import sqlite3
from functools import wraps

from flask import (Flask, abort, flash, g, jsonify, redirect, render_template,
                   request, send_file, session, url_for)
from openpyxl import Workbook, load_workbook
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from werkzeug.security import check_password_hash, generate_password_hash

BASE = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE, "school.db")
LOGO = os.path.join(BASE, "static", "logo.png")
SCHOOL = "CENTER OF EXCELLENCE"

app = Flask(__name__)
_key_file = os.path.join(BASE, ".secret_key")
if not os.path.exists(_key_file):
    with open(_key_file, "w") as f:
        f.write(secrets.token_hex(32))
with open(_key_file) as f:
    app.secret_key = f.read().strip()
app.config.update(SESSION_COOKIE_SAMESITE="Lax", SESSION_COOKIE_HTTPONLY=True,
                  MAX_CONTENT_LENGTH=5 * 1024 * 1024)

SCHEMA = """
CREATE TABLE IF NOT EXISTS users(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  role TEXT NOT NULL CHECK(role IN ('teacher','student','admin')),
  uid TEXT NOT NULL UNIQUE,
  name TEXT NOT NULL,
  subject TEXT,
  class_section TEXT,      -- student: one section; teacher: comma separated list
  father TEXT,
  mobile TEXT,
  email TEXT,
  password_hash TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'Pending' CHECK(status IN ('Pending','Approved','Blocked'))
);
CREATE TABLE IF NOT EXISTS classes(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  label TEXT NOT NULL UNIQUE      -- e.g. 9th-B
);
CREATE TABLE IF NOT EXISTS results(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  student_uid TEXT NOT NULL,
  student_name TEXT NOT NULL,
  subject TEXT NOT NULL,
  teacher_uid TEXT NOT NULL,
  total REAL NOT NULL,
  obtained REAL NOT NULL,
  UNIQUE(student_uid, subject)
);
"""


def db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(_):
    d = g.pop("db", None)
    if d:
        d.close()


def init_db():
    con = sqlite3.connect(DB_PATH)
    con.executescript(SCHEMA)
    if not con.execute("SELECT 1 FROM users WHERE role='admin'").fetchone():
        pw = os.environ.get("ADMIN_PASSWORD", "admin123")
        con.execute("INSERT INTO users(role,uid,name,password_hash,status) VALUES('admin','admin','Administrator',?,'Approved')",
                    (generate_password_hash(pw),))
        print(f"Created default admin -> ID: admin  Password: {pw}  (set ADMIN_PASSWORD before first run to change)")
    if not con.execute("SELECT 1 FROM classes").fetchone():
        con.executemany("INSERT INTO classes(label) VALUES(?)",
                        [("9th-A",), ("9th-B",), ("10th-A",), ("10th-B",)])
    con.commit()
    con.close()


# ---------- helpers ----------
GRADES = ["A+", "A", "B", "C", "D", "F"]


def grade(p):
    for cut, g_ in ((90, "A+"), (80, "A"), (70, "B"), (60, "C"), (50, "D")):
        if p >= cut:
            return g_
    return "F"


def pct(o, t):
    return round(o / t * 100, 1) if t else 0.0


def current_user():
    uid = session.get("uid")
    if not uid:
        return None
    u = db().execute("SELECT * FROM users WHERE uid=?", (uid,)).fetchone()
    if not u or u["status"] != "Approved":
        session.clear()
        return None
    return u


def login_required(*roles):
    def deco(fn):
        @wraps(fn)
        def inner(*a, **kw):
            u = current_user()
            if not u or u["role"] not in roles:
                return redirect(url_for("admin_login" if "admin" in roles else "login"))
            g.user = u
            return fn(*a, **kw)
        return inner
    return deco


def class_labels():
    return [r["label"] for r in db().execute("SELECT label FROM classes ORDER BY label")]


@app.context_processor
def inject():
    return {"school": SCHOOL, "me": current_user()}


# ---------- registration ----------
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


@app.route("/", methods=["GET", "POST"])
@app.route("/register", methods=["GET", "POST"])
def register():
    tab = request.values.get("tab", "teacher")
    if tab not in ("teacher", "student"):
        tab = "teacher"
    if request.method == "POST":
        f = {k: request.form.get(k, "").strip() for k in
             ("uid", "name", "subject", "mobile", "email", "father", "class_section", "password", "confirm")}
        sections = request.form.getlist("sections")
        valid = set(class_labels())
        errs = []
        if not f["uid"]:
            errs.append("ID is required.")
        if not f["name"]:
            errs.append("Full name is required.")
        if not re.fullmatch(r"[0-9+\-\s]{7,15}", f["mobile"]):
            errs.append("Enter a valid mobile number.")
        if not EMAIL_RE.match(f["email"]):
            errs.append("Enter a valid email.")
        if len(f["password"]) < 6:
            errs.append("Password must be at least 6 characters.")
        if f["password"] != f["confirm"]:
            errs.append("Passwords do not match.")
        if tab == "teacher":
            if not f["subject"]:
                errs.append("Subject is required.")
            sections = [s for s in sections if s in valid]
            if not sections:
                errs.append("Select at least one class / section.")
        else:
            if not f["father"]:
                errs.append("Father name is required.")
            if f["class_section"] not in valid:
                errs.append("Select a valid class / section.")
        if f["uid"].lower() == "admin" or db().execute("SELECT 1 FROM users WHERE uid=?", (f["uid"],)).fetchone():
            errs.append("This ID is already registered.")
        if errs:
            for e in errs:
                flash(e, "error")
            return render_template("register.html", tab=tab, classes=class_labels(), form=f, sel=sections), 400
        db().execute(
            "INSERT INTO users(role,uid,name,subject,class_section,father,mobile,email,password_hash) VALUES(?,?,?,?,?,?,?,?,?)",
            (tab, f["uid"], f["name"], f["subject"] if tab == "teacher" else None,
             ",".join(sections) if tab == "teacher" else f["class_section"],
             f["father"] if tab == "student" else None, f["mobile"], f["email"],
             generate_password_hash(f["password"])))
        db().commit()
        flash("Registration submitted. Your account is waiting for Admin approval.", "ok")
        return redirect(url_for("register", tab=tab))
    return render_template("register.html", tab=tab, classes=class_labels(), form={}, sel=[])


@app.route("/api/users")
def api_users():
    """Public live table: role, id, name, class/subject, status. No secrets."""
    rows = db().execute("SELECT id,role,uid,name,subject,class_section,status FROM users WHERE role!='admin' ORDER BY id DESC").fetchall()
    u = current_user()
    is_admin = bool(u and u["role"] == "admin")
    out = [{"id": r["id"], "role": r["role"].capitalize(), "uid": r["uid"], "name": r["name"],
            "info": (r["subject"] + " (" + r["class_section"] + ")") if r["role"] == "teacher" else r["class_section"],
            "status": r["status"]} for r in rows]
    resp = jsonify(users=out, admin=is_admin)
    resp.headers["Cache-Control"] = "no-store"
    return resp


# ---------- auth ----------
@app.route("/login", methods=["GET", "POST"])
def login():
    role = request.values.get("role", "teacher")
    if role not in ("teacher", "student"):
        role = "teacher"
    if request.method == "POST":
        return do_login(role)
    return render_template("login.html", role=role, admin=False)


@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        return do_login("admin")
    return render_template("login.html", role="admin", admin=True)


def do_login(role):
    uid = request.form.get("uid", "").strip()
    pw = request.form.get("password", "")
    u = db().execute("SELECT * FROM users WHERE uid=? AND role=?", (uid, role)).fetchone()
    if not u or not check_password_hash(u["password_hash"], pw):
        flash("Invalid ID or password.", "error")
    elif u["status"] == "Pending":
        flash("Your account is still pending Admin approval.", "error")
    elif u["status"] == "Blocked":
        flash("Your account has been blocked. Contact the Admin.", "error")
    else:
        session.clear()
        session["uid"] = u["uid"]
        return redirect(url_for({"teacher": "teacher_dash", "student": "student_dash", "admin": "admin_dash"}[role]))
    return redirect(url_for("admin_login") if role == "admin" else url_for("login", role=role))


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# ---------- teacher ----------
def teacher_sections(u):
    return [s for s in (u["class_section"] or "").split(",") if s]


def save_result(teacher, roll, total, obtained):
    """Upsert one result row for the teacher's subject. Returns an error string or None."""
    s = db().execute("SELECT * FROM users WHERE role='student' AND uid=?", (roll,)).fetchone()
    if not s:
        return f"Roll No {roll or '(blank)'}: no such student."
    if s["class_section"] not in teacher_sections(teacher):
        return f"Roll No {roll}: student is not in your sections."
    try:
        t, o = float(total), float(obtained)
    except (TypeError, ValueError):
        return f"Roll No {roll}: marks must be numbers."
    if not (t > 0 and 0 <= o <= t):
        return f"Roll No {roll}: obtained marks must be between 0 and total."
    db().execute(
        """INSERT INTO results(student_uid,student_name,subject,teacher_uid,total,obtained) VALUES(?,?,?,?,?,?)
           ON CONFLICT(student_uid,subject) DO UPDATE SET total=excluded.total, obtained=excluded.obtained,
           teacher_uid=excluded.teacher_uid, student_name=excluded.student_name""",
        (roll, s["name"], teacher["subject"], teacher["uid"], t, o))
    return None


@app.route("/teacher")
@login_required("teacher")
def teacher_dash():
    u = g.user
    secs = teacher_sections(u)
    ph = ",".join("?" * len(secs)) or "''"
    students = db().execute(
        f"SELECT * FROM users WHERE role='student' AND class_section IN ({ph}) ORDER BY class_section, uid", secs).fetchall()
    rows = db().execute("""SELECT r.*, s.class_section FROM results r LEFT JOIN users s ON s.uid=r.student_uid
                           WHERE r.teacher_uid=? ORDER BY s.class_section, r.student_uid""", (u["uid"],)).fetchall()
    res = [dict(r, pct=pct(r["obtained"], r["total"]), grade=grade(pct(r["obtained"], r["total"]))) for r in rows]
    dist = {x: 0 for x in GRADES}
    sec_acc = {}
    for r in res:
        dist[r["grade"]] += 1
        sec_acc.setdefault(r["class_section"], []).append(r["pct"])
    avg = round(sum(r["pct"] for r in res) / len(res), 1) if res else None
    sec_avg = {k: round(sum(v) / len(v), 1) for k, v in sorted(sec_acc.items())}
    return render_template("teacher.html", u=u, secs=secs, students=students, res=res,
                           avg=avg, dist=dist, sec_avg=sec_avg)


@app.post("/teacher/result")
@login_required("teacher")
def teacher_manual():
    err = save_result(g.user, request.form.get("roll", "").strip(),
                      request.form.get("total"), request.form.get("obtained"))
    if err:
        flash(err, "error")
    else:
        db().commit()
        flash("Result saved.", "ok")
    return redirect(url_for("teacher_dash") + "#upload")


@app.post("/teacher/upload")
@login_required("teacher")
def teacher_upload():
    back = url_for("teacher_dash") + "#upload"
    f = request.files.get("file")
    if not f or not f.filename.lower().endswith(".xlsx"):
        flash("Please choose an .xlsx Excel file.", "error")
        return redirect(back)
    try:
        rows = list(load_workbook(f, read_only=True, data_only=True).active.iter_rows(values_only=True))
    except Exception:
        flash("Could not read that Excel file.", "error")
        return redirect(back)
    head = [str(c or "").strip().lower() for c in (rows[0] if rows else [])]
    try:
        i_roll = next(i for i, h in enumerate(head) if "roll" in h)
        i_tot = next(i for i, h in enumerate(head) if "total" in h)
        i_obt = next(i for i, h in enumerate(head) if "obtain" in h)
    except StopIteration:
        flash("Header row must contain: Student Name, Roll No, Total Marks, Obtained Marks.", "error")
        return redirect(back)
    ok, errs = 0, []
    for r in rows[1:]:
        if not r or all(c in (None, "") for c in r):
            continue
        roll = str(r[i_roll]).strip() if r[i_roll] is not None else ""
        e = save_result(g.user, roll, r[i_tot], r[i_obt])
        if e:
            errs.append(e)
        else:
            ok += 1
    db().commit()
    flash(f"{ok} result(s) imported.", "ok")
    for e in errs[:10]:
        flash(e, "error")
    if len(errs) > 10:
        flash(f"...and {len(errs) - 10} more rows skipped.", "error")
    return redirect(back)


@app.post("/teacher/result/<int:rid>/delete")
@login_required("teacher")
def teacher_del(rid):
    db().execute("DELETE FROM results WHERE id=? AND teacher_uid=?", (rid, g.user["uid"]))
    db().commit()
    return redirect(url_for("teacher_dash") + "#upload")


@app.route("/teacher/template.xlsx")
@login_required("teacher")
def template_xlsx():
    wb = Workbook()
    ws = wb.active
    ws.append(["Student Name", "Roll No", "Total Marks", "Obtained Marks"])
    ws.append(["Ali Ahmed", "S-201", 100, 85])
    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return send_file(buf, as_attachment=True, download_name="results_template.xlsx")


# ---------- student ----------
def student_report(uid):
    s = db().execute("SELECT * FROM users WHERE role='student' AND uid=?", (uid,)).fetchone()
    if not s:
        abort(404)
    rows = db().execute("SELECT * FROM results WHERE student_uid=? ORDER BY subject", (uid,)).fetchall()
    subs = [dict(r, pct=pct(r["obtained"], r["total"]), grade=grade(pct(r["obtained"], r["total"]))) for r in rows]
    T, O = sum(r["total"] for r in subs), sum(r["obtained"] for r in subs)
    p = pct(O, T)
    return s, subs, T, O, p, (grade(p) if subs else "-")


@app.route("/student")
@login_required("student")
def student_dash():
    s, subs, T, O, p, gr = student_report(g.user["uid"])
    return render_template("student.html", s=s, subs=subs, T=T, O=O, p=p, gr=gr)


def _esc(x):
    return str(x).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


@app.route("/report/<uid>.pdf")
def report_pdf(uid):
    u = current_user()
    if not u or not (u["role"] == "admin" or (u["role"] == "student" and u["uid"] == uid)):
        abort(403)
    s, subs, T, O, p, gr = student_report(uid)
    navy = colors.HexColor("#1e3a8a")
    styles = getSampleStyleSheet()
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, topMargin=48 * mm, bottomMargin=20 * mm,
                            title=f"Result - {s['name']}")

    def page(c, d):
        w, h = A4
        c.saveState()  # watermark: faded logo + diagonal school name
        c.setFillAlpha(0.07)
        c.drawImage(ImageReader(LOGO), w / 2 - 70 * mm, h / 2 - 70 * mm, 140 * mm, 140 * mm, mask="auto")
        c.translate(w / 2, h / 2)
        c.rotate(35)
        c.setFont("Helvetica-Bold", 44)
        c.setFillColor(navy)
        c.drawCentredString(0, -10, SCHOOL)
        c.restoreState()
        c.saveState()  # header
        c.drawImage(ImageReader(LOGO), 20 * mm, h - 38 * mm, 22 * mm, 22 * mm, mask="auto")
        c.setFont("Helvetica-Bold", 20)
        c.setFillColor(navy)
        c.drawString(47 * mm, h - 26 * mm, SCHOOL)
        c.setFont("Helvetica", 10)
        c.setFillColor(colors.grey)
        c.drawString(47 * mm, h - 33 * mm, "Official Result Card")
        c.setStrokeColor(navy)
        c.line(20 * mm, h - 41 * mm, w - 20 * mm, h - 41 * mm)
        c.restoreState()

    el = [Paragraph(f"<b>Student Name:</b> {_esc(s['name'])} &nbsp;|&nbsp; <b>Roll No:</b> {_esc(s['uid'])}", styles["Normal"]),
          Spacer(1, 2 * mm),
          Paragraph(f"<b>Class / Section:</b> {_esc(s['class_section'])} &nbsp;|&nbsp; <b>Father Name:</b> {_esc(s['father'] or '')}", styles["Normal"]),
          Spacer(1, 8 * mm)]
    data = [["Subject", "Total", "Obtained", "%", "Grade"]]
    data += [[r["subject"], f"{r['total']:g}", f"{r['obtained']:g}", f"{r['pct']}%", r["grade"]] for r in subs]
    data.append(["TOTAL", f"{T:g}", f"{O:g}", f"{p}%", gr])
    t = Table(data, colWidths=[70 * mm, 25 * mm, 25 * mm, 25 * mm, 25 * mm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), navy), ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"), ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
        ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#e0e7ff")),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey), ("ALIGN", (1, 0), (-1, -1), "CENTER"),
        ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 6)]))
    el.append(t)
    if not subs:
        el += [Spacer(1, 6 * mm), Paragraph("No results have been uploaded yet.", styles["Normal"])]
    doc.build(el, onFirstPage=page, onLaterPages=page)
    buf.seek(0)
    return send_file(buf, mimetype="application/pdf", download_name=f"result_{uid}.pdf",
                     as_attachment=request.args.get("dl") == "1")


# ---------- admin ----------
@app.route("/admin")
@login_required("admin")
def admin_dash():
    stats = []
    for t in db().execute("SELECT * FROM users WHERE role='teacher' ORDER BY uid").fetchall():
        rs = db().execute("SELECT total,obtained FROM results WHERE teacher_uid=?", (t["uid"],)).fetchall()
        avg = round(sum(pct(r["obtained"], r["total"]) for r in rs) / len(rs), 1) if rs else None
        stats.append({"uid": t["uid"], "name": t["name"], "subject": t["subject"], "n": len(rs), "avg": avg})
    rows = db().execute("""SELECT r.*, s.class_section, t.name AS tname FROM results r
        LEFT JOIN users s ON s.uid=r.student_uid LEFT JOIN users t ON t.uid=r.teacher_uid
        ORDER BY s.class_section, r.student_uid, r.subject""").fetchall()
    res = [dict(r, pct=pct(r["obtained"], r["total"]), grade=grade(pct(r["obtained"], r["total"]))) for r in rows]
    classes = db().execute("SELECT * FROM classes ORDER BY label").fetchall()
    return render_template("admin.html", stats=stats, res=res, classes=classes)


@app.post("/admin/user/<int:user_id>/<action>")
@login_required("admin")
def admin_user(user_id, action):
    u = db().execute("SELECT * FROM users WHERE id=? AND role!='admin'", (user_id,)).fetchone()
    if not u:
        return jsonify(ok=False), 404
    if action == "delete":
        db().execute("DELETE FROM users WHERE id=?", (user_id,))
        if u["role"] == "student":
            db().execute("DELETE FROM results WHERE student_uid=?", (u["uid"],))
    elif action in ("approve", "block"):
        db().execute("UPDATE users SET status=? WHERE id=?", ("Approved" if action == "approve" else "Blocked", user_id))
    else:
        return jsonify(ok=False), 400
    db().commit()
    return jsonify(ok=True)


@app.post("/admin/class")
@login_required("admin")
def admin_class():
    cls = request.form.get("cls", "").strip()
    secs = [s.strip().upper() for s in request.form.get("sections", "").split(",") if s.strip()] or [""]
    if not cls or "," in cls:
        flash("Enter a class name (no commas).", "error")
    else:
        for s in secs:
            db().execute("INSERT OR IGNORE INTO classes(label) VALUES(?)", (f"{cls}-{s}" if s else cls,))
        db().commit()
        flash("Class / section saved.", "ok")
    return redirect(url_for("admin_dash") + "#classes")


@app.post("/admin/class/<int:cid>/delete")
@login_required("admin")
def admin_class_del(cid):
    row = db().execute("SELECT label FROM classes WHERE id=?", (cid,)).fetchone()
    if row and db().execute("SELECT 1 FROM users WHERE role!='admin' AND (',' || class_section || ',') LIKE ?",
                            (f"%,{row['label']},%",)).fetchone():
        flash("Cannot delete: users are assigned to this section.", "error")
    else:
        db().execute("DELETE FROM classes WHERE id=?", (cid,))
        db().commit()
    return redirect(url_for("admin_dash") + "#classes")


@app.post("/admin/result/<int:rid>/delete")
@login_required("admin")
def admin_result_del(rid):
    db().execute("DELETE FROM results WHERE id=?", (rid,))
    db().commit()
    return redirect(url_for("admin_dash") + "#results")


init_db()
if __name__ == "__main__":
    app.run(debug=False, port=5000)


from flask import Flask, request, session, redirect, url_for, render_template_string, flash
import controller
import model
from datetime import datetime

app = Flask(__name__)
app.secret_key = "dev-key-for-assignment"  # for demo only

# ---------- Templates (inline to keep one-file simplicity) ----------
LAYOUT = """
<!doctype html>
<html lang="th">
<head>
  <meta charset="utf-8">
  <title>{{ title or "Job Fair MVC (CSV)" }}</title>
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <style>
    body { font-family: system-ui, -apple-system, Segoe UI, Arial; margin: 20px; }
    header { display:flex; gap:12px; align-items:center; margin-bottom: 16px; }
    nav a { margin-right: 10px; }
    .card { border:1px solid #ddd; border-radius:10px; padding:12px; margin:10px 0; }
    .pill { padding:2px 8px; border-radius:999px; background:#eee; font-size:12px; }
    .pill.open { background:#d1fae5; }
    .pill.closed { background:#fee2e2; }
    table { border-collapse: collapse; width: 100%; }
    th, td { border-bottom: 1px solid #eee; padding: 8px; text-align: left; }
    .right { text-align:right; }
    .muted { color:#666; font-size: 12px; }
    .btn { display:inline-block; padding:6px 10px; border-radius:8px; border:1px solid #333; text-decoration:none; }
    .btn-primary { background:#111; color:white; }
    .flash { padding:8px 12px; border-radius:8px; background:#fff7ed; border:1px solid #fed7aa; margin:8px 0;}
  </style>
</head>
<body>
<header>
  <h2 style="margin:0;">Job Fair – MVC (CSV)</h2>
  <nav>
    {% if current_user %}
      <span class="muted">สวัสดี, {{ current_user.first_name }} {{ current_user.last_name }} ({{ current_user.role }})</span>
      <a href="{{ url_for('jobs') }}">ตำแหน่งงาน</a>
      {% if is_admin %}<a href="{{ url_for('admin_candidates') }}">ผู้สมัครทั้งหมด</a>{% endif %}
      <a href="{{ url_for('my_profile') }}">ประวัติของฉัน</a>
      <a href="{{ url_for('logout') }}">ออกจากระบบ</a>
    {% else %}
      <a href="{{ url_for('login') }}">เข้าสู่ระบบ</a>
    {% endif %}
  </nav>
</header>
{% for m in get_flashed_messages() %}
  <div class="flash">{{ m }}</div>
{% endfor %}
{{ body|safe }}
</body>
</html>
"""

def render(body, **ctx):
    user = session.get("user")
    is_admin = user and user.get("role","").upper() == "ADMIN"
    return render_template_string(LAYOUT, body=body, current_user=user, is_admin=is_admin, **ctx)

# ---------- Auth helpers ----------
def require_login():
    if "user" not in session:
        return redirect(url_for("login"))
    return None

def require_admin():
    redir = require_login()
    if redir: 
        return redir
    if session["user"]["role"].upper() != "ADMIN":
        flash("ต้องเป็นแอดมินเท่านั้น")
        return redirect(url_for("jobs"))
    return None

# ---------- Routes ----------
@app.route("/")
def home():
    # default landing depends on role
    if "user" not in session:
        return redirect(url_for("login"))
    if session["user"]["role"].upper() == "ADMIN":
        return redirect(url_for("admin_candidates"))
    return redirect(url_for("jobs"))

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        candidate_id = request.form.get("candidate_id","").strip()
        email = request.form.get("email","").strip().lower()
        if not model.is_valid_8digit_not0(candidate_id):
            flash("รหัสผู้ใช้ต้องเป็นเลข 8 หลัก และตัวแรกต้องไม่ใช่ 0")
        elif not model.is_valid_email(email):
            flash("อีเมลไม่ถูกต้อง")
        else:
            user, err = controller.login(candidate_id, email)
            if err:
                flash(err)
            else:
                session["user"] = user
                flash("เข้าสู่ระบบสำเร็จ")
                return redirect(url_for("home"))
    body = """
    <div class="card">
      <h3>เข้าสู่ระบบ</h3>
      <form method="post">
        <label>รหัสผู้ใช้ (8 หลัก):<br><input name="candidate_id" required maxlength="8"></label><br><br>
        <label>อีเมล:<br><input name="email" type="email" required></label><br><br>
        <button class="btn btn-primary" type="submit">เข้าสู่ระบบ</button>
      </form>
      <p class="muted">* สำหรับเดโม่: ดูรายชื่อและอีเมลจากไฟล์ candidates.csv</p>
    </div>
    """
    return render(body, title="Login")

@app.route("/logout")
def logout():
    session.clear()
    flash("ออกจากระบบแล้ว")
    return redirect(url_for("login"))

@app.route("/jobs")
def jobs():
    if "user" not in session:
        return redirect(url_for("login"))
    sort_by = request.args.get("sort","title")
    jobs = controller.get_open_jobs_sorted(sort_by)
    is_admin = session["user"]["role"].upper() == "ADMIN"

    rows = []
    for j in jobs:
        comp = model.get_company(j["company_id"]) or {}
        rows.append(f"""
            <tr>
              <td>{j['title']}</td>
              <td>{comp.get('name','')}</td>
              <td>{j['deadline']}</td>
              <td class="right">
                <a class="btn" href="{url_for('apply', job_id=j['job_id'])}">สมัคร</a>
                {"<span class='pill open'>เปิดรับ</span>" if j['status'].upper()=="OPEN" else "<span class='pill closed'>ปิดรับ</span>"}
              </td>
            </tr>
        """)
    body = f"""
    <div class="card">
      <h3>ตำแหน่งงานที่เปิดรับ</h3>
      <div class="muted">จัดเรียง:
        <a href="{url_for('jobs', sort='title')}">ชื่อตำแหน่ง</a> · 
        <a href="{url_for('jobs', sort='company')}">ชื่อบริษัท</a> · 
        <a href="{url_for('jobs', sort='deadline')}">วันปิดรับ</a>
      </div>
      <table>
        <thead><tr><th>ตำแหน่ง</th><th>บริษัท</th><th>วันปิดรับ</th><th class="right">การทำงาน</th></tr></thead>
        <tbody>
          {''.join(rows)}
        </tbody>
      </table>
    </div>
    """
    if is_admin:
        # extra block: admin can see applicant counts
        counts = controller.admin_counts_by_job()
        rows2 = []
        for r in counts:
            pill = "<span class='pill open'>เปิดรับ</span>" if r["status"].upper()=="OPEN" else "<span class='pill closed'>ปิดรับ</span>"
            rows2.append(f"<tr><td>{r['title']}</td><td>{r['company']}</td><td>{r['deadline']}</td><td>{pill}</td><td class='right'>{r['applicants']}</td></tr>")
        body += f"""
        <div class="card">
          <h3>ภาพรวมตำแหน่งงาน (แอดมิน)</h3>
          <table>
            <thead><tr><th>ตำแหน่ง</th><th>บริษัท</th><th>ปิดรับ</th><th>สถานะ</th><th class="right">จำนวนผู้สมัคร</th></tr></thead>
            <tbody>{''.join(rows2)}</tbody>
          </table>
        </div>
        """
    return render(body, title="ตำแหน่งงาน")

@app.route("/apply/<job_id>")
def apply(job_id):
    redir = require_login()
    if redir: return redir
    user = session["user"]
    ok, msg = controller.apply_job(job_id, user["candidate_id"])
    if ok:
        flash("สมัครงานสำเร็จ")
    else:
        flash(msg)
    # Business rule: after apply, return to jobs page
    return redirect(url_for("jobs"))

@app.route("/me")
def my_profile():
    redir = require_login()
    if redir: return redir
    sort_by = request.args.get("sort","title")
    cand, apps, err = controller.candidate_profile(session["user"]["candidate_id"], sort_by=sort_by)
    if err:
        flash(err)
        return redirect(url_for("jobs"))
    rows = []
    for a in apps:
        job = model.get_job(a["job_id"]) or {}
        comp = model.get_company(job.get("company_id","")) or {}
        rows.append(f"<tr><td>{job.get('title','')}</td><td>{comp.get('name','')}</td><td>{a.get('applied_at','')}</td></tr>")
    body = f"""
    <div class="card">
      <h3>ประวัติผู้สมัคร: {cand['first_name']} {cand['last_name']}</h3>
      <p class="muted">อีเมล: {cand['email']}</p>
      <div class="muted">เรียงตาม: 
        <a href="{url_for('my_profile', sort='title')}">ชื่อตำแหน่ง</a> · 
        <a href="{url_for('my_profile', sort='company')}">ชื่อบริษัท</a> · 
        <a href="{url_for('my_profile', sort='applied_at')}">วันที่สมัคร</a>
      </div>
      <table>
        <thead><tr><th>ตำแหน่ง</th><th>บริษัท</th><th>วันที่สมัคร</th></tr></thead>
        <tbody>{''.join(rows)}</tbody>
      </table>
    </div>
    """
    return render(body, title="ประวัติของฉัน")

# ---------- Admin views ----------
@app.route("/admin/candidates")
def admin_candidates():
    redir = require_admin()
    if redir: return redir
    sort_by = request.args.get("sort","first_name")
    cands = controller.sort_candidates(model.list_candidates(), by=sort_by)
    rows = []
    for c in cands:
        rows.append(f"<tr><td><a href='{url_for('admin_candidate_detail', candidate_id=c['candidate_id'])}'>{c['first_name']} {c['last_name']}</a></td><td>{c['email']}</td><td>{c['role']}</td></tr>")
    body = f"""
    <div class="card">
      <h3>ผู้สมัครทั้งหมด (เรียงตามชื่อ)</h3>
      <table>
        <thead><tr><th>ชื่อ-นามสกุล</th><th>อีเมล</th><th>สิทธิ์</th></tr></thead>
        <tbody>{''.join(rows)}</tbody>
      </table>
    </div>
    """
    return render(body, title="ผู้สมัครทั้งหมด")

@app.route("/admin/candidate/<candidate_id>")
def admin_candidate_detail(candidate_id):
    redir = require_admin()
    if redir: return redir
    sort_by = request.args.get("sort","title")
    cand, apps, err = controller.candidate_profile(candidate_id, sort_by=sort_by)
    if err:
        flash(err)
        return redirect(url_for("admin_candidates"))
    rows = []
    for a in apps:
        job = model.get_job(a["job_id"]) or {}
        comp = model.get_company(job.get("company_id","")) or {}
        rows.append(f"<tr><td>{job.get('title','')}</td><td>{comp.get('name','')}</td><td>{a.get('applied_at','')}</td></tr>")
    body = f"""
    <div class="card">
      <h3>รายละเอียดผู้สมัคร</h3>
      <p><strong>{cand['first_name']} {cand['last_name']}</strong> · {cand['email']}</p>
      <div class="muted">เรียงตาม: 
        <a href="{url_for('admin_candidate_detail', candidate_id=cand['candidate_id'], sort='title')}">ชื่อตำแหน่ง</a> · 
        <a href="{url_for('admin_candidate_detail', candidate_id=cand['candidate_id'], sort='company')}">ชื่อบริษัท</a> · 
        <a href="{url_for('admin_candidate_detail', candidate_id=cand['candidate_id'], sort='applied_at')}">วันที่สมัคร</a>
      </div>
      <table>
        <thead><tr><th>ตำแหน่ง</th><th>บริษัท</th><th>วันที่สมัคร</th></tr></thead>
        <tbody>{''.join(rows)}</tbody>
      </table>
    </div>
    """
    return render(body, title="รายละเอียดผู้สมัคร")

if __name__ == "__main__":
    # Run dev server
    app.run(host="0.0.0.0", port=5000, debug=True)

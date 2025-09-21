
from datetime import datetime
from typing import List, Dict
import model

# ---------- Sorting utilities ----------
def sort_candidates(cands: List[Dict[str,str]], by="first_name") -> List[Dict[str,str]]:
    return sorted(cands, key=lambda x: x.get(by,"").lower())

def sort_jobs(jobs: List[Dict[str,str]], by="title") -> List[Dict[str,str]]:
    key_funcs = {
        "title": lambda j: j.get("title","").lower(),
        "company": lambda j: (model.get_company(j.get("company_id","")) or {}).get("name","").lower(),
        "deadline": lambda j: j.get("deadline","")
    }
    return sorted(jobs, key=key_funcs.get(by, key_funcs["title"]))

def sort_apps(apps: List[Dict[str,str]], by="title") -> List[Dict[str,str]]:
    def key_title(a):
        job = model.get_job(a["job_id"]) or {}
        return job.get("title","").lower()
    def key_company(a):
        job = model.get_job(a["job_id"]) or {}
        comp = model.get_company(job.get("company_id","") ) or {}
        return comp.get("name","").lower()
    def key_date(a):
        return a.get("applied_at","")
    key_map = {"title": key_title, "company": key_company, "applied_at": key_date}
    return sorted(apps, key=key_map.get(by, key_title))

# ---------- Business logic ----------
def login(candidate_id: str, email: str):
    user = model.get_candidate(candidate_id)
    if not user:
        return None, "ไม่พบรหัสผู้ใช้"
    if user.get("email","").lower() != email.lower():
        return None, "อีเมลไม่ถูกต้อง"
    return user, None

def get_open_jobs_sorted(sort_by="title"):
    jobs = model.list_jobs(only_open=True)
    return sort_jobs(jobs, by=sort_by)


def can_apply(job_id: str) -> tuple[bool, str]:
    job = model.get_job(job_id)
    if not job:
        return False, "ไม่พบตำแหน่งงาน"

    if job.get("status", "").upper() != "OPEN":
        return False, "ตำแหน่งนี้ปิดรับสมัครแล้ว"

    # รองรับทั้ง str/date/datetime (parse_date_ymd ของคุณรองรับหลายฟอร์แมตแล้ว)
    raw_deadline = job.get("deadline", "")
    deadline = model.parse_date_ymd(raw_deadline)

    if deadline is None:
        return False, "ข้อมูลวันปิดรับสมัครไม่ถูกต้อง"

    if datetime.now().date() > deadline.date():
        return False, "วันนี้เกินวันปิดรับสมัครแล้ว"

    return True, ""




def apply_job(job_id: str, candidate_id: str) -> tuple[bool, str]:
    res = can_apply(job_id)

    # ป้องกันการคืนรูปแบบผิด (ต้องได้ 2 ค่า)
    if not isinstance(res, tuple) or len(res) != 2:
        ok = bool(res)
        msg = "" if ok else "ข้อมูลวันปิดรับสมัครไม่ถูกต้อง"
    else:
        ok, msg = res

    if not ok:
        return False, msg

    # prevent duplicate application
    existing = model.list_applications_by_candidate(candidate_id)
    for a in existing:
        if a["job_id"] == job_id:
            return False, "คุณสมัครตำแหน่งนี้แล้ว"

    model.add_application(job_id, candidate_id, datetime.now())
    return True, "สมัครงานสำเร็จ"


def candidate_profile(candidate_id: str, sort_by="title"):
    cand = model.get_candidate(candidate_id)
    if not cand:
        return None, [], "ไม่พบผู้สมัคร"
    apps = model.list_applications_by_candidate(candidate_id)
    apps = sort_apps(apps, by=sort_by)
    return cand, apps, ""

def admin_counts_by_job():
    jobs = model.list_jobs(only_open=False)
    result = []
    for j in jobs:
        count = len(model.list_applications_by_job(j["job_id"]))
        comp = model.get_company(j["company_id"]) or {}
        result.append({
            "job_id": j["job_id"],
            "title": j["title"],
            "company": comp.get("name",""),
            "deadline": j["deadline"],
            "status": j["status"],
            "applicants": count
        })
    return result

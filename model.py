
import csv
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional

DATA_DIR = Path(__file__).resolve().parent

COMPANIES_CSV   = DATA_DIR / "companies.csv"
JOBS_CSV        = DATA_DIR / "jobs.csv"
CANDIDATES_CSV  = DATA_DIR / "candidates.csv"
APPLICATIONS_CSV= DATA_DIR / "applications.csv"

DATE_FMT = "%Y-%m-%d"

def _read_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return list(reader)

def _write_csv(path: Path, rows: List[Dict[str, str]]):
    if not rows:
        # if empty, we still need headers; infer from known schemas
        schemas = {
            COMPANIES_CSV: ["company_id","name","email","location"],
            JOBS_CSV: ["job_id","title","description","company_id","deadline","status"],
            CANDIDATES_CSV: ["candidate_id","first_name","last_name","email","role"],
            APPLICATIONS_CSV: ["job_id","candidate_id","applied_at"],
        }
        headers = schemas.get(path, list(rows[0].keys()) if rows else [])
    else:
        headers = list(rows[0].keys())
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        for r in rows:
            writer.writerow(r)

# ---------- CRUD helpers ----------
def list_companies() -> List[Dict[str,str]]:
    return _read_csv(COMPANIES_CSV)

def get_company(company_id: str) -> Optional[Dict[str,str]]:
    for c in list_companies():
        if c["company_id"] == company_id:
            return c
    return None

def list_jobs(only_open: bool=False) -> List[Dict[str,str]]:
    jobs = _read_csv(JOBS_CSV)
    if only_open:
        jobs = [j for j in jobs if j.get("status","").upper() == "OPEN"]
    return jobs

def get_job(job_id: str) -> Optional[Dict[str,str]]:
    for j in list_jobs(only_open=False):
        if j["job_id"] == job_id:
            return j
    return None

def list_candidates() -> List[Dict[str,str]]:
    return _read_csv(CANDIDATES_CSV)

def get_candidate(candidate_id: str) -> Optional[Dict[str,str]]:
    for c in list_candidates():
        if c["candidate_id"] == candidate_id:
            return c
    return None

def list_applications() -> List[Dict[str,str]]:
    return _read_csv(APPLICATIONS_CSV)

def list_applications_by_candidate(candidate_id: str) -> List[Dict[str,str]]:
    return [a for a in list_applications() if a["candidate_id"] == candidate_id]

def list_applications_by_job(job_id: str) -> List[Dict[str,str]]:
    return [a for a in list_applications() if a["job_id"] == job_id]

def add_application(job_id: str, candidate_id: str, applied_at: datetime) -> None:
    apps = list_applications()
    apps.append({
        "job_id": job_id,
        "candidate_id": candidate_id,
        "applied_at": applied_at.strftime("%Y-%m-%d %H:%M:%S")
    })
    _write_csv(APPLICATIONS_CSV, apps)

def upsert_row(path: Path, key_field: str, row: Dict[str,str]) -> None:
    rows = _read_csv(path)
    found = False
    for i, r in enumerate(rows):
        if r.get(key_field) == row.get(key_field):
            rows[i] = row
            found = True
            break
    if not found:
        rows.append(row)
    _write_csv(path, rows)

# ---------- Validation helpers ----------
def is_valid_8digit_not0(s: str) -> bool:
    return len(s) == 8 and s.isdigit() and s[0] != "0"

def is_valid_email(email: str) -> bool:
    # very simple check for assignment purposes
    if not email or "@" not in email:
        return False
    local, _, domain = email.partition("@")
    return "." in domain and len(local) > 0
# model.py
from datetime import datetime, date

DATE_FMT = "%Y-%m-%d"

def parse_date_ymd(s) -> Optional[datetime]:
    if not s:
        return None
    s = str(s).strip()          # ตัดช่องว่างหัวท้าย
    s10 = s[:10]                # เผื่อมีเวลาเกินมา ตัดเหลือ 10 ตัวแรก

    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(s10, fmt)
        except ValueError:
            continue
    return None

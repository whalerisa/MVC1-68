
# Creates sample CSV data for the Job Fair MVC (CSV) app.
import csv, random
from pathlib import Path
from datetime import datetime, timedelta

DATA_DIR = Path(__file__).resolve().parent

def write(path, rows, headers):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=headers)
        w.writeheader()
        for r in rows: w.writerow(r)

def gen_8digit(n, nozero=True):
    s = f"{n:08d}"
    if nozero and s[0] == "0":
        s = "1" + s[1:]
    return s

# Companies
companies = [
    {"company_id":"10000001","name":"Alpha Tech Co., Ltd.","email":"hr@alphatech.co","location":"Bangkok"},
    {"company_id":"10000002","name":"Beta Solutions PLC","email":"jobs@betasolutions.com","location":"Chiang Mai"},
]

# Jobs (>=10 across 2 companies)
titles = [
    "Software Engineer (Backend)",
    "Software Engineer (Frontend)",
    "Data Analyst",
    "DevOps Engineer",
    "QA Engineer",
    "Mobile Developer",
    "UI/UX Designer",
    "IT Support",
    "Product Manager",
    "Data Engineer",
    "Security Analyst",
]
jobs = []
today = datetime.now().date()
for i, t in enumerate(titles, start=1):
    cid = companies[i % 2]["company_id"]
    deadline = today + timedelta(days=7 + i)  # all open by default
    jobs.append({
        "job_id": gen_8digit(2000+i),
        "title": t,
        "description": f"{t} – responsibilities include collaborating with cross-functional teams.",
        "company_id": cid,
        "deadline": str(deadline),
        "status": "OPEN" if i % 5 != 0 else "CLOSED"  # a few closed
    })

# Candidates (>=10) + 1 admin
firsts = ["Anya","Ben","Chai","Dao","Ek","Fah","Gao","Hana","Ice","Jane","Admin"]
lasts  = ["Wong","Smith","Prasert","Nok","Kitti","Chan","Manee","Sato","Kim","Doe","User"]
cands = []
for i in range(11):
    cid = gen_8digit(3000+i)
    role = "ADMIN" if i == 10 else "USER"
    cands.append({
        "candidate_id": cid,
        "first_name": firsts[i],
        "last_name": lasts[i],
        "email": (firsts[i] + "." + lasts[i] + "@example.com").lower(),
        "role": role
    })

# Applications (some random existing)
apps = []
for i in range(12):
    c = random.choice(cands[:-1])  # exclude admin from random
    j = random.choice([j for j in jobs if j["status"]=="OPEN"])
    apps.append({
        "job_id": j["job_id"],
        "candidate_id": c["candidate_id"],
        "applied_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })

write(DATA_DIR/"companies.csv", companies, ["company_id","name","email","location"])
write(DATA_DIR/"jobs.csv", jobs, ["job_id","title","description","company_id","deadline","status"])
write(DATA_DIR/"candidates.csv", cands, ["candidate_id","first_name","last_name","email","role"])
write(DATA_DIR/"applications.csv", apps, ["job_id","candidate_id","applied_at"])

print("Seeded sample CSVs in", DATA_DIR)
print("- companies.csv")
print("- jobs.csv")
print("- candidates.csv (use Admin user to login: candidate_id =", cands[-1]["candidate_id"], ", email =", cands[-1]["email"], ")")
print("- applications.csv")

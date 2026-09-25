#!/usr/bin/env python3
"""
يحدّث data/listings.json تلقائيًا من صفحات التوظيف العامة للشركات الناشئة.

- يجيب الإعلانات من أنظمة التوظيف (Workable, Greenhouse, Ashby, Pinpoint)
- ياخذ بس الإعلانات اللي في السعودية ومناسبة للمبتدئين
- الإعلانات اليدوية (بدون "source": "auto") ما يلمسها أبدًا
- إذا فشل الاتصال بشركة، يخلي إعلاناتها القديمة زي ما هي
"""
import json, re, sys, datetime, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "listings.json"
HISTORY = ROOT / "data" / "history.json"
TODAY = datetime.date.today().isoformat()

# ---------- الشركات ومصادرها ----------
# لإضافة شركة: انسخي سطر وغيّري الاسم ونوع النظام ومعرّف الشركة فيه
SOURCES = [
    {"company": "تابي",     "companyEn": "Tabby",             "ats": "pinpoint",   "id": "tabby"},
    {"company": "لين",      "companyEn": "Lean Technologies", "ats": "ashby",      "id": "leantech"},
    {"company": "هلا",      "companyEn": "HALA",              "ats": "greenhouse", "id": "hala"},
    {"company": "تمارا",    "companyEn": "Tamara",            "ats": "greenhouse", "id": "tamara"},
    {"company": "فودكس",    "companyEn": "Foodics",           "ats": "workable",   "id": "foodics"},
    {"company": "سلة",      "companyEn": "Salla",             "ats": "workable",   "id": "salla"},
    {"company": "لوسيديا",  "companyEn": "Lucidya",           "ats": "workable",   "id": "lucidya"},
    {"company": "مرسول",    "companyEn": "Mrsool",            "ats": "workable",   "id": "mrsool-3"},
    {"company": "ساري",     "companyEn": "Sary",              "ats": "workable",   "id": "sary"},
    {"company": "نينجا",    "companyEn": "Ninja",             "ats": "workable",   "id": "ananinja"},
    {"company": "نعناع",    "companyEn": "Nana",              "ats": "workable",   "id": "nana-grocery-direct"},
    {"company": "كوقنا",    "companyEn": "COGNNA",            "ats": "workable",   "id": "cognna"},
    {"company": "مزن",      "companyEn": "Mozn",              "ats": "workable",   "id": "mozn-ai"},
    {"company": "زد",       "companyEn": "Zid",               "ats": "smartrecruiters", "id": "Zid1"},
    {"company": "جسر",      "companyEn": "Jisr",              "ats": "smartrecruiters", "id": "Jisr"},
]

# ---------- الفلاتر ----------
BEGINNER = re.compile(
    r"\b(intern|internship|interns|trainee|traineeship|apprentice|graduate|graduates|grad|fresh|junior|jr\.?|entry[\s-]?level|co-?op|tamheer|builders)\b"
    r"|تمهير|تدريب|متدرب|حديثي|تعاوني", re.I)
EXCLUDE = re.compile(r"\b(senior|sr\.?|lead|head|manager|director|principal|staff)\b", re.I)
SAUDI = re.compile(r"saudi|\bksa\b|riyadh|jeddah|jiddah|dammam|khobar|makkah|mecca|madinah|medina|dhahran|السعودية|الرياض|جدة", re.I)

CITY_AR = {"riyadh": "الرياض", "jeddah": "جدة", "jiddah": "جدة", "dammam": "الدمام", "khobar": "الخبر",
           "al khobar": "الخبر", "makkah": "مكة", "mecca": "مكة", "madinah": "المدينة", "medina": "المدينة",
           "dhahran": "الظهران"}

FIELD_RULES = [
    ("cyber",   r"secur|cyber|\bgrc\b|\bsoc\b|infosec|fraud"),
    ("data",    r"\bdata\b|\bai\b|\bml\b|machine learning|analytic|scien|\bbi\b"),
    ("media",   r"content|marketing|social|video|campaign|brand|creative"),
    ("product", r"product|design|\bux\b|\bui\b"),
    ("tech",    r"engineer|developer|devops|\bqa\b|software|frontend|backend|front-end|back-end|\bios\b|android|\bsre\b"),
]

def classify_type(title, experience=""):
    t = f"{title} {experience}".lower()
    if re.search(r"co-?op|تعاوني|graduation requirement", t): return "coop"
    if re.search(r"graduate program|builders program|trainee|traineeship|development program|تمهير|tamheer", t): return "grad"
    if re.search(r"intern", t): return "internship"
    return "entry"

def classify_field(text):
    t = text.lower()
    for key, pat in FIELD_RULES:
        if re.search(pat, t): return key
    return "business"

def city_ar(raw):
    raw = (raw or "").strip()
    return CITY_AR.get(raw.lower(), raw or "السعودية")

def is_beginner(title, experience=""):
    if EXCLUDE.search(title) and not re.search(r"intern|graduate|trainee|tamheer|builders|تمهير", title, re.I):
        return False
    return bool(BEGINNER.search(title)) or experience.lower() in ("entry level", "internship")

# ---------- الاتصال ----------
def get_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": "awal-khatwa-bot/1.0", "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode("utf-8"))

def fetch_workable(src):
    d = get_json(f"https://apply.workable.com/api/v1/widget/accounts/{src['id']}")
    for j in d.get("jobs", []):
        loc = " ".join(filter(None, [j.get("city"), j.get("state"), j.get("country")]))
        yield dict(title=j.get("title", ""), url=j.get("url") or j.get("shortlink"), location=loc,
                   city=j.get("city"), experience=j.get("experience") or "", dept=j.get("department") or "",
                   deadline="", posted=j.get("published_on") or "", remote=bool(j.get("telecommuting")))

def fetch_greenhouse(src):
    host = "boards-api.eu.greenhouse.io" if src.get("region") == "eu" else "boards-api.greenhouse.io"
    d = get_json(f"https://{host}/v1/boards/{src['id']}/jobs")
    for j in d.get("jobs", []):
        loc = (j.get("location") or {}).get("name", "")
        dl = (j.get("application_deadline") or "")[:10]
        yield dict(title=j.get("title", ""), url=j.get("absolute_url"), location=loc,
                   city=loc.split(",")[0], experience="", dept="", deadline=dl,
                   posted=(j.get("first_published") or j.get("updated_at") or "")[:10],
                   remote=bool(re.search(r"remote", loc, re.I)))

def fetch_ashby(src):
    d = get_json(f"https://api.ashbyhq.com/posting-api/job-board/{src['id']}")
    for j in d.get("jobs", []):
        if j.get("isListed") is False: continue
        addr = ((j.get("address") or {}).get("postalAddress") or {})
        loc = " ".join(filter(None, [j.get("location"), addr.get("addressLocality"), addr.get("addressCountry")]))
        yield dict(title=j.get("title", ""), url=j.get("jobUrl"), location=loc,
                   city=addr.get("addressLocality") or (j.get("location") or "").split(",")[0],
                   experience="", dept=j.get("department") or "", deadline="",
                   posted=(j.get("publishedAt") or "")[:10],
                   remote=bool(j.get("isRemote")) or (j.get("workplaceType") or "").lower() == "remote")

def fetch_pinpoint(src):
    d = get_json(f"https://{src['id']}.pinpointhq.com/postings.json")
    for j in d.get("data", []):
        L = j.get("location") or {}
        loc = " ".join(filter(None, [L.get("city"), L.get("name"), L.get("province")]))
        dept = ((j.get("job") or {}).get("department") or {}).get("name", "")
        yield dict(title=j.get("title", ""), url=j.get("url"), location=loc, city=L.get("city"),
                   experience="", dept=dept, deadline=(j.get("deadline_at") or "")[:10], posted="",
                   remote=(j.get("workplace_type") or "").lower() == "remote")

def fetch_smartrecruiters(src):
    offset = 0
    while True:
        d = get_json(f"https://api.smartrecruiters.com/v1/companies/{src['id']}/postings?limit=100&offset={offset}")
        content = d.get("content", [])
        for j in content:
            L = j.get("location") or {}
            loc = " ".join(filter(None, [L.get("city"), L.get("region"), L.get("country"), L.get("fullLocation")]))
            if (L.get("country") or "").lower() == "sa":
                loc += " Saudi Arabia"
            exp = ((j.get("experienceLevel") or {}).get("id") or "").replace("_", " ")
            yield dict(title=j.get("name", ""), url=f"https://jobs.smartrecruiters.com/{src['id']}/{j.get('id')}",
                       location=loc, city=L.get("city"), experience=exp,
                       dept=(j.get("department") or {}).get("label", ""), deadline="",
                       posted=(j.get("releasedDate") or "")[:10], remote=bool(L.get("remote")))
        offset += len(content)
        if not content or offset >= d.get("totalFound", 0):
            break

FETCHERS = {"workable": fetch_workable, "greenhouse": fetch_greenhouse, "ashby": fetch_ashby,
            "pinpoint": fetch_pinpoint, "smartrecruiters": fetch_smartrecruiters}

# ---------- الدمج ----------
def norm_title(t):
    return re.sub(r"[^a-z0-9؀-ۿ]+", " ", (t or "").lower()).strip()

def key_of(item):
    return f"{(item.get('companyEn') or '').lower()}|{norm_title(item.get('title'))}"

def slug(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")[:60]

def main():
    old = json.loads(DATA.read_text(encoding="utf-8")) if DATA.exists() else []
    manual = [x for x in old if x.get("source") != "auto"]
    old_auto = {key_of(x): x for x in old if x.get("source") == "auto"}
    manual_keys = {key_of(x) for x in manual}

    fresh, failed = {}, set()
    for src in SOURCES:
        try:
            rows = list(FETCHERS[src["ats"]](src))
        except Exception as e:
            print(f"!! {src['companyEn']}: {e}", file=sys.stderr)
            failed.add(src["companyEn"].lower())
            continue
        kept = 0
        for r in rows:
            if not r["url"] or not SAUDI.search(r["location"] or ""):
                continue
            if not is_beginner(r["title"], r["experience"]):
                continue
            item = {"company": src["company"], "companyEn": src["companyEn"], "title": r["title"].strip()}
            k = key_of(item)
            if k in manual_keys:
                continue
            c = city_ar(r["city"])
            if k in fresh:  # نفس الإعلان في أكثر من مدينة
                if c not in fresh[k]["city"]:
                    fresh[k]["city"] += f" أو {c}"
                fresh[k]["remote"] = fresh[k]["remote"] or bool(r.get("remote"))
                continue
            prev = old_auto.get(k, {})
            item.update({
                "id": prev.get("id") or slug(f"{src['companyEn']}-{r['title']}"),
                "type": prev.get("type") or classify_type(r["title"], r["experience"]),
                "field": prev.get("field") or classify_field(f"{r['title']} {r['dept']}"),
                "city": c,
                "status": "open",
                "deadline": r["deadline"] or prev.get("deadline", ""),
                "paid": prev.get("paid", ""),
                "duration": prev.get("duration", ""),
                "who": prev.get("who") or (f"قسم {r['dept']}." if r["dept"] else ""),
                "url": r["url"],
                "checked": TODAY,
                "posted": r["posted"] or prev.get("posted", ""),
                "firstSeen": prev.get("firstSeen") or ((r["posted"] or prev.get("posted") or TODAY) if prev else TODAY),
                "remote": bool(r.get("remote")),
                "source": "auto",
            })
            fresh[k] = item
            kept += 1
        print(f"{src['companyEn']}: {len(rows)} وظيفة، {kept} مناسبة للمبتدئين")

    # الشركات اللي فشل الاتصال فيها: نخلي إعلاناتها القديمة
    for k, x in old_auto.items():
        if (x.get("companyEn") or "").lower() in failed and k not in fresh:
            fresh[k] = x

    result = manual + sorted(fresh.values(), key=lambda x: x.get("posted", ""), reverse=True)

    record_history(result)

    def strip_dates(lst):
        return [{kk: vv for kk, vv in x.items() if kk != "checked"} for x in lst]
    if strip_dates(result) == strip_dates(old):
        print("ما فيه تغيير في الإعلانات.")
        return
    DATA.write_text(json.dumps(result, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"انحفظ: {len(manual)} يدوي + {len(fresh)} تلقائي")

# ---------- سجل يومي للإحصائيات ----------
def is_open(x):
    if x.get("status") not in ("open", "rolling"):
        return False
    return not (x.get("deadline") and x["deadline"] < TODAY)

def record_history(listings):
    hist = json.loads(HISTORY.read_text(encoding="utf-8")) if HISTORY.exists() else []
    hist = [h for h in hist if h.get("date") != TODAY]
    open_items = [x for x in listings if is_open(x)]
    def count(key, items):
        out = {}
        for x in items:
            v = x.get(key) or "other"
            out[v] = out.get(v, 0) + 1
        return dict(sorted(out.items(), key=lambda kv: -kv[1]))
    new_today = [x for x in listings if x.get("source") == "auto" and x.get("firstSeen") == TODAY]
    hist.append({
        "date": TODAY,
        "open": len(open_items),
        "total": len(listings),
        "new": len(new_today),
        "newIds": [x["id"] for x in new_today],
        "byCompany": count("companyEn", open_items),
        "byField": count("field", open_items),
        "byType": count("type", open_items),
    })
    hist.sort(key=lambda h: h["date"])
    HISTORY.write_text(json.dumps(hist[-730:], ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"السجل: {len(open_items)} فرصة مفتوحة، {len(new_today)} جديدة اليوم")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
يحدّث data/listings.json تلقائيًا من صفحات التوظيف العامة للشركات الناشئة.

- يجيب الإعلانات من أنظمة التوظيف (Workable, Greenhouse, Ashby, Pinpoint)
- ياخذ بس الإعلانات اللي في السعودية ومناسبة للمبتدئين
- الإعلانات اليدوية (بدون "source": "auto") ما يلمسها أبدًا
- إذا فشل الاتصال بشركة، يخلي إعلاناتها القديمة زي ما هي
"""
import json, re, sys, html, datetime, urllib.request
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
    {"company": "ويبوك",    "companyEn": "webook",            "ats": "workable",   "id": "webook"},
    {"company": "سرج",      "companyEn": "Sarj",              "ats": "ashby",      "id": "sarjai"},
    {"company": "ملاءة",    "companyEn": "Malaa",             "ats": "pinpoint",   "id": "malaa"},
    {"company": "ليكورا",   "companyEn": "LAKEORA",           "ats": "ashby",      "id": "lakeora"},
    {"company": "ميراي",    "companyEn": "Mirai",             "ats": "workable",   "id": "playmirai"},
    {"company": "أدري",     "companyEn": "Adree",             "ats": "workable",   "id": "adree"},
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

# ---------- فحص نص الوصف: يطلب خبرة؟ ----------
AR_NUM = {"سنة": 1, "سنه": 1, "سنتين": 2, "سنتان": 2, "ثلاث": 3, "ثلاثة": 3, "أربع": 4, "اربع": 4, "أربعة": 4, "خمس": 5, "خمسة": 5}
EN_NUM = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8, "ten": 10}
NUM = r"(\d{1,2}|one|two|three|four|five|six|seven|eight|ten)"
EXP_PATTERNS = [
    # 2+ years of experience / 3-5 years experience / 2 or more years of relevant experience
    re.compile(NUM + r"\s*(?:\+|plus)?\s*(?:(?:-|–|—|to)\s*\d{1,2}\s*)?(?:or more\s*)?(?:years?|yrs?)(?:'s)?\s*(?:of\s*)?(?:[a-z\-/&,]+\s+){0,4}?(?:experience|exp\b)", re.I),
    # minimum / at least / minimum of 2 years
    re.compile(r"(?:minimum(?:\s+of)?|at\s+least|min\.?)\s*" + NUM + r"\s*(?:\+\s*)?(?:years?|yrs?)", re.I),
    # experience: 3 years
    re.compile(r"experience\s*(?:of|:)?\s*" + NUM + r"\s*(?:\+|plus)?\s*(?:years?|yrs?)", re.I),
]
AR_PATTERNS = [
    re.compile(r"خبرة\s*(?:عملية\s*)?(?:لا\s*تقل\s*عن|لاتقل\s*عن|من|تتجاوز)?\s*(\d{1,2}|سنتين|سنتان|ثلاث|ثلاثة|أربع|اربع|أربعة|خمس|خمسة)\s*(?:سنوات|سنة|سنين)?"),
    re.compile(r"(\d{1,2}|سنتين|ثلاث|أربع|خمس)\s*(?:سنوات|سنة)?\s*(?:من\s*)?(?:ال)?خبرة"),
]
NO_FRESH = re.compile(r"not\s+(?:open|suitable|applicable|eligible)\s+(?:to|for)\s+(?:fresh|new|recent)\s+grad|no\s+fresh\s+grad|fresh\s+graduates?\s+(?:are\s+)?not\s+(?:eligible|accepted|considered)|(?:لا|غير)\s*(?:يقبل|مقبول|مناسب)\S*\s*(?:ل)?حديثي\s*(?:ال)?تخرج", re.I)

def _num(tok):
    tok = tok.strip().lower()
    if tok.isdigit(): return int(tok)
    return EN_NUM.get(tok) or AR_NUM.get(tok) or 0

def needs_experience(text):
    """يرجع سبب الاستبعاد إذا الإعلان يطلب خبرة سنتين أو أكثر، أو يرفض حديثي التخرج."""
    if not text:
        return None
    t = re.sub(r"\s+", " ", text)
    m = NO_FRESH.search(t)
    if m:
        return m.group(0)
    for pat in EXP_PATTERNS + AR_PATTERNS:
        for m in pat.finditer(t):
            if _num(m.group(1)) >= 2:
                return m.group(0)
    return None

def strip_html(s):
    s = html.unescape(s or "")
    s = re.sub(r"<(br|/p|/li|/div|/h\d)[^>]*>", "\n", s, flags=re.I)
    s = re.sub(r"<[^>]+>", " ", s)
    return html.unescape(s)

# ---------- كلمات مفتاحية من الوصف (للمطابقة مع السيرة) ----------
KW_STOP = set("""a an and are as at be been being but by can could do does for from has have having he her his how i if in into is it its may more most must no not of on or our out over own per should so some such than that the their them then there these they this those to under up us very was we were what when where which while who will with within without would you your about above across after again against all also among any because before below between both during each few further here just less many much only other same shall since still through too until upon via whether yet able ability abilities work working works job role roles team teams company candidate candidates looking join years year experience experiences strong good great excellent knowledge understanding skills skill including include includes using use used new well etc responsibilities responsibility qualifications qualification requirements required preferred plus bonus opportunity degree related field fields based ensure support day days key help make level levels familiarity familiar bachelor bachelors master masters riyadh jeddah dammam khobar saudi arabia ksa junior senior intern interns internship graduate graduates fresh entry full time part hybrid remote onsite apply applicants ideal minimum preferably proven solid demonstrated similar equivalent month months week weeks program training trainee opportunity opportunities environment offer offers benefits competitive salary join growing fast leading platform customers customer clients client people business across world region mena gcc need needs seeking want wants looking ideally students student welcome welcomed one two best right clear existing basic learn learning assist updates written evidence problems processes develop developing development organisations organizations tools office partners relationships technical technologies products tech""" .split())
KW_PHRASES = ["a/b testing","machine learning","deep learning","data analysis","data analytics","data science","data visualization","power bi","project management","product management","customer service","customer success","business development","social media","content writing","problem solving","attention to detail","communication skills","time management","rest api","unit testing","version control","incident response","threat intelligence","penetration testing","vulnerability assessment","risk management","financial analysis","user research","ui design","ux design","google analytics","microsoft excel","ms office","full stack","cloud computing","network security","information security","sql server","node.js","react native","computer science","information systems","software engineering","iso 27001","nca ecc"]

def extract_keywords(text, limit=20, company=""):
    low = (text or "").lower()
    own = set(re.findall(r"[a-z]+", (company or "").lower()))
    found = {}
    for p in KW_PHRASES:
        n = low.count(p)
        if n:
            found[p] = n * 3
            low = low.replace(p, " ")
    for w in re.findall(r"[a-z][a-z0-9+#.\-]{1,}", low):
        w = w.rstrip(".-")
        if (len(w) < 3 and w not in ("c#", "go", "ai", "ml", "bi", "qa", "ux", "ui", "hr")) or w in KW_STOP or w in own or w.isdigit():
            continue
        found[w] = found.get(w, 0) + 1
    return [k for k, _ in sorted(found.items(), key=lambda kv: -kv[1])[:limit]]

# ---------- الاتصال ----------
def get_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": "awal-khatwa-bot/1.0", "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode("utf-8"))

def fetch_workable(src):
    d = get_json(f"https://apply.workable.com/api/v1/widget/accounts/{src['id']}?details=true")
    for j in d.get("jobs", []):
        loc = " ".join(filter(None, [j.get("city"), j.get("state"), j.get("country")]))
        yield dict(title=j.get("title", ""), url=j.get("url") or j.get("shortlink"), location=loc,
                   city=j.get("city"), experience=j.get("experience") or "", dept=j.get("department") or "",
                   deadline="", posted=j.get("published_on") or "", remote=bool(j.get("telecommuting")),
                   desc=strip_html(j.get("description")))

def fetch_greenhouse(src):
    host = "boards-api.eu.greenhouse.io" if src.get("region") == "eu" else "boards-api.greenhouse.io"
    d = get_json(f"https://{host}/v1/boards/{src['id']}/jobs?content=true")
    for j in d.get("jobs", []):
        loc = (j.get("location") or {}).get("name", "")
        dl = (j.get("application_deadline") or "")[:10]
        yield dict(title=j.get("title", ""), url=j.get("absolute_url"), location=loc,
                   city=loc.split(",")[0], experience="", dept="", deadline=dl,
                   posted=(j.get("first_published") or j.get("updated_at") or "")[:10],
                   remote=bool(re.search(r"remote", loc, re.I)),
                   desc=strip_html(j.get("content")))

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
                   remote=bool(j.get("isRemote")) or (j.get("workplaceType") or "").lower() == "remote",
                   desc=j.get("descriptionPlain") or strip_html(j.get("descriptionHtml")))

def fetch_pinpoint(src):
    d = get_json(f"https://{src['id']}.pinpointhq.com/postings.json")
    for j in d.get("data", []):
        L = j.get("location") or {}
        loc = " ".join(filter(None, [L.get("city"), L.get("name"), L.get("province")]))
        dept = ((j.get("job") or {}).get("department") or {}).get("name", "")
        yield dict(title=j.get("title", ""), url=j.get("url"), location=loc, city=L.get("city"),
                   experience="", dept=dept, deadline=(j.get("deadline_at") or "")[:10], posted="",
                   remote=(j.get("workplace_type") or "").lower() == "remote",
                   desc=strip_html(" ".join(filter(None, [j.get("description"), j.get("key_responsibilities"), j.get("skills_knowledge_expertise")]))))

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
                       posted=(j.get("releasedDate") or "")[:10], remote=bool(L.get("remote")),
                       desc=None, load_desc=(lambda pid=j.get("id"): smartrecruiters_desc(src["id"], pid)))
        offset += len(content)
        if not content or offset >= d.get("totalFound", 0):
            break

def smartrecruiters_desc(company, pid):
    d = get_json(f"https://api.smartrecruiters.com/v1/companies/{company}/postings/{pid}")
    sec = ((d.get("jobAd") or {}).get("sections") or {})
    return strip_html(" ".join((sec.get(k) or {}).get("text", "") for k in ("jobDescription", "qualifications", "additionalInformation")))

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
        kept = skipped = 0
        for r in rows:
            if not r["url"] or not SAUDI.search(r["location"] or ""):
                continue
            if not is_beginner(r["title"], r["experience"]):
                continue
            r["title"] = re.sub(r"\s+", " ", re.sub(r"&amp;?", "&", html.unescape(r["title"] or ""))).strip()
            item = {"company": src["company"], "companyEn": src["companyEn"], "title": r["title"]}
            k = key_of(item)
            if k in manual_keys:
                continue
            desc = r.get("desc")
            if desc is None and r.get("load_desc"):
                try:
                    desc = r["load_desc"]()
                except Exception as e:
                    print(f"   (ما قدرنا نقرأ وصف {r['title']}: {e})", file=sys.stderr)
                    desc = ""
            why = needs_experience(desc)
            if why:
                skipped += 1
                print(f"   ✗ استبعدنا «{r['title']}»: الوصف يقول «{why.strip()[:70]}»")
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
                "keywords": extract_keywords(desc, company=src["companyEn"]) or prev.get("keywords", []),
                "source": "auto",
            })
            fresh[k] = item
            kept += 1
        print(f"{src['companyEn']}: {len(rows)} وظيفة، {kept} مناسبة للمبتدئين" + (f"، واستبعدنا {skipped} تطلب خبرة" if skipped else ""))

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

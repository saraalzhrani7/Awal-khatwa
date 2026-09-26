#!/usr/bin/env python3
"""
يحدّث data/listings.json تلقائيًا من صفحات التوظيف العامة للشركات الناشئة.

- يجيب الإعلانات من أنظمة التوظيف (Workable, Greenhouse, Ashby, Pinpoint, SmartRecruiters, Workday, Oracle, SuccessFactors)
- ياخذ بس الإعلانات اللي في السعودية ومناسبة للمبتدئين
- الإعلانات اليدوية (بدون "source": "auto") ما يلمسها أبدًا
- إذا فشل الاتصال بشركة، يخلي إعلاناتها القديمة زي ما هي
"""
import json, re, sys, html, datetime, urllib.request, urllib.parse
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "listings.json"
HISTORY = ROOT / "data" / "history.json"
FEED = ROOT / "feed.xml"
JOBS_DIR = ROOT / "j"
SITE = "https://saraalzhrani7.github.io/Awal-khatwa/"
TODAY = datetime.date.today().isoformat()
MANUAL_MAX_AGE = 60   # الإعلان اليدوي اللي ما تحدث من 60 يوم ينقفل تلقائيًا
TYPES_AR = {"coop": "تدريب تعاوني", "internship": "Internship", "grad": "برنامج خريجين", "entry": "Entry Level"}

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

    # ---- شبه حكومي (صندوق الاستثمارات العامة والشركات المملوكة للدولة) ----
    {"company": "القدية",   "companyEn": "Qiddiya",           "ats": "workable",   "id": "qiddiya-investment-company-1", "org": "semi"},
    {"company": "إس تي سي", "companyEn": "stc",               "ats": "successfactors", "domain": "careers.stc.com.sa", "saudi": True, "org": "semi"},
    {"company": "الخطوط السعودية", "companyEn": "Saudia",     "ats": "successfactors", "domain": "careers.saudia.com", "saudi": True, "org": "semi"},
    {"company": "علم",      "companyEn": "Elm",               "ats": "successfactors", "domain": "career.elm.sa", "path": "/elm", "saudi": True, "org": "semi"},
    {"company": "أرامكو",   "companyEn": "Aramco",            "ats": "successfactors", "domain": "careers.aramco.com", "org": "semi"},
    {"company": "البحر الأحمر الدولية", "companyEn": "Red Sea Global", "ats": "successfactors", "domain": "careers.theredsea.sa", "saudi": True, "org": "semi"},
    {"company": "الشركة السعودية للكهرباء", "companyEn": "Saudi Electricity", "ats": "successfactors", "domain": "jobs.se.com.sa", "saudi": True, "org": "semi"},
    {"company": "كاوست",    "companyEn": "KAUST",             "ats": "successfactors", "domain": "careers.kaust.edu.sa", "saudi": True, "org": "semi"},
    {"company": "أكوا باور", "companyEn": "ACWA Power",       "ats": "successfactors", "domain": "careers.acwapower.com", "org": "private"},

    # ---- شركات خاصة كبيرة وعالمية (فروعها في السعودية) ----
    {"company": "النهدي",   "companyEn": "Nahdi",             "ats": "oracle",     "host": "efan.fa.em3.oraclecloud.com", "site": "CX_1", "org": "private"},
    {"company": "لوسد",     "companyEn": "Lucid Motors",      "ats": "greenhouse", "id": "lucidmotors", "org": "private"},
    {"company": "كي بي إم جي", "companyEn": "KPMG",           "ats": "successfactors", "domain": "slccareers.kpmg.com", "loc": "Saudi Arabia", "org": "private"},
    {"company": "بي دبليو سي", "companyEn": "PwC Middle East", "ats": "workday", "host": "pwc.wd3.myworkdayjobs.com", "tenant": "pwc", "site": "Global_Campus_Careers", "global": True, "org": "private"},
    {"company": "أكسنتشر",  "companyEn": "Accenture",         "ats": "workday",    "host": "accenture.wd103.myworkdayjobs.com", "tenant": "accenture", "site": "AccentureCareers", "global": True, "org": "private"},
    {"company": "بيكر هيوز", "companyEn": "Baker Hughes",     "ats": "workday",    "host": "bakerhughes.wd5.myworkdayjobs.com", "tenant": "bakerhughes", "site": "BakerHughes", "global": True, "org": "private"},
    {"company": "جي إي فيرنوفا", "companyEn": "GE Vernova",   "ats": "workday",    "host": "gevernova.wd5.myworkdayjobs.com", "tenant": "gevernova", "site": "Vernova_ExternalSite", "global": True, "org": "private"},
    {"company": "بارسونز",  "companyEn": "Parsons",           "ats": "workday",    "host": "parsons.wd5.myworkdayjobs.com", "tenant": "parsons", "site": "Search", "global": True, "org": "private"},
    {"company": "إتش بي إي", "companyEn": "HPE",              "ats": "workday",    "host": "hpe.wd5.myworkdayjobs.com", "tenant": "hpe", "site": "WFMathpe", "global": True, "org": "private"},
    {"company": "موتورولا سوليوشنز", "companyEn": "Motorola Solutions", "ats": "workday", "host": "motorolasolutions.wd5.myworkdayjobs.com", "tenant": "motorolasolutions", "site": "Careers", "global": True, "org": "private"},
]
# نوع الجهة: startup (افتراضي) · private · semi (شبه حكومي) · gov (حكومي) · bank
ORG_DEFAULT = "startup"

# كلمات البحث في الأنظمة الكبيرة (Workday وOracle وSuccessFactors) عشان ما نحمّل آلاف الوظائف
SEARCH_TERMS = ["intern", "graduate", "co-op", "coop", "trainee", "tamheer", "junior", "fresh graduate", "entry level", "development program"]
# للشركات العالمية: ندور بالسعودية أول، وبعدين نفلتر وظائف المبتدئين
GLOBAL_TERMS = ["Saudi", "Riyadh", "KSA", "Tamheer", "Jeddah", "Dhahran", "Khobar"]

# ---------- الفلاتر ----------
BEGINNER = re.compile(
    r"\b(intern|internship|interns|trainee|traineeship|apprentice|graduate|graduates|grad|fresh[\s-]?grad\w*|junior|jr\.?|entry[\s-]?level|co-?op|tamheer|builders)\b"
    r"|تمهير|تدريب|متدرب|حديثي|تعاوني", re.I)
EXCLUDE = re.compile(r"\b(senior|sr\.?|lead|head|manager|director|principal|staff)\b", re.I)
SAUDI = re.compile(r"saudi|\bksa\b|riyadh|jeddah|jiddah|dammam|khobar|makkah|mecca|madinah|medina|dhahran|jubail|yanbu|ras tanura|abqaiq|tabuk|neom|abha|taif|qassim|buraydah|hail|jazan|najran|al ?ahsa|hofuf|kaec|king abdullah economic city|thuwal|السعودية|الرياض|جدة|الدمام|الخبر|الظهران", re.I)

CITY_AR = {"riyadh": "الرياض", "jeddah": "جدة", "jiddah": "جدة", "dammam": "الدمام", "khobar": "الخبر",
           "al khobar": "الخبر", "makkah": "مكة", "mecca": "مكة", "madinah": "المدينة", "medina": "المدينة",
           "dhahran": "الظهران", "jubail": "الجبيل", "yanbu": "ينبع", "tabuk": "تبوك", "neom": "نيوم", "abha": "أبها",
           "taif": "الطائف", "al ahsa": "الأحساء", "alahsa": "الأحساء", "hofuf": "الأحساء", "ras tanura": "رأس تنورة",
           "abqaiq": "بقيق", "kaec": "مدينة الملك عبدالله الاقتصادية", "king abdullah economic city": "مدينة الملك عبدالله الاقتصادية",
           "thuwal": "ثول", "qassim": "القصيم", "buraydah": "القصيم", "jazan": "جازان", "najran": "نجران", "hail": "حائل"}

def guess_city(loc):
    """يطلع أول مدينة سعودية معروفة من نص الموقع (مثل «SA - Riyadh» أو «Dhahran, Saudi Arabia»)."""
    low = (loc or "").lower()
    best = None
    for k in CITY_AR:
        i = low.find(k)
        if i >= 0 and (best is None or i < best[0] or (i == best[0] and len(k) > len(best[1]))):
            best = (i, k)
    return best[1] if best else ""

FIELD_RULES = [
    ("cyber",       r"secur|cyber|\bgrc\b|\bsoc\b|infosec|fraud"),
    ("data",        r"\bdata\b|\bai\b|\bml\b|machine learning|analytic|data scien|\bbi\b"),
    ("tech",        r"software|developer|devops|\bqa\b|frontend|backend|front-end|back-end|\bios\b|android|\bsre\b|\bit\b|cloud|network|digital|technology|systems? engineer|تقنية"),
    ("health",      r"pharma|nurs|medical|clinic|health|biolog|chemist|laborator|lab tech|dental|physio|hospital|صيدل|تمريض|صحي|طبي|مختبر"),
    ("engineering", r"engineer|mechanical|electrical|civil|chemical|industrial|petroleum|process|structural|mechatronic|instrument|maintenance|construction|\bhse\b|operations technician|هندس"),
    ("finance",     r"financ|account|audit|\btax\b|treasury|bank|credit|risk|investment|actuar|deals|valuation|compliance|مالي|محاسب|مراجع|تدقيق|مخاطر|بنك|استثمار"),
    ("legal",       r"legal|law|lawyer|paralegal|contract|قانون|قانوني|محام"),
    ("supply",      r"supply chain|procure|purchas|logistic|warehouse|inventory|sourcing|planning analyst|مشتريات|سلاسل|لوجست|مستودع"),
    ("product",     r"product|design|\bux\b|\bui\b"),
    ("marketing",   r"marketing|sales|brand|campaign|growth|business development|تسويق|مبيعات"),
    ("media",       r"content|social|video|creative|media|journalis|محتوى|إعلام"),
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
KW_STOP = set("""a an and are as at be been being but by can could do does for from has have having he her his how i if in into is it its may more most must no not of on or our out over own per should so some such than that the their them then there these they this those to under up us very was we were what when where which while who will with within without would you your about above across after again against all also among any because before below between both during each few further here just less many much only other same shall since still through too until upon via whether yet able ability abilities work working works job role roles team teams company candidate candidates looking join years year experience experiences strong good great excellent knowledge understanding skills skill including include includes using use used new well etc responsibilities responsibility qualifications qualification requirements required preferred plus bonus opportunity degree related field fields based ensure support day days key help make level levels familiarity familiar bachelor bachelors master masters riyadh jeddah dammam khobar saudi arabia ksa junior senior intern interns internship graduate graduates fresh entry full time part hybrid remote onsite apply applicants ideal minimum preferably proven solid demonstrated similar equivalent month months week weeks program training trainee opportunity opportunities environment offer offers benefits competitive salary join growing fast leading platform customers customer clients client people business across world region mena gcc need needs seeking want wants looking ideally students student welcome welcomed one two best right clear existing basic learn learning assist updates written evidence problems processes develop developing development organisations organizations tools office partners relationships technical technologies products tech someone curious expected real rather run runs operate operating closely provide providing motivated motivation issues issue hands-on improvement improvements results result tasks task critical exposure practices practice environments associate modern high-quality programme ownership collaborating collaborate collaboration squads designers engineers managers engineer manager passionate passion eager excited exciting driven self-starter detail-oriented dynamic fast-paced thrive impact impactful meaningful various multiple ensure ensuring deliver delivering related day-to-day across end-to-end world-class cutting-edge innovative mindset attitude values culture mission vision goals goal ways way things thing part parts high low large small big key main core daily weekly monthly timely quickly effectively efficiently successfully highly closely directly actively proactive proactively ability contribute contributing gain gaining exposure hands""" .split())
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

# ---------- الأنظمة الكبيرة: Workday وOracle وSuccessFactors ----------
UA = {"User-Agent": "Mozilla/5.0 (compatible; awal-khatwa-bot/1.0; +https://saraalzhrani7.github.io/Awal-khatwa/)"}

def post_json(url, body):
    req = urllib.request.Request(url, data=json.dumps(body).encode("utf-8"), method="POST",
                                 headers={**UA, "Accept": "application/json", "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=40) as r:
        return json.loads(r.read().decode("utf-8"))

def get_text(url):
    req = urllib.request.Request(url, headers={**UA, "Accept": "text/html,application/xml;q=0.9,*/*;q=0.8"})
    with urllib.request.urlopen(req, timeout=40) as r:
        return r.read().decode("utf-8", "replace")

MONTHS = {m: i for i, m in enumerate(["jan","feb","mar","apr","may","jun","jul","aug","sep","oct","nov","dec"], 1)}
def _date(s):
    """يحول تاريخ مثل 2026-09-22 أو Sep 22, 2026 أو Tue, 22 Sep 2026 إلى 2026-09-22."""
    s = (s or "").strip()
    m = re.search(r"(20\d{2})-(\d{2})-(\d{2})", s)
    if m: return m.group(0)
    m = re.search(r"([A-Za-z]{3})[a-z]*\.?\s+(\d{1,2}),?\s+(20\d{2})", s)
    if m and m.group(1).lower() in MONTHS: return f"{m.group(3)}-{MONTHS[m.group(1).lower()]:02d}-{int(m.group(2)):02d}"
    m = re.search(r"(\d{1,2})\s+([A-Za-z]{3})[a-z]*\.?\s+(20\d{2})", s)
    if m and m.group(2).lower() in MONTHS: return f"{m.group(3)}-{MONTHS[m.group(2).lower()]:02d}-{int(m.group(1)):02d}"
    return ""

def fetch_workday(src):
    host, tenant, site = src["host"], src["tenant"], src["site"]
    base = f"https://{host}/wday/cxs/{tenant}/{site}"
    seen = {}
    for q in (GLOBAL_TERMS if src.get("global") else SEARCH_TERMS):
        offset = 0
        while offset < 100:
            d = post_json(base + "/jobs", {"appliedFacets": {}, "limit": 20, "offset": offset, "searchText": q})
            posts = d.get("jobPostings") or []
            for p in posts:
                if p.get("externalPath"):
                    seen.setdefault(p["externalPath"], p)
            offset += 20
            if len(posts) < 20 or offset >= (d.get("total") or 0):
                break
    for path, p in seen.items():
        title = p.get("title", "")
        if not is_beginner(title):
            continue
        try:
            info = (get_json(base + path) or {}).get("jobPostingInfo") or {}
        except Exception as e:
            print(f"   (ما قدرنا نقرأ تفاصيل {title}: {e})", file=sys.stderr)
            info = {}
        locs = [info.get("location") or p.get("locationsText") or ""] + list(info.get("additionalLocations") or [])
        country = (info.get("country") or {}).get("descriptor", "")
        loc = " ".join(filter(None, locs + [country]))
        yield dict(title=title, url=info.get("externalUrl") or f"https://{host}/en-US/{site}{path}", location=loc,
                   city=guess_city(loc), experience="", dept="", deadline=(info.get("endDate") or "")[:10],
                   posted=(info.get("startDate") or "")[:10], remote=bool(re.search(r"remote", loc, re.I)),
                   desc=strip_html(info.get("jobDescription")))

def fetch_oracle(src):
    host, site = src["host"], src["site"]
    seen = {}
    for q in (GLOBAL_TERMS if src.get("global") else SEARCH_TERMS):
        finder = urllib.parse.quote(f'findReqs;siteNumber={site},limit=50,keyword="{q}",sortBy=POSTING_DATES_DESC', safe="")
        d = get_json(f"https://{host}/hcmRestApi/resources/latest/recruitingCEJobRequisitions?onlyData=true&expand=requisitionList&finder={finder}")
        for it in d.get("items", []):
            for r in it.get("requisitionList") or []:
                if r.get("Id"):
                    seen.setdefault(str(r["Id"]), r)
    for rid, r in seen.items():
        loc = " ".join(filter(None, [r.get("PrimaryLocation"), "Saudi Arabia" if (r.get("PrimaryLocationCountry") or "").upper() == "SA" else ""]))
        end = (r.get("PostingEndDate") or "")[:10]
        yield dict(title=r.get("Title", ""), url=f"https://{host}/hcmUI/CandidateExperience/en/sites/{site}/job/{rid}",
                   location=loc, city=guess_city(loc), experience="", dept=r.get("JobFamily") or r.get("JobFunction") or "",
                   deadline=end if end and end < "2100" else "", posted=(r.get("PostedDate") or "")[:10], remote=False,
                   desc=strip_html(" ".join(filter(None, [r.get("ShortDescriptionStr"), r.get("ExternalResponsibilitiesStr"), r.get("ExternalQualificationsStr")]))))

def _sf_rss(xml, dom):
    rows = []
    for item in re.findall(r"<item>(.*?)</item>", xml, flags=re.S):
        g = lambda tag: html.unescape(re.sub(r"<!\[CDATA\[|\]\]>", "", (re.search(rf"<{tag}[^>]*>(.*?)</{tag}>", item, flags=re.S) or [None, ""])[1])).strip()
        title, link, desc = g("title"), g("link"), strip_html(g("description"))
        m = re.match(r"^(.*?)\s*\(([^()]*)\)\s*$", title)   # «المسمى (المدينة، SA)»
        loc = m.group(2) if m else ""
        if m: title = m.group(1)
        rows.append({"title": title, "url": link, "location": f"{loc} {desc[:300]}", "posted": _date(g("pubDate"))})
    return rows

def _sf_html(page, dom):
    rows = []
    for chunk in re.split(r'<tr[^>]*class="[^"]*data-row', page)[1:]:
        a = re.search(r'<a[^>]*href="(/[^"]*?/job/[^"]+|/job/[^"]+)"[^>]*>(.*?)</a>', chunk, flags=re.S)
        if not a: continue
        loc = re.search(r'class="jobLocation[^"]*"[^>]*>(.*?)</span>', chunk, flags=re.S)
        dt = re.search(r'class="jobDate[^"]*"[^>]*>(.*?)</span>', chunk, flags=re.S)
        rows.append({"title": strip_html(a.group(2)).strip(), "url": f"https://{dom}{a.group(1)}",
                     "location": strip_html(loc.group(1)).strip() if loc else "", "posted": _date(strip_html(dt.group(1)) if dt else "")})
    return rows

def _sf_desc(url):
    page = get_text(url)
    m = re.search(r'class="jobdescription"[^>]*>(.*?)</span>\s*</div>', page, flags=re.S) or re.search(r'itemprop="description"[^>]*>(.*?)</(?:span|div)>\s*</div>', page, flags=re.S)
    return strip_html(m.group(1)) if m else ""

def fetch_successfactors(src):
    dom, path = src["domain"], src.get("path", "")
    extra = f"&locationsearch={urllib.parse.quote(src['loc'])}" if src.get("loc") else ""
    seen = {}
    for q in SEARCH_TERMS:
        rows = []
        try:
            xml = get_text(f"https://{dom}{path}/services/rss/job/?locale=en_US&keywords={urllib.parse.quote(q)}{extra}")
            if "<item" in xml:
                rows = _sf_rss(xml, dom)
        except Exception:
            rows = []
        if not rows:
            rows = _sf_html(get_text(f"https://{dom}{path}/search/?q={urllib.parse.quote(q)}&locale=en_US&sortColumn=referencedate&sortDirection=desc{extra}"), dom)
        for r in rows:
            seen.setdefault(r["url"], r)
    for url, r in seen.items():
        loc = re.sub(r",\s*SA\b", ", Saudi Arabia", r["location"])
        yield dict(title=r["title"], url=url, location=loc, city=guess_city(loc), experience="", dept="", deadline="",
                   posted=r.get("posted", ""), remote=bool(re.search(r"remote", loc, re.I)),
                   desc=None, load_desc=(lambda u=url: _sf_desc(u)))

FETCHERS = {"workable": fetch_workable, "greenhouse": fetch_greenhouse, "ashby": fetch_ashby,
            "pinpoint": fetch_pinpoint, "smartrecruiters": fetch_smartrecruiters,
            "workday": fetch_workday, "oracle": fetch_oracle, "successfactors": fetch_successfactors}

# ---------- الدمج ----------
def norm_title(t):
    return re.sub(r"[^a-z0-9؀-ۿ]+", " ", (t or "").lower()).strip()

def key_of(item):
    return f"{(item.get('companyEn') or '').lower()}|{norm_title(item.get('title'))}"

def slug(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")[:60]

def main():
    old = json.loads(DATA.read_text(encoding="utf-8")) if DATA.exists() else []
    manual = expire_manual([x for x in old if x.get("source") != "auto"])
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
            if not r["url"] or not (SAUDI.search(r["location"] or "") or src.get("saudi")):
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
            c = city_ar(r["city"]) if (r.get("city") and (r["city"] or "").lower() in CITY_AR) else city_ar(guess_city(f"{r.get('city') or ''} {r['location']}") or r.get("city"))
            if k in fresh:  # نفس الإعلان في أكثر من مدينة
                if c not in fresh[k]["city"]:
                    fresh[k]["city"] += f" أو {c}"
                fresh[k]["remote"] = fresh[k]["remote"] or bool(r.get("remote"))
                continue
            prev = old_auto.get(k, {})
            item.update({
                "id": prev.get("id") or slug(f"{src['companyEn']}-{r['title']}"),
                "type": prev.get("type") or classify_type(r["title"], r["experience"]),
                "field": classify_field(f"{r['title']} {r['dept']}"),
                "org": src.get("org", ORG_DEFAULT),
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
    for x in list(fresh.values()) + manual:
        x.setdefault("org", ORG_DEFAULT)

    result = manual + sorted(fresh.values(), key=lambda x: x.get("posted", ""), reverse=True)

    record_history(result)
    write_feed(result)
    write_job_pages(result)

    def strip_dates(lst):
        return [{kk: vv for kk, vv in x.items() if kk != "checked"} for x in lst]
    if strip_dates(result) == strip_dates(old):
        print("ما فيه تغيير في الإعلانات.")
        return
    DATA.write_text(json.dumps(result, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"انحفظ: {len(manual)} يدوي + {len(fresh)} تلقائي")

# ---------- الإعلانات اليدوية: تنتهي لحالها ----------
def expire_manual(items):
    """يشيل الإعلان اليدوي إذا عدّى تاريخ "expires"، ويقفله إذا ما تحدث (checked) من فترة طويلة."""
    out = []
    limit = (datetime.date.today() - datetime.timedelta(days=MANUAL_MAX_AGE)).isoformat()
    for x in items:
        if x.get("expires") and x["expires"] < TODAY:
            print(f"   ⌛ شلنا الإعلان اليدوي «{x.get('title')}»: انتهى في {x['expires']}")
            continue
        if x.get("status") in ("open", "rolling") and not x.get("expires") and (x.get("checked") or "") < limit:
            x = dict(x, status="closed")
            print(f"   ⌛ قفلنا «{x.get('title')}»: ما تحدث من أكثر من {MANUAL_MAX_AGE} يوم")
        out.append(x)
    return out

# ---------- RSS: كل فرصة جديدة (للتطبيقات وقنوات تيليجرام) ----------
def _xml(t):
    return html.escape(str(t or ""), quote=True)

def _rfc822(d):
    try:
        dt = datetime.datetime.strptime(d, "%Y-%m-%d").replace(hour=6, tzinfo=datetime.timezone(datetime.timedelta(hours=3)))
    except Exception:
        dt = datetime.datetime.now(datetime.timezone.utc)
    return dt.strftime("%a, %d %b %Y %H:%M:%S %z")

def job_summary(x):
    parts = [TYPES_AR.get(x.get("type"), ""), x.get("city", "")]
    if x.get("deadline"):
        parts.append(f"آخر موعد {x['deadline']}")
    if x.get("paid"):
        parts.append(x["paid"])
    return " · ".join(p for p in parts if p)

def write_if_changed(path, text):
    if path.exists() and path.read_text(encoding="utf-8") == text:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return True

def write_feed(listings):
    items = sorted([x for x in listings if is_open(x)], key=lambda x: (x.get("firstSeen") or x.get("posted") or ""), reverse=True)[:60]
    rows = []
    for x in items:
        link = f"{SITE}j/{x['id']}.html"
        rows.append(f"""  <item>
    <title>{_xml(x['title'])} — {_xml(x['company'])}</title>
    <link>{_xml(link)}</link>
    <guid isPermaLink="false">awal-khatwa-{_xml(x['id'])}</guid>
    <pubDate>{_rfc822(x.get('firstSeen') or x.get('posted') or TODAY)}</pubDate>
    <description>{_xml(job_summary(x))}</description>
  </item>""")
    text = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
<channel>
  <title>أول خطوة: فرص المبتدئين في السعودية</title>
  <link>{SITE}</link>
  <description>تدريب تعاوني وInternship وبرامج خريجين ووظائف Entry Level، تتحدث كل يوم.</description>
  <language>ar</language>
{chr(10).join(rows)}
</channel>
</rss>
"""
    if write_if_changed(FEED, text):
        print(f"RSS: {len(rows)} فرصة")

# ---------- صفحة صغيرة لكل فرصة (عشان المعاينة لما أحد يشاركها) ----------
def write_job_pages(listings):
    keep = set()
    for x in listings:
        name = f"{x['id']}.html"
        keep.add(name)
        title = f"{x['title']} — {x['company']}"
        desc = job_summary(x) + " · قدّم من صفحة التوظيف الرسمية عن طريق «أول خطوة»"
        target = f"../#job-{x['id']}"
        page = f"""<!doctype html>
<html lang="ar" dir="rtl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{_xml(title)} | أول خطوة</title>
<meta name="description" content="{_xml(desc)}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="أول خطوة">
<meta property="og:title" content="{_xml(title)}">
<meta property="og:description" content="{_xml(desc)}">
<meta property="og:url" content="{SITE}j/{_xml(name)}">
<meta property="og:image" content="{SITE}og-image.jpg?v=2">
<meta name="twitter:card" content="summary_large_image">
<link rel="canonical" href="{SITE}#job-{_xml(x['id'])}">
<meta http-equiv="refresh" content="0; url={_xml(target)}">
<script>location.replace({json.dumps(target)});</script>
</head>
<body style="font-family:system-ui,sans-serif;padding:24px">
<p><a href="{_xml(target)}">{_xml(title)}</a></p>
</body>
</html>
"""
        write_if_changed(JOBS_DIR / name, page)
    if JOBS_DIR.exists():
        for f in JOBS_DIR.glob("*.html"):
            if f.name not in keep:
                f.unlink()

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

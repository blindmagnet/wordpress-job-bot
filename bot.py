"""
WordPress Job Scraper Bot v5.1
================================
تنظیم‌شده برای: Ghazaleh Ghasemzadeh
هدف: WordPress Developer / WooCommerce Specialist — Remote

منابع:
  • Remotive.com
  • Jobicy.com
  • Arbeitnow
  • Adzuna (با API key)
  • FindWork.dev
  • Cloudflare Worker (اختیاری)
  • JSearch via RapidAPI (اختیاری)

متغیرهای محیطی (GitHub Secrets):
  TELEGRAM_BOT_TOKEN   — اجباری
  TELEGRAM_CHAT_ID     — اجباری
  RAPIDAPI_KEY         — اختیاری
  GSHEET_CREDENTIALS   — اختیاری (JSON)
  GSHEET_ID            — اختیاری
  CF_WORKER_URL        — اختیاری
  ADZUNA_APP_ID        — اختیاری
  ADZUNA_API_KEY       — اختیاری
"""

import html
import json
import logging
import os
import re
import time
import traceback
import urllib.parse
from collections import OrderedDict
from datetime import datetime, timezone
from pathlib import Path

import requests
from dotenv import load_dotenv

try:
    import gspread
    from google.oauth2.service_account import Credentials
    SHEETS_AVAILABLE = True
except ImportError:
    SHEETS_AVAILABLE = False

SCRIPT_DIR = Path(__file__).parent

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[logging.StreamHandler()],
)
log = logging.getLogger(__name__)

load_dotenv()

TELEGRAM_TOKEN   = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")

if not TELEGRAM_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN not set")
if not TELEGRAM_CHAT_ID:
    raise ValueError("TELEGRAM_CHAT_ID not set")

RAPIDAPI_KEY       = os.environ.get("RAPIDAPI_KEY", "")
GSHEET_CREDENTIALS = os.environ.get("GSHEET_CREDENTIALS", "")
GSHEET_ID          = os.environ.get("GSHEET_ID", "")
GSHEET_SHEET_NAME  = "Jobs"

CF_WORKER_URL    = os.environ.get("CF_WORKER_URL", "")
ADZUNA_APP_ID    = os.environ.get("ADZUNA_APP_ID", "")
ADZUNA_API_KEY   = os.environ.get("ADZUNA_API_KEY", "")

SEEN_JOBS_FILE   = SCRIPT_DIR / "seen_jobs.txt"
MAX_SEEN_JOBS    = 3000
MAX_JOBS_PER_RUN = 20
MIN_FIT_SCORE    = 30
MAX_JOB_AGE_DAYS = 5

# ── کوئری‌های JSearch برای WordPress Developer ──────────────────────────────
JSEARCH_QUERIES = {
    1: [
        "WordPress developer remote",
        "WooCommerce developer remote",
        "WordPress PHP developer remote",
    ],
    2: [
        "WordPress plugin developer remote",
        "WordPress theme developer remote",
        "PHP WordPress developer freelance remote",
    ],
    3: [
        "Python Django developer remote",
        "full stack PHP developer remote",
        "WordPress WooCommerce specialist remote",
    ],
}

# ── مهارت‌های Ghazaleh ───────────────────────────────────────────────────────
_DEFAULT_SKILLS = [
    "wordpress", "woocommerce", "php", "python", "django",
    "javascript", "jquery", "html", "css", "rest api",
    "mysql", "postgresql", "sqlite", "git", "github",
    "ajax", "oop", "plugin development", "elementor",
    "gsap", "responsive design", "rtl", "seo",
    "hooks", "filters", "shortcodes", "wp-cron",
    "theme development", "custom plugin", "woodmart",
]

_user_skills_env = os.environ.get("USER_SKILLS", "")
MY_SKILLS = (
    [s.strip().lower() for s in _user_skills_env.split(",") if s.strip()]
    if _user_skills_env
    else _DEFAULT_SKILLS
)

# ── کلمات Blacklist ──────────────────────────────────────────────────────────
BLACKLIST_KEYWORDS = [
    # محدودیت موقعیت جغرافیایی
    "us residents only",
    "must reside in us",
    "must be based in the us",
    "us only",
    "uk only",
    "eu only",
    "europe only",
    "must be authorized to work",
    "work authorization",
    "visa sponsorship not",
    "no visa",
    # سطح ارشد
    "senior developer",
    "lead developer",
    "principal developer",
    "head of",
    "director of",
    "vp of",
    "10+ years",
    "8+ years",
    "7+ years",
    "6+ years",
    # نامرتبط
    "native english only",
    "react native",
    "ios developer",
    "android developer",
    "mobile developer",
    "data scientist",
    "machine learning engineer",
    "devops engineer",
    "blockchain developer",
]

# ── کلمات Boost با امتیاز ────────────────────────────────────────────────────
BOOST_KEYWORDS = {
    # هسته اصلی
    "wordpress":          25,
    "woocommerce":        25,
    "php":                18,
    "plugin":             15,
    "plugin development": 18,
    "theme development":  15,
    "custom theme":       15,
    "custom plugin":      18,
    # فریمورک‌ها
    "python":             12,
    "django":             12,
    # سطح تجربه
    "junior":             20,
    "entry level":        18,
    "entry-level":        18,
    "mid level":          10,
    "mid-level":          10,
    "associate":          12,
    # نوع کار
    "part-time":          12,
    "contract":           10,
    "freelance":          10,
    "remote-first":       10,
    "fully remote":       10,
    "async":               8,
    "flexible":            6,
    # فنی
    "rest api":           10,
    "elementor":           8,
    "woocommerce store":  15,
    "e-commerce":         10,
    "ecommerce":          10,
}

_SKILL_PATTERNS   = {s: re.compile(r"\b" + re.escape(s) + r"\b", re.I) for s in MY_SKILLS}
_BOOST_PATTERNS   = {kw: re.compile(r"\b" + re.escape(kw) + r"\b", re.I) for kw in BOOST_KEYWORDS}
_BLACKLIST_PATTERNS = {kw: re.compile(r"\b" + re.escape(kw.lower()) + r"\b", re.I) for kw in BLACKLIST_KEYWORDS}

# ── کلمات کلیدی WordPress برای فیلتر منابع رایگان ───────────────────────────
WP_TERMS = [
    "wordpress", "woocommerce", "php developer", "wp developer",
    "web developer", "plugin developer", "theme developer",
    "full stack", "backend developer", "frontend developer",
    "web designer", "elementor", "django", "python developer",
]

# ── Prompt Template ──────────────────────────────────────────────────────────
CL_PROMPT_TEMPLATE = os.environ.get("CL_PROMPT", "")

def load_prompt_template() -> str:
    if CL_PROMPT_TEMPLATE:
        return CL_PROMPT_TEMPLATE.strip()
    try:
        prompt_file = SCRIPT_DIR / "prompt.txt"
        if prompt_file.exists():
            content = prompt_file.read_text(encoding="utf-8").strip()
            if content:
                return content
    except Exception as e:
        log.warning(f"Could not load prompt.txt: {e}")
    # پیش‌فرض برای Ghazaleh
    return (
        "Write a professional cover letter for the {title} position at {company}.\n\n"
        "About the applicant:\n"
        "- Name: Ghazaleh Ghasemzadeh\n"
        "- Role: WordPress Developer & WooCommerce Specialist\n"
        "- Location: Tehran, Iran (open to remote)\n"
        "- Skills: WordPress, WooCommerce, PHP (OOP), Python, Django, "
        "JavaScript, jQuery, AJAX, MySQL, REST API, Git, Elementor\n\n"
        "Key experience:\n"
        "- Built full WooCommerce store from scratch at Lavazemito.ir\n"
        "- Custom warranty plugin for bekohome.com (PHP, OOP, MySQL)\n"
        "- E-commerce Telegram bot (Python, SQLite, ZarinPal)\n"
        "- Freelance WordPress projects via Karlancer\n"
        "- Portfolio: awoodhome.ir, bekohome.com\n\n"
        "Job link: {url}\n\n"
        "Write a concise cover letter (3 paragraphs max). "
        "Be specific. No generic filler phrases."
    )

# ── Seen Jobs Cache ──────────────────────────────────────────────────────────
def load_seen_jobs() -> OrderedDict:
    seen = OrderedDict()
    if SEEN_JOBS_FILE.exists():
        for line in SEEN_JOBS_FILE.read_text(encoding="utf-8").splitlines():
            if line.strip():
                seen[line.strip()] = True
        log.info(f"Loaded {len(seen)} seen IDs")
    else:
        log.info("No cache — starting fresh")
    return seen

def save_seen_jobs(seen: OrderedDict) -> None:
    ids = list(seen.keys())
    if len(ids) > MAX_SEEN_JOBS:
        ids = ids[-MAX_SEEN_JOBS:]
    SEEN_JOBS_FILE.write_text("\n".join(ids), encoding="utf-8")
    log.info(f"Saved {len(ids)} IDs to cache")

# ── Fit Score ────────────────────────────────────────────────────────────────
def calculate_fit_score(job: dict) -> tuple:
    score = 0
    matched_skills = []
    title    = (job.get("title") or "").lower()
    desc     = (job.get("description") or "").lower()
    combined = f"{title} {desc}"

    for kw, pts in BOOST_KEYWORDS.items():
        if _BOOST_PATTERNS[kw].search(combined):
            score += pts

    for skill in MY_SKILLS:
        if _SKILL_PATTERNS[skill].search(combined):
            matched_skills.append(skill)
            score += 7

    # بونوس‌های اضافه
    if re.search(r"\bwordpress\b", title):
        score += 15
    if re.search(r"\bwoocommerce\b", title):
        score += 15
    if re.search(r"\bphp\b", title):
        score += 10
    if job.get("salary"):
        score += 8
    if job.get("remote"):
        score += 6
    if any(re.search(r"\b" + w + r"\b", title) for w in ["junior", "associate", "entry", "jr"]):
        score += 12

    return min(score, 100), matched_skills[:5]

# ── منابع رایگان ─────────────────────────────────────────────────────────────

def fetch_remotive() -> list:
    endpoints = [
        "https://remotive.com/api/remote-jobs?category=software-dev&limit=30",
        "https://remotive.com/api/remote-jobs?search=wordpress&limit=20",
        "https://remotive.com/api/remote-jobs?search=woocommerce&limit=10",
        "https://remotive.com/api/remote-jobs?search=php+developer&limit=15",
    ]
    results = []
    for url in endpoints:
        try:
            resp = requests.get(url, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
            resp.raise_for_status()
            for j in resp.json().get("jobs", []):
                title = (j.get("title") or "").lower()
                desc  = (j.get("description") or "").lower()[:300]
                if not any(t in title or t in desc for t in WP_TERMS):
                    continue
                results.append({
                    "id":           f"remotive_{j.get('id', '')}",
                    "title":        j.get("title", ""),
                    "company":      j.get("company_name", ""),
                    "description":  j.get("description", ""),
                    "salary":       j.get("salary", ""),
                    "remote":       True,
                    "url":          j.get("url", ""),
                    "source":       "Remotive",
                    "source_emoji": "🌐",
                    "posted_at":    (j.get("publication_date") or "")[:10],
                    "location":     "Remote",
                })
        except Exception as e:
            log.error(f"Remotive error: {e}")
        time.sleep(1)
    log.info(f"Remotive -> {len(results)} jobs")
    return results

def fetch_jobicy() -> list:
    endpoints = [
        "https://jobicy.com/api/v2/remote-jobs?tag=wordpress&count=20",
        "https://jobicy.com/api/v2/remote-jobs?tag=php&count=20",
        "https://jobicy.com/api/v2/remote-jobs?tag=woocommerce&count=10",
        "https://jobicy.com/api/v2/remote-jobs?tag=web-development&count=15",
    ]
    results = []
    for url in endpoints:
        try:
            resp = requests.get(url, timeout=15)
            resp.raise_for_status()
            for j in resp.json().get("jobs", []):
                title = (j.get("jobTitle") or "").lower()
                desc  = (j.get("jobDescription") or "").lower()[:300]
                if not any(t in title or t in desc for t in WP_TERMS):
                    continue
                lo  = j.get("annualSalaryMin")
                hi  = j.get("annualSalaryMax")
                cur = j.get("annualSalaryCurrency", "USD")
                sal = (
                    f"{cur} {int(lo):,}-{int(hi):,}/yr" if lo and hi
                    else (f"{cur} {int(lo):,}+/yr" if lo else "")
                )
                results.append({
                    "id":           f"jobicy_{j.get('id', '')}",
                    "title":        j.get("jobTitle", ""),
                    "company":      j.get("companyName", ""),
                    "description":  j.get("jobDescription", ""),
                    "salary":       sal,
                    "remote":       True,
                    "url":          j.get("url", ""),
                    "source":       "Jobicy",
                    "source_emoji": "🟢",
                    "posted_at":    (j.get("pubDate") or "")[:10],
                    "location":     "Remote",
                })
        except Exception as e:
            log.error(f"Jobicy error: {e}")
        time.sleep(1)
    log.info(f"Jobicy -> {len(results)} jobs")
    return results

def fetch_arbeitnow() -> list:
    try:
        resp = requests.get(
            "https://arbeitnow.com/api/job-board-api",
            timeout=15,
            headers={"User-Agent": "Mozilla/5.0"},
        )
        resp.raise_for_status()
        results = []
        for j in resp.json().get("data", []):
            if not j.get("remote"):
                continue
            title = (j.get("title") or "").lower()
            desc  = (j.get("description") or "").lower()[:300]
            if not any(t in title or t in desc for t in WP_TERMS):
                continue
            results.append({
                "id":           f"arbeitnow_{j.get('slug', '')}",
                "title":        j.get("title", ""),
                "company":      j.get("company_name", ""),
                "description":  j.get("description", ""),
                "salary":       "",
                "remote":       True,
                "url":          j.get("url", ""),
                "source":       "Arbeitnow",
                "source_emoji": "🔷",
                "posted_at":    datetime.now(timezone.utc).strftime("%Y-%m-%d"),
                "location":     "Remote",
            })
        log.info(f"Arbeitnow -> {len(results)} jobs")
        return results
    except Exception as e:
        log.error(f"Arbeitnow error: {e}")
        return []

def fetch_adzuna() -> list:
    if not ADZUNA_APP_ID or not ADZUNA_API_KEY:
        return []
    results = []
    for q in ["wordpress developer", "woocommerce developer", "php wordpress"]:
        try:
            resp = requests.get(
                "https://api.adzuna.com/v1/api/jobs/us/search/1",
                params={
                    "app_id": ADZUNA_APP_ID,
                    "app_key": ADZUNA_API_KEY,
                    "what": q,
                    "what_or": "remote",
                    "max_days_old": 5,
                    "results_per_page": 15,
                    "content-type": "application/json",
                },
                timeout=15,
            )
            resp.raise_for_status()
            for j in resp.json().get("results", []):
                salary = ""
                if j.get("salary_min"):
                    lo = int(float(j["salary_min"]))
                    hi = int(float(j.get("salary_max") or j["salary_min"]))
                    salary = f"${lo:,}-${hi:,}/yr"
                results.append({
                    "id":           f"adzuna_{j.get('id', '')}",
                    "title":        j.get("title", ""),
                    "company":      (j.get("company") or {}).get("display_name", ""),
                    "description":  j.get("description", ""),
                    "salary":       salary,
                    "remote":       True,
                    "url":          j.get("redirect_url", ""),
                    "source":       "Adzuna",
                    "source_emoji": "🟡",
                    "posted_at":    (j.get("created") or "")[:10],
                    "location":     j.get("location", {}).get("display_name", "Remote"),
                })
        except Exception as e:
            log.error(f"Adzuna error ({q}): {e}")
        time.sleep(1)
    log.info(f"Adzuna -> {len(results)} jobs")
    return results

def fetch_findwork() -> list:
    try:
        resp = requests.get(
            "https://findwork.dev/api/jobs/",
            params={"search": "wordpress", "remote": "true", "order_by": "-date_posted"},
            headers={"User-Agent": "Mozilla/5.0 (compatible; WPJobBot/5.1)"},
            timeout=15,
        )
        if resp.status_code == 403:
            log.warning("FindWork.dev: access denied")
            return []
        resp.raise_for_status()
        results = []
        for j in resp.json().get("results", []):
            title = (j.get("role") or "").lower()
            desc  = (j.get("text") or "").lower()[:500]
            if not any(t in title or t in desc for t in WP_TERMS):
                continue
            results.append({
                "id":           f"findwork_{j.get('id', '')}",
                "title":        j.get("role", ""),
                "company":      j.get("company_name", ""),
                "description":  j.get("text", ""),
                "salary":       "",
                "remote":       j.get("remote", True),
                "url":          j.get("url", ""),
                "source":       "FindWork",
                "source_emoji": "🟣",
                "posted_at":    (j.get("date_posted") or "")[:10],
                "location":     j.get("location") or "Remote",
            })
        log.info(f"FindWork -> {len(results)} jobs")
        return results
    except Exception as e:
        log.error(f"FindWork error: {e}")
        return []

def fetch_cloudflare_worker() -> list:
    if not CF_WORKER_URL:
        return []
    worker_url = CF_WORKER_URL.rstrip("/")
    if not worker_url.endswith("/jobs"):
        worker_url += "/jobs"
    try:
        resp = requests.get(worker_url, headers={"User-Agent": "WPJobBot/5.1"}, timeout=20)
        if resp.status_code in (401, 404):
            log.error(f"CF Worker: {resp.status_code}")
            return []
        resp.raise_for_status()
        data = resp.json()
        if data.get("status") != "ok":
            return []
        jobs = []
        for j in data.get("jobs", []):
            if not j.get("id") or not j.get("title"):
                continue
            jobs.append({
                "id":           str(j.get("id", "")),
                "title":        j.get("title", ""),
                "company":      j.get("company", ""),
                "description":  j.get("description", ""),
                "salary":       j.get("salary", ""),
                "remote":       j.get("remote", True),
                "url":          j.get("url", ""),
                "source":       j.get("source", "CF Worker"),
                "source_emoji": j.get("source_emoji", "☁️"),
                "posted_at":    (j.get("posted_at") or "")[:10],
                "location":     j.get("location", "Remote"),
            })
        log.info(f"CF Worker -> {len(jobs)} jobs")
        return jobs
    except Exception as e:
        log.error(f"CF Worker error: {e}")
        return []

# ── JSearch API ──────────────────────────────────────────────────────────────
def _should_run_p3() -> bool:
    return datetime.now(timezone.utc).day % 2 == 0

def search_jsearch(query: str) -> list:
    if not RAPIDAPI_KEY:
        return []
    url = "https://jsearch.p.rapidapi.com/search"
    headers = {
        "x-rapidapi-key": RAPIDAPI_KEY,
        "x-rapidapi-host": "jsearch.p.rapidapi.com",
    }
    params = {
        "query": query,
        "num_pages": "1",
        "date_posted": "week",
        "work_from_home": "true",
    }
    for attempt in range(1, 4):
        try:
            resp = requests.get(url, headers=headers, params=params, timeout=20)
            if resp.status_code == 429:
                log.warning("JSearch rate limit — waiting 60s")
                time.sleep(60)
                continue
            if resp.status_code == 403:
                log.error("JSearch 403")
                return []
            resp.raise_for_status()
            data = resp.json()
            if data.get("status") != "OK":
                return []
            return [_normalize_jsearch(j) for j in data.get("data", [])]
        except requests.exceptions.Timeout:
            log.warning(f"JSearch timeout {attempt}/3")
        except Exception as e:
            log.error(f"JSearch error: {e}")
            return []
        if attempt < 3:
            time.sleep(5 * attempt)
    return []

def _normalize_jsearch(j: dict) -> dict:
    salary = j.get("job_salary_string", "")
    if not salary and j.get("job_min_salary"):
        lo  = int(j["job_min_salary"])
        hi  = int(j.get("job_max_salary") or lo)
        per = {"year": "/yr", "month": "/mo", "hour": "/hr"}.get(
            (j.get("job_salary_period") or "").lower(), ""
        )
        salary = f"${lo:,}-${hi:,}{per}" if lo != hi else f"${lo:,}+{per}"

    city    = j.get("job_city") or ""
    country = j.get("job_country") or ""
    loc     = ", ".join(p for p in (city, country) if p) or "Remote"

    return {
        "id":           j.get("job_id", ""),
        "title":        j.get("job_title", ""),
        "company":      j.get("employer_name", ""),
        "description":  j.get("job_description", ""),
        "salary":       salary,
        "remote":       True,
        "url":          j.get("job_apply_link") or j.get("job_google_link") or "",
        "source":       j.get("job_publisher", "JSearch"),
        "source_emoji": "🔍",
        "posted_at":    (j.get("job_posted_at_datetime_utc") or "")[:10],
        "location":     loc,
    }

# ── Filters ──────────────────────────────────────────────────────────────────
def is_blacklisted(job: dict) -> tuple:
    text = f"{(job.get('title') or '').lower()} {(job.get('description') or '')[:2000].lower()}"
    for kw, pattern in _BLACKLIST_PATTERNS.items():
        if pattern.search(text):
            return True, kw
    return False, ""

def is_too_old(job: dict) -> bool:
    posted = (job.get("posted_at") or "")[:10]
    if not posted:
        return False
    try:
        dt = datetime.strptime(posted, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        return (datetime.now(timezone.utc) - dt).days > MAX_JOB_AGE_DAYS
    except Exception:
        return False

# ── Telegram ─────────────────────────────────────────────────────────────────
def _score_bar(score: int) -> str:
    filled = round(score / 10)
    return "█" * filled + "░" * (10 - filled)

def format_job(job: dict, score: int, skills: list) -> str:
    title   = html.escape(job.get("title") or "No Title")
    company = html.escape(job.get("company") or "Unknown")
    salary  = job.get("salary") or ""
    source  = html.escape(job.get("source") or "")
    semoji  = job.get("source_emoji", "🌐")
    posted  = job.get("posted_at") or ""
    loc     = html.escape(job.get("location") or "Remote")

    lines = [
        f"💼 <b>{title}</b>",
        f"🏢 {company}",
        f"📍 {loc}",
    ]
    if salary:
        lines.append(f"💰 <b>{html.escape(str(salary))}</b>")
    lines.append(f"📊 {_score_bar(score)} {score}/100")
    if skills:
        lines.append(f"✅ {', '.join(html.escape(s) for s in skills)}")
    lines.append(f"{semoji} {source}")
    if posted:
        lines.append(f"📅 {posted}")

    return "\n".join(lines)

def build_job_buttons(job: dict) -> dict:
    url = job.get("url", "")
    if not url:
        return {}

    title   = job.get("title", "")
    company = job.get("company", "")

    template    = load_prompt_template()
    prompt      = template.format(title=title, company=company, url=url)
    safe_prompt = urllib.parse.quote(prompt)
    chatgpt_url = f"https://chatgpt.com/?q={safe_prompt}"

    return {"inline_keyboard": [
        [{"text": "📝 Apply Now", "url": url}],
        [{"text": "🤖 ChatGPT Cover Letter", "url": chatgpt_url}],
    ]}

def send_telegram(text: str, reply_markup: dict = None, _retries: int = 3) -> bool:
    api_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id":    TELEGRAM_CHAT_ID,
        "text":       text,
        "parse_mode": "HTML",
        "link_preview_options": {"is_disabled": True},
    }
    if reply_markup:
        payload["reply_markup"] = reply_markup

    for attempt in range(1, _retries + 1):
        try:
            resp = requests.post(api_url, json=payload, timeout=15)
            if resp.ok:
                return True
            if resp.status_code == 429:
                retry_after = resp.json().get("parameters", {}).get("retry_after", 30)
                log.warning(f"Telegram Flood — sleeping {retry_after}s")
                time.sleep(retry_after + 1)
                continue
            log.error(f"Telegram {resp.status_code}: {resp.text[:200]}")
            return False
        except requests.exceptions.Timeout:
            log.warning(f"Telegram timeout ({attempt}/{_retries})")
            if attempt < _retries:
                time.sleep(3)
        except Exception as e:
            log.error(f"Telegram error: {e}")
            return False
    return False

# ── Google Sheets ─────────────────────────────────────────────────────────────
def get_sheets_client():
    if not SHEETS_AVAILABLE or not GSHEET_CREDENTIALS or not GSHEET_ID:
        return None
    try:
        creds = Credentials.from_service_account_info(
            json.loads(GSHEET_CREDENTIALS),
            scopes=[
                "https://www.googleapis.com/auth/spreadsheets",
                "https://www.googleapis.com/auth/drive",
            ],
        )
        log.info("Google Sheets connected")
        return gspread.authorize(creds)
    except Exception as e:
        log.error(f"Sheets auth error: {e}")
        return None

def ensure_sheet_headers(client) -> None:
    if not client:
        return
    try:
        sheet = client.open_by_key(GSHEET_ID).worksheet(GSHEET_SHEET_NAME)
        if not sheet.row_values(1):
            sheet.insert_row(
                ["Job Title", "Company", "Source", "Apply Link", "Posted",
                 "Salary", "Fit Score", "Location", "Saved At (UTC)", "Status"],
                1,
            )
    except Exception as e:
        log.error(f"Sheet header error: {e}")

def batch_append_to_sheet(client, rows: list) -> None:
    if not client or not rows:
        return
    try:
        sheet = client.open_by_key(GSHEET_ID).worksheet(GSHEET_SHEET_NAME)
        sheet.append_rows(rows, value_input_option="USER_ENTERED")
        log.info(f"Appended {len(rows)} rows to Sheets")
    except Exception as e:
        log.error(f"Sheet append error: {e}")

# ── Main ──────────────────────────────────────────────────────────────────────
def main() -> None:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    log.info(f"=== WordPress Job Scraper v5.1 started at {now} ===")

    seen_jobs = load_seen_jobs()
    sheets    = get_sheets_client()
    ensure_sheet_headers(sheets)

    raw_jobs     = []
    source_counts = {}

    # منابع رایگان
    for fn, name in [
        (fetch_remotive,          "Remotive"),
        (fetch_jobicy,            "Jobicy"),
        (fetch_arbeitnow,         "Arbeitnow"),
        (fetch_adzuna,            "Adzuna"),
        (fetch_findwork,          "FindWork"),
        (fetch_cloudflare_worker, "CF Worker"),
    ]:
        try:
            jobs = fn()
            source_counts[name] = len(jobs)
            raw_jobs.extend(jobs)
        except Exception as e:
            log.error(f"{name} failed: {e}\n{traceback.format_exc()}")
            source_counts[name] = 0

    # JSearch
    jsearch_total = 0
    for priority in sorted(JSEARCH_QUERIES.keys()):
        if priority == 3 and not _should_run_p3():
            log.info("Skipping P3 JSearch queries (odd day)")
            continue
        for query in JSEARCH_QUERIES[priority]:
            try:
                jobs = search_jsearch(query)
                jsearch_total += len(jobs)
                raw_jobs.extend(jobs)
            except Exception as e:
                log.error(f"JSearch '{query}': {e}")
            time.sleep(1.5)
    source_counts["JSearch"] = jsearch_total

    # فیلتر + امتیازدهی
    seen_ids   = set()
    title_keys = set()
    stats      = {"blacklisted": 0, "seen": 0, "old": 0, "low_score": 0}
    qualified  = []

    for job in raw_jobs:
        try:
            jid       = job.get("id") or job.get("url") or ""
            title_key = (
                f"{(job.get('title') or '').lower().strip()}"
                f"|{(job.get('company') or '').lower().strip()}"
            )

            if not jid:
                continue
            if jid in seen_jobs or jid in seen_ids:
                stats["seen"] += 1
                continue
            if title_key in title_keys:
                stats["seen"] += 1
                seen_ids.add(jid)
                seen_jobs[jid] = True
                continue

            seen_ids.add(jid)
            seen_jobs[jid] = True
            title_keys.add(title_key)

            bl, _ = is_blacklisted(job)
            if bl:
                stats["blacklisted"] += 1
                continue

            if is_too_old(job):
                stats["old"] += 1
                continue

            score, skills = calculate_fit_score(job)
            if score < MIN_FIT_SCORE:
                stats["low_score"] += 1
                continue

            qualified.append((job, score, skills))
        except Exception as e:
            log.error(f"Processing error: {e}")

    qualified.sort(key=lambda x: x[1], reverse=True)

    log.info(
        f"Qualified: {len(qualified)} | BL: {stats['blacklisted']} | "
        f"Seen: {stats['seen']} | Old: {stats['old']} | Low: {stats['low_score']}"
    )

    # ارسال به تلگرام
    active_sources = {k: v for k, v in source_counts.items() if v > 0}
    sources_line   = " | ".join(f"{k}: {v}" for k, v in active_sources.items())

    if not qualified:
        send_telegram(
            f"🔍 <b>Daily Report</b>\n📅 {now}\n\n"
            f"No qualified jobs found today.\n\n"
            f"📌 {sources_line or 'No sources'}\n"
            f"⛔ {stats['blacklisted']} filtered | "
            f"📉 {stats['low_score']} low score | "
            f"🔁 {stats['seen']} duplicates | "
            f"🕐 {stats['old']} old"
        )
        save_seen_jobs(seen_jobs)
        return

    send_telegram(
        f"💻 <b>WordPress Jobs — Daily Report</b>\n"
        f"📅 {now}\n\n"
        f"✅ <b>{len(qualified)}</b> jobs found (sorted by fit)\n"
        f"⛔ {stats['blacklisted']} filtered | "
        f"📉 {stats['low_score']} low | "
        f"🔁 {stats['seen']} dupes\n\n"
        f"📌 {sources_line}\n"
        f"➖➖➖➖➖➖➖➖"
    )
    time.sleep(1.5)

    sent       = 0
    sheet_rows = []

    for job, score, skills in qualified[:MAX_JOBS_PER_RUN]:
        try:
            buttons = build_job_buttons(job)
            msg     = format_job(job, score, skills)

            if send_telegram(msg, reply_markup=buttons if buttons else None):
                sent += 1
                sheet_rows.append([
                    job.get("title", ""),
                    job.get("company", ""),
                    job.get("source", ""),
                    job.get("url", ""),
                    job.get("posted_at", ""),
                    job.get("salary", ""),
                    score,
                    job.get("location", ""),
                    datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M"),
                    "New",
                ])

            time.sleep(1.5)
        except Exception as e:
            log.error(f"Send error: {e}")

    batch_append_to_sheet(sheets, sheet_rows)
    save_seen_jobs(seen_jobs)
    log.info(f"=== Done. Sent {sent}/{len(qualified)} ===")

if __name__ == "__main__":
    main()

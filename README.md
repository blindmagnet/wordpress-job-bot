<div dir="rtl">

# 🤖 WordPress Job Bot

ربات تلگرامی که هر روز صبح بهترین فرصت‌های شغلی **ریموت WordPress و WooCommerce** رو پیدا می‌کنه و مستقیم برات میفرسته.

**ساخته شده برای:** WordPress Developer هایی که دنبال کار ریموت در خارج از ایران هستن.

---

## ✨ ویژگی‌ها

- 🔍 جستجو در **۶+ منبع** شغلی به صورت همزمان
- 📊 **امتیازدهی هوشمند** بر اساس مهارت‌های تو
- 🚫 **فیلتر خودکار** آگهی‌های نامرتبط، منقضی و تکراری
- 📱 ارسال مستقیم به **تلگرام** با دکمه Apply
- 🤖 دکمه **ChatGPT Cover Letter** برای هر آگهی
- ⚙️ کاملاً **قابل شخصی‌سازی** برای هر توسعه‌دهنده
- ☁️ اجرای **رایگان** روی GitHub Actions — بدون نیاز به سرور

---

## 📸 نمونه خروجی

```
💼 WordPress Developer (Remote)
🏢 Acme Digital Agency
📍 Remote
💰 $40,000-$60,000/yr
📊 ████████░░ 82/100
✅ wordpress, woocommerce, php, elementor
🌐 Remotive
📅 2026-06-15

[📝 Apply Now]  [🤖 ChatGPT Cover Letter]
```

---

## 🚀 راه‌اندازی سریع

### پله ۱ — Fork یا Clone

روی دکمه **Fork** بالای صفحه کلیک کن تا یه کپی توی اکانت خودت بسازی.

### پله ۲ — ساخت ربات تلگرام

1. به [@BotFather](https://t.me/BotFather) برو و `/newbot` بفرست
2. یه اسم و username بده
3. **توکن** رو کپی کن
4. به ربات خودت برو و `/start` بزن
5. از [@userinfobot](https://t.me/userinfobot) **Chat ID** رو بگیر

### پله ۳ — تنظیم GitHub Secrets

توی ریپوی Fork شده:
**Settings → Secrets and variables → Actions → New repository secret**

| نام Secret | توضیح | اجباری؟ |
|-----------|-------|---------|
| `TELEGRAM_BOT_TOKEN` | توکن BotFather | ✅ |
| `TELEGRAM_CHAT_ID` | Chat ID تلگرام | ✅ |
| `RAPIDAPI_KEY` | کلید JSearch API | ❌ |
| `ADZUNA_APP_ID` | Adzuna App ID | ❌ |
| `ADZUNA_API_KEY` | Adzuna API Key | ❌ |

### پله ۴ — فعال‌سازی

**Actions → WordPress Job Bot → Enable workflow → Run workflow**

همین! از فردا هر روز ساعت ۷ صبح آگهی‌ها میان 🎉

---

## ⚙️ شخصی‌سازی

### تغییر مهارت‌ها

فایل `bot.py` رو باز کن و `_DEFAULT_SKILLS` رو ویرایش کن:

```python
_DEFAULT_SKILLS = [
    "wordpress", "woocommerce", "php", "python",
    "javascript", "elementor", "rest api",
    # مهارت‌های خودت رو اینجا اضافه کن
]
```

### تغییر کوئری‌های جستجو

```python
JSEARCH_QUERIES = {
    1: [
        "WordPress developer remote",
        "WooCommerce developer remote",
        # کوئری‌های خودت رو اضافه کن
    ],
}
```

### تنظیم Cover Letter

فایل `prompt.txt` رو با اطلاعات خودت ویرایش کن.
فقط مطمئن شو `{title}`، `{company}` و `{url}` رو نگه داری.

### Blacklist — فیلتر آگهی‌های ناخواسته

```python
BLACKLIST_KEYWORDS = [
    "us only",
    "senior developer",
    "10+ years",
    # کلماتی که نمیخوای رو اضافه کن
]
```

---

## 📡 منابع شغلی

| منبع | رایگان؟ | نیاز به Key؟ |
|------|--------|-------------|
| [Remotive](https://remotive.com) | ✅ | ❌ |
| [Jobicy](https://jobicy.com) | ✅ | ❌ |
| [Arbeitnow](https://arbeitnow.com) | ✅ | ❌ |
| [FindWork.dev](https://findwork.dev) | ✅ | ❌ |
| [Adzuna](https://developer.adzuna.com) | ✅ محدود | ✅ |
| [JSearch (RapidAPI)](https://rapidapi.com/letscrape-6bRBa3QguO5/api/jsearch) | ✅ ۲۰۰/ماه | ✅ |

---

## 🙏 تقدیر

این پروژه با الهام از [aminsadidi/seo-job-scraper](https://github.com/aminsadidi/seo-job-scraper) ساخته شده و برای WordPress Developer ها بازنویسی و بهینه‌سازی شده.

---

## 📄 License

MIT License — آزادانه استفاده، تغییر و منتشر کن.

</div>

---

<div dir="ltr">

# 🤖 WordPress Job Bot

A Telegram bot that finds the best **remote WordPress & WooCommerce jobs** every morning and sends them directly to you.

**Built for:** WordPress developers looking for remote work worldwide.

---

## ✨ Features

- 🔍 Searches **6+ job sources** simultaneously
- 📊 **Smart scoring** based on your skills
- 🚫 **Auto-filters** irrelevant, expired & duplicate listings
- 📱 Sends directly to **Telegram** with Apply button
- 🤖 **ChatGPT Cover Letter** button for every job
- ⚙️ Fully **customizable** for any developer
- ☁️ Runs **free** on GitHub Actions — no server needed

---

## 🚀 Quick Setup

### Step 1 — Fork this repo

Click the **Fork** button at the top of this page.

### Step 2 — Create a Telegram Bot

1. Go to [@BotFather](https://t.me/BotFather) and send `/newbot`
2. Choose a name and username
3. Copy the **token**
4. Open your bot and send `/start`
5. Get your **Chat ID** from [@userinfobot](https://t.me/userinfobot)

### Step 3 — Add GitHub Secrets

In your forked repo:
**Settings → Secrets and variables → Actions → New repository secret**

| Secret Name | Description | Required? |
|------------|-------------|----------|
| `TELEGRAM_BOT_TOKEN` | BotFather token | ✅ |
| `TELEGRAM_CHAT_ID` | Your Telegram Chat ID | ✅ |
| `RAPIDAPI_KEY` | JSearch API key | ❌ |
| `ADZUNA_APP_ID` | Adzuna App ID | ❌ |
| `ADZUNA_API_KEY` | Adzuna API Key | ❌ |

### Step 4 — Enable & Run

**Actions → WordPress Job Bot → Enable workflow → Run workflow**

Done! Every morning at 7am (Iran time) you'll receive job alerts 🎉

---

## ⚙️ Customization

### Change your skills

Edit `_DEFAULT_SKILLS` in `bot.py`:

```python
_DEFAULT_SKILLS = [
    "wordpress", "woocommerce", "php",
    # add your own skills here
]
```

### Change search queries

```python
JSEARCH_QUERIES = {
    1: [
        "WordPress developer remote",
        # add your own queries
    ],
}
```

### Customize Cover Letter

Edit `prompt.txt` with your own info.
Keep `{title}`, `{company}` and `{url}` placeholders.

### Blacklist unwanted keywords

```python
BLACKLIST_KEYWORDS = [
    "us only",
    "senior developer",
    # add keywords to filter out
]
```

---

## 🙏 Credits

Inspired by [aminsadidi/seo-job-scraper](https://github.com/aminsadidi/seo-job-scraper).
Rebuilt and optimized for WordPress & WooCommerce developers.

---

## 📄 License

MIT — free to use, modify and distribute.

</div>

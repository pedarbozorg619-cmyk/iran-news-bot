import os, json, re, html
import feedparser, requests
import anthropic

TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]
client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

FEEDS = [
    "https://api.axios.com/feed/",
    "https://www.cbsnews.com/latest/rss/world",
    "https://feeds.bbci.co.uk/news/world/rss.xml",
    "https://www.aljazeera.com/xml/rss/all.xml",
    "https://www.theguardian.com/world/rss",
]
KEYWORDS = [
    # ایران و مکان‌ها
    "iran", "iranian", "tehran", "persian gulf", "hormuz",
    "strait of hormuz", "isfahan", "natanz", "fordow", "bushehr",
    # رهبران و نهادها
    "khamenei", "pezeshkian", "araghchi", "irgc", "revolutionary guard",
    # مذاکرات و برنامه هسته‌ای
    "nuclear talks", "nuclear deal", "nuclear program", "enrichment",
    "uranium", "iaea", "jcpoa", "snapback", "sanctions on iran",
    "islamabad", "memorandum of understanding",
    # میانجی‌ها
    "qatar mediat", "pakistan mediat", "egypt mediat", "oman mediat",
    "witkoff", "vance",
    # ترامپ و ایران
    "trump iran", "trump on iran", "trump tehran",
    "trump said iran", "trump warns iran", "trump threatens iran",
    "blockade", "naval blockade",
    # پست و توییت سیاستمداران
    "truth social", "posted on truth social", "said on x",
    "wrote on x", "posted on x", "tweeted", "social media post",
]

# سیاستمدارها و رهبران مهم
LEADERS = [
    "trump", "netanyahu", "macron", "starmer", "merz", "biden",
    "putin", "zelensky", "erdogan", "xi jinping", "modi",
    "rubio", "hegseth", "guterres", "von der leyen",
    "mbs", "bin salman", "sisi", "sharif",
]

IRAN_WORDS = ["iran", "tehran", "nuclear", "enrichment", "hormuz",
              "ayatollah", "irgc", "sanctions"]
SIGNATURE = "\n\n🤖 من ربات خبریاب ایران کهنم و این خبر مستقیم از سایت مربوطه براتون آوردم"
SEEN_FILE = "seen.json"
MODEL = "claude-haiku-4-5-20251001"

def load_seen():
    if os.path.exists(SEEN_FILE):
        return set(json.load(open(SEEN_FILE)))
    return set()

def save_seen(seen):
    json.dump(list(seen)[-2000:], open(SEEN_FILE, "w"))

def is_iran_related(title, summary):
    text = (title + " " + summary).lower()
    if any(k in text for k in KEYWORDS):
        return True
    # هر سیاستمدار مهم + کلمات مرتبط با ایران
    if any(l in text for l in LEADERS) and any(w in text for w in IRAN_WORDS):
        return True
    return False

def translate(title, summary):
    prompt = (
        "این خبر را به فارسی روان و خبری ترجمه کن. "
        "فقط یک JSON با کلیدهای title و summary برگردان "
        "(summary حداکثر ۳ جمله). هیچ متن اضافه‌ای ننویس.\n\n"
        f"Title: {title}\nSummary: {summary}"
    )
    r = client.messages.create(
        model=MODEL, max_tokens=600,
        messages=[{"role": "user", "content": prompt}],
    )
    text = r.content[0].text
    m = re.search(r"\{.*\}", text, re.S)
    return json.loads(m.group(0))

def send(text):
    requests.post(
        f"https://api.telegram.org/bot{TOKEN}/sendMessage",
        data={"chat_id": CHAT_ID, "text": text,
              "parse_mode": "HTML",
              "disable_web_page_preview": "false"},
        timeout=30,
    )

def main():
    seen = load_seen()
    for url in FEEDS:
        feed = feedparser.parse(url)
        for e in feed.entries[:5]:
            link = e.get("link", "")
            if not link or link in seen:
                continue
            title = e.get("title", "")
            summary = re.sub("<[^<]+?>", "", e.get("summary", ""))
            if not is_iran_related(title, summary):
                continue
            try:
                t = translate(title, summary)
            except Exception as ex:
                print("translate error:", ex)
                continue
            msg = (f"<b>{html.escape(t['title'])}</b>\n\n"
                   f"{html.escape(t['summary'])}\n\n"
                   f"🔗 <a href=\"{html.escape(link)}\">منبع خبر</a>"
                   f"{SIGNATURE}")
            send(msg)
            seen.add(link)
    save_seen(seen)

if __name__ == "__main__":
    main()

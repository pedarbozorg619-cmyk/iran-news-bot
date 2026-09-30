import os, json, re, html
import feedparser, requests
from deep_translator import GoogleTranslator

TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

FEEDS = [
    "https://api.axios.com/feed/",
    "https://www.cbsnews.com/latest/rss/world",
    "https://feeds.bbci.co.uk/news/world/rss.xml",
    "https://www.aljazeera.com/xml/rss/all.xml",
    "https://www.theguardian.com/world/rss",
]

KEYWORDS = [
    "iran", "iranian", "tehran", "persian gulf", "hormuz",
    "strait of hormuz", "isfahan", "natanz", "fordow", "bushehr",
    "khamenei", "pezeshkian", "araghchi", "irgc", "revolutionary guard",
    "nuclear talks", "nuclear deal", "nuclear program", "enrichment",
    "uranium", "iaea", "jcpoa", "snapback", "sanctions on iran",
    "islamabad", "memorandum of understanding",
    "qatar mediat", "pakistan mediat", "egypt mediat", "oman mediat",
    "witkoff", "vance",
    "trump iran", "trump on iran", "trump tehran",
    "trump said iran", "trump warns iran", "trump threatens iran",
    "blockade", "naval blockade",
    "truth social", "posted on truth social", "said on x",
    "wrote on x", "posted on x", "tweeted", "social media post",
]

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
    if any(l in text for l in LEADERS) and any(w in text for w in IRAN_WORDS):
        return True
    return False

def translate(title, summary):
    tr = GoogleTranslator(source="auto", target="fa")
    t = tr.translate(title[:400])
    s = tr.translate(summary[:900]) if summary.strip() else ""
    return {"title": t, "summary": s}

def send(text):
    r = requests.post(
        f"https://api.telegram.org/bot{TOKEN}/sendMessage",
        data={"chat_id": CHAT_ID, "text": text,
              "parse_mode": "HTML",
              "disable_web_page_preview": "false"},
        timeout=30,
    )
    print("telegram:", r.status_code)
    return r.ok

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
            if send(msg):
                seen.add(link)
    save_seen(seen)

if __name__ == "__main__":
    main()

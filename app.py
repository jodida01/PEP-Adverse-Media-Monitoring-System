import os
import re
import requests
import feedparser
from bs4 import BeautifulSoup
from email.message import EmailMessage
from urllib.parse import quote

from database import init_db, save_alert
from sources import SOURCES

# Initialize DB
init_db()

# -------------------------
# RISK SCORING MODEL
# -------------------------
SCORES = {
    "fraud": 70,
    "money laundering": 90,
    "corruption": 80,
    "terrorism": 100,
    "bribery": 60,
    "scandal": 30,
    "crime": 40,
    "investigation": 40,
    "tax evasion": 75,
    "arrested": 50,
    "charged": 50,
    "illegal": 60,
    "sanctions": 85,
}

STOPWORDS = {
    "the",
    "and",
    "of",
    "in",
    "for",
    "with",
    "by",
    "on",
    "from",
    "to",
    "at",
    "as",
    "a",
    "an",
    "court",
    "press",
    "release",
    "agency",
    "commission",
}


def get_score(keyword):
    return SCORES.get(keyword.lower(), 10)


def load_lines(path):
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]


NAMES = load_lines("names.txt")
PEP_LIST = [x.lower() for x in load_lines("pep_watchlist.txt")]


def send_email(name, headline, keyword, risk_level, score):
    smtp_host = os.environ.get("SMTP_HOST", "smtp.gmail.com")
    smtp_port = int(os.environ.get("SMTP_PORT", "465"))
    smtp_user = os.environ.get("SMTP_USER", "your_email@gmail.com")
    smtp_password = os.environ.get("SMTP_PASSWORD", "APP_PASSWORD")
    recipient = os.environ.get("ALERT_RECIPIENT", smtp_user)

    msg = EmailMessage()
    msg["Subject"] = f"AML ALERT: {name} ({risk_level})"
    msg["From"] = smtp_user
    msg["To"] = recipient

    msg.set_content(f"""
AML ALERT DETECTED

Name: {name}
Headline: {headline}
Keyword: {keyword}
Risk Level: {risk_level}
Score: {score}
""")

    try:
        import smtplib

        if smtp_port == 465:
            with smtplib.SMTP_SSL(smtp_host, smtp_port) as smtp:
                smtp.login(smtp_user, smtp_password)
                smtp.send_message(msg)
        else:
            with smtplib.SMTP(smtp_host, smtp_port) as smtp:
                smtp.starttls()
                smtp.login(smtp_user, smtp_password)
                smtp.send_message(msg)

        print("Email sent ✔")
    except Exception as e:
        print("Email error:", e)


def fetch_rss(url):
    return feedparser.parse(url)


def fetch_html_text(url):
    try:
        response = requests.get(url, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        parts = []
        for node in soup.find_all(["h1", "h2", "h3", "p"]):
            text = node.get_text(separator=" ", strip=True)
            if text:
                parts.append(text)
        return " ".join(parts)
    except Exception as e:
        print(f"Failed to fetch HTML source {url}: {e}")
        return ""


def extract_names(text):
    matches = re.findall(r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,4})\b", text)
    cleaned = []
    for match in matches:
        normalized = " ".join(match.split())
        lower = normalized.lower()
        if lower in STOPWORDS:
            continue
        if any(word.lower() in STOPWORDS for word in normalized.split()):
            continue
        cleaned.append(normalized)
    return list(dict.fromkeys(cleaned))


def classify_risk(keyword, name):
    score = get_score(keyword)
    if name.lower() in PEP_LIST:
        return "PEP HIGH", score
    if score >= 80:
        return "HIGH", score
    if score >= 50:
        return "MEDIUM", score
    return "LOW", score


def scan_entry(source_name, title, summary, search_name=None):
    text = f"{title} {summary}".strip()
    lower_text = text.lower()
    found_keyword = None

    for keyword in SCORES:
        if keyword in lower_text:
            found_keyword = keyword
            break

    if not found_keyword:
        return

    if search_name:
        name = search_name
    else:
        names = extract_names(f"{title} {summary}")
        name = names[0] if names else "Unlisted individual"

    risk_level, score = classify_risk(found_keyword, name)
    headline = f"[{source_name}] {title}" if source_name else title

    save_alert(name, headline, found_keyword, risk_level, score)
    send_email(name, headline, found_keyword, risk_level, score)
    print(f"RISK DETECTED: {name} | {found_keyword} | {risk_level} | {source_name}")


def scan_source(source):
    if source.get("type") == "rss":
        print(f"\nScanning RSS source: {source['name']}")
        feed = fetch_rss(source["url"])
        for entry in feed.entries[:20]:
            scan_entry(source["name"], getattr(entry, "title", ""), getattr(entry, "summary", ""))
    elif source.get("type") == "html":
        print(f"\nScanning HTML source: {source['name']}")
        text = fetch_html_text(source["url"])
        scan_entry(source["name"], source["url"], text)
    else:
        print(f"Unknown source type for {source['name']}")


def run_scan():
    if not SOURCES:
        print("No sources defined. Add sources in sources.py.")
        return

    for source in SOURCES:
        if source.get("query"):
            for name in NAMES:
                query = quote(name)
                url = source["url"].replace("{query}", query)
                print(f"\nScanning search source: {source['name']} for {name}")
                feed = fetch_rss(url)
                for entry in feed.entries[:10]:
                    scan_entry(source["name"], getattr(entry, "title", ""), getattr(entry, "summary", ""), search_name=name)
        else:
            scan_source(source)


if __name__ == "__main__":
    run_scan()

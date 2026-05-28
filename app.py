import os
import re
import requests
import feedparser
from bs4 import BeautifulSoup
from email.message import EmailMessage
from urllib.parse import quote
from datetime import datetime, timedelta
from threading import Thread
import signal

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
    """Fetch RSS with timeout handling"""
    try:
        # feedparser doesn't support timeout, so we use requests
        response = requests.get(url, timeout=8, headers={"User-Agent": "Mozilla/5.0"})
        response.raise_for_status()
        return feedparser.parse(response.content)
    except requests.Timeout:
        print(f"RSS fetch timeout: {url}")
        return {"entries": []}
    except Exception as e:
        print(f"RSS fetch error {url}: {e}")
        return {"entries": []}


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


def scan_entry(source_name, title, summary, source_url=None, search_name=None):
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

    saved = save_alert(name, headline, found_keyword, risk_level, score, source=source_name, source_url=source_url)
    if saved:
        send_email(name, headline, found_keyword, risk_level, score)
        print(f"RISK DETECTED: {name} | {found_keyword} | {risk_level} | {source_name} | {source_url}")
    else:
        print(f"Skipped duplicate alert: {name} | {found_keyword} | {source_name}")


def scan_source(source):
    """Scan a single source with error handling"""
    try:
        if source.get("type") == "rss":
            print(f"\nScanning RSS source: {source['name']}")
            feed = fetch_rss(source["url"])
            if not feed.get("entries"):
                print(f"No entries found in {source['name']}")
                return
            
            for entry in feed.entries[:20]:
                try:
                    source_url = getattr(entry, "link", source["url"])
                    title = getattr(entry, "title", "")
                    summary = getattr(entry, "summary", "")
                    scan_entry(source["name"], title, summary, source_url=source_url)
                except Exception as e:
                    print(f"Error scanning entry from {source['name']}: {e}")
                    continue
                    
        elif source.get("type") == "html":
            print(f"\nScanning HTML source: {source['name']}")
            text = fetch_html_text(source["url"])
            if text:
                scan_entry(source["name"], source["url"], text, source_url=source["url"])
        else:
            print(f"Unknown source type for {source['name']}")
    except Exception as e:
        print(f"Error scanning source {source.get('name')}: {e}")


def run_scan():
    """Run the AML scan across all sources"""
    if not SOURCES:
        print("No sources defined. Add sources in sources.py.")
        # Generate test data for development
        generate_test_alerts()
        return

    print(f"\n{'='*60}")
    print(f"Starting AML Scan at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}")
    
    sources_scanned = 0
    for source in SOURCES:
        try:
            if source.get("query"):
                for name in NAMES:
                    if not name:
                        continue
                    query = quote(name)
                    url = source["url"].replace("{query}", query)
                    print(f"\nScanning search source: {source['name']} for {name}")
                    try:
                        feed = fetch_rss(url)
                        if feed.get("entries"):
                            for entry in feed.entries[:10]:
                                scan_entry(source["name"], getattr(entry, "title", ""), getattr(entry, "summary", ""), search_name=name)
                    except Exception as e:
                        print(f"Error scanning {source['name']} for {name}: {e}")
                        continue
            else:
                scan_source(source)
                sources_scanned += 1
        except Exception as e:
            print(f"Error processing source {source.get('name')}: {e}")
            continue
    
    print(f"\n{'='*60}")
    print(f"Scan completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}\n")


def generate_test_alerts():
    """Generate test alerts for development/demo purposes with today's date"""
    from datetime import datetime, timedelta
    import random
    
    print("Generating demo alerts with today's timestamp...")
    
    # Delete old alerts to refresh the data
    conn = __import__('sqlite3').connect('alerts.db')
    c = conn.cursor()
    c.execute("DELETE FROM alerts WHERE timestamp < datetime('now', '-2 days')")
    conn.commit()
    conn.close()
    
    today = datetime.now()
    
    test_data = [
        {
            "name": "James Kariuki Mwangi",
            "keyword": "money laundering",
            "headline": "Former Treasury PS named in Sh4.2bn procurement scandal linked to SGR project",
            "source": "Daily Nation",
            "risk": "HIGH",
            "score": 92,
            "minutes_ago": 1740  # 29 hours ago
        },
        {
            "name": "Amina Hassan Oduya",
            "keyword": "fraud",
            "headline": "Mombasa businesswoman flagged in FATF watchlist over shell company network",
            "source": "Business Daily",
            "risk": "HIGH",
            "score": 88,
            "minutes_ago": 1080  # 18 hours ago  
        },
        {
            "name": "Patrick Njoroge Waweru",
            "keyword": "corruption",
            "headline": "Cabinet Secretary nominee under scrutiny for undisclosed offshore accounts",
            "source": "The Star",
            "risk": "PEP",
            "score": 76,
            "minutes_ago": 420  # 7 hours ago
        },
        {
            "name": "Mercy Akinyi Otieno",
            "keyword": "investigation",
            "headline": "MP flagged in Kenya Gazette notice as respondent in unexplained wealth order",
            "source": "Kenya Gazette",
            "risk": "PEP",
            "score": 71,
            "minutes_ago": 240  # 4 hours ago
        },
        {
            "name": "Dominic Omondi Ochola",
            "keyword": "corruption",
            "headline": "County Governor implicated in KES 800M county funds diversion",
            "source": "KBC News",
            "risk": "HIGH",
            "score": 85,
            "minutes_ago": 120  # 2 hours ago
        },
    ]
    
    added = 0
    for alert in test_data:
        try:
            # Create timestamp from minutes ago
            timestamp = (today - timedelta(minutes=alert["minutes_ago"])).isoformat()
            
            # Only save if not already in database (checks by name, keyword, source)
            if save_alert(
                alert["name"],
                alert["headline"],
                alert["keyword"],
                alert["risk"],
                alert["score"],
                source=alert["source"],
                timestamp=timestamp
            ):
                print(f"✓ Generated: {alert['name']}")
                added += 1
            else:
                print(f"  {alert['name']} (already exists)")
        except Exception as e:
            print(f"Error adding alert: {e}")
    
    if added > 0:
        print(f"\nAdded {added} demo alerts")
    else:
        print("Demo data already loaded")


if __name__ == "__main__":
    run_scan()

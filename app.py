import feedparser
import smtplib
from email.message import EmailMessage
from urllib.parse import quote

from database import init_db, save_alert

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
    "sanctions": 85
}

def get_score(keyword):
    return SCORES.get(keyword.lower(), 10)

# -------------------------
# LOAD PEP WATCHLIST
# -------------------------
with open("pep_watchlist.txt", "r", encoding="utf-8") as f:
    PEP_LIST = [x.strip().lower() for x in f.readlines()]

# -------------------------
# EMAIL FUNCTION
# -------------------------
def send_email(name, headline, keyword, risk_level, score):

    msg = EmailMessage()
    msg["Subject"] = f"AML ALERT: {name} ({risk_level})"
    msg["From"] = "your_email@gmail.com"
    msg["To"] = "your_email@gmail.com"

    msg.set_content(f"""
AML ALERT DETECTED

Name: {name}
Headline: {headline}
Keyword: {keyword}
Risk Level: {risk_level}
Score: {score}
""")

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login("your_email@gmail.com", "APP_PASSWORD")
            smtp.send_message(msg)
            print("Email sent ✔")

    except Exception as e:
        print("Email error:", e)

# -------------------------
# MAIN SCANNER
# -------------------------
def run_scan():

    names = open("names.txt", encoding="utf-8").read().splitlines()

    for name in names:

        search_name = quote(name)
        url = f"https://news.google.com/rss/search?q={search_name}"

        feed = feedparser.parse(url)

        print(f"\nScanning: {name}")

        for entry in feed.entries[:5]:

            title = entry.title.lower()

            for keyword, base_score in SCORES.items():

                if keyword in title:

                    # Risk classification
                    if base_score >= 80:
                        level = "HIGH"
                    elif base_score >= 50:
                        level = "MEDIUM"
                    else:
                        level = "LOW"

                    # PEP override
                    if name.lower() in PEP_LIST:
                        level = "PEP HIGH"

                    # Save to DB
                    save_alert(name, entry.title, keyword, level, base_score)

                    # Send email alert
                    send_email(name, entry.title, keyword, level, base_score)

                    print(f"RISK DETECTED: {name} | {keyword} | {level}")

# -------------------------
# RUN
# -------------------------
if __name__ == "__main__":
    run_scan()
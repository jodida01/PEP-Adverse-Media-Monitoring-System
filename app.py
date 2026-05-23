import feedparser
import csv
import smtplib
from email.message import EmailMessage

# =========================
# RISK KEYWORDS
# =========================
risk_keywords = [
    "fraud", "money laundering", "corruption", "terrorism",
    "bribery", "scandal", "crime", "investigation",
    "tax evasion", "arrested", "charged", "illegal", "sanctions"
]

# =========================
# EMAIL CONFIG
# =========================
EMAIL_ADDRESS = "odidajudah01@gmail.com"
EMAIL_PASSWORD = "YOUR_APP_PASSWORD"
RECEIVER_EMAIL = "odidajudah01@gmail.com"

# Prevent duplicate emails (VERY IMPORTANT)
sent_alerts = set()

def send_email_alert(name, headline, keyword):

    # prevent duplicates
    alert_key = f"{name}-{headline}-{keyword}"
    if alert_key in sent_alerts:
        return
    sent_alerts.add(alert_key)

    subject = f"PEP/Adverse Media Alert: {name}"

    body = f"""
Risk Alert Detected

Name: {name}
Headline: {headline}
Keyword: {keyword}
"""

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = RECEIVER_EMAIL
    msg.set_content(body)

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            smtp.send_message(msg)

        print("📧 Email sent:", name)

    except Exception as e:
        print("Email failed:", e)


def run_scan():

    with open("names.txt", "r", encoding="utf-8") as file:
        names = [n.strip() for n in file.readlines() if n.strip()]

    with open("alerts.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Name", "Headline", "Keyword"])

    with open("alerts.csv", "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)

        for name in names:

            print("\nScanning:", name)

            url = f"https://news.google.com/rss/search?q={name.replace(' ', '+')}"
            feed = feedparser.parse(url)

            for entry in feed.entries[:5]:

                title = entry.title

                for keyword in risk_keywords:

                    if keyword.lower() in title.lower():

                        print("RISK:", name, keyword)

                        writer.writerow([name, title, keyword])

                        send_email_alert(name, title, keyword)


if __name__ == "__main__":
    run_scan()
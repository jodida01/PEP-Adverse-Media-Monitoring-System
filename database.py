import sqlite3

DB = "alerts.db"

def init_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS alerts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        headline TEXT,
        keyword TEXT,
        risk_level TEXT,
        score INTEGER,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()
    conn.close()


def save_alert(name, headline, keyword, risk_level, score):
    conn = sqlite3.connect(DB)
    c = conn.cursor()

    c.execute("""
        INSERT INTO alerts (name, headline, keyword, risk_level, score)
        VALUES (?, ?, ?, ?, ?)
    """, (name, headline, keyword, risk_level, score))

    conn.commit()
    conn.close()


def get_alerts():
    conn = sqlite3.connect(DB)
    c = conn.cursor()

    c.execute("SELECT name, headline, keyword, risk_level, score, timestamp FROM alerts ORDER BY id DESC")
    data = c.fetchall()

    conn.close()
    return data
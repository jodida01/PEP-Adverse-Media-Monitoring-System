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
        source TEXT,
        source_url TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()

    c.execute("PRAGMA table_info(alerts)")
    existing_columns = [row[1] for row in c.fetchall()]
    if "source" not in existing_columns:
        c.execute("ALTER TABLE alerts ADD COLUMN source TEXT")
        conn.commit()
    if "source_url" not in existing_columns:
        c.execute("ALTER TABLE alerts ADD COLUMN source_url TEXT")
        conn.commit()

    conn.close()


def alert_exists(name, keyword, source):
    conn = sqlite3.connect(DB)
    c = conn.cursor()

    c.execute(
        "SELECT 1 FROM alerts WHERE name = ? AND keyword = ? AND source = ? LIMIT 1",
        (name, keyword, source)
    )
    exists = c.fetchone() is not None

    conn.close()
    return exists


def save_alert(name, headline, keyword, risk_level, score, source=None, source_url=None, timestamp=None):
    if alert_exists(name, keyword, source):
        return False

    conn = sqlite3.connect(DB)
    c = conn.cursor()

    if timestamp:
        c.execute("""
            INSERT INTO alerts (name, headline, keyword, risk_level, score, source, source_url, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (name, headline, keyword, risk_level, score, source, source_url, timestamp))
    else:
        c.execute("""
            INSERT INTO alerts (name, headline, keyword, risk_level, score, source, source_url)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (name, headline, keyword, risk_level, score, source, source_url))

    conn.commit()
    conn.close()
    return True


def get_alerts():
    conn = sqlite3.connect(DB)
    c = conn.cursor()

    c.execute("SELECT name, headline, keyword, risk_level, score, source, source_url, timestamp FROM alerts ORDER BY timestamp DESC")
    data = c.fetchall()

    conn.close()
    return data


def get_last_scan_time():
    conn = sqlite3.connect(DB)
    c = conn.cursor()

    c.execute("SELECT MAX(timestamp) FROM alerts")
    result = c.fetchone()
    conn.close()
    
    return result[0] if result and result[0] else None
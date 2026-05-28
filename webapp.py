from flask import Flask, render_template_string, jsonify, request, send_file
from database import get_alerts, get_last_scan_time, init_db
from datetime import datetime
import io
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import csv
import threading
import time
import schedule
from app import run_scan, generate_test_alerts

app = Flask(__name__)
init_db()

# Background scheduler flag
scheduler_running = False

def start_background_scheduler():
    """Start the background scheduler in a daemon thread"""
    global scheduler_running
    if scheduler_running:
        return
    
    scheduler_running = True
    
    def scheduler_worker():
        # Generate demo data immediately on startup
        print("[Startup] Generating demo alerts...")
        try:
            generate_test_alerts()
        except Exception as e:
            print(f"Demo data generation error: {e}")
        
        # Try to fetch real data from sources (non-blocking)
        print("[Startup] Starting background scan (may timeout, that's OK)...")
        def async_scan():
            try:
                run_scan()
            except Exception as e:
                print(f"Background scan error: {e}")
        
        Thread(target=async_scan, daemon=True).start()
        
        # Schedule scans every 6 hours
        schedule.every(6).hours.do(lambda: run_scan_with_logging())
        
        while True:
            try:
                schedule.run_pending()
                time.sleep(60)
            except Exception as e:
                print(f"Scheduler error: {e}")
                time.sleep(60)
    
    def run_scan_with_logging():
        """Wrapper to log when scan runs"""
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{now}] Running scheduled AML scan...")
        try:
            run_scan()
            print(f"[{now}] Scan completed")
        except Exception as e:
            print(f"[{now}] Scan error: {e}")
    
    thread = threading.Thread(target=scheduler_worker, daemon=True)
    thread.start()
    print("✓ Background scheduler started")

# Start scheduler when app starts
start_background_scheduler()

# -------------------------
# DASHBOARD UI (PROFESSIONAL COMPLIANCE SUITE)
# -------------------------
HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>AML Monitor - Compliance Suite</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen', 'Ubuntu', 'Cantarell', sans-serif;
            background: #0f172a;
            color: #e2e8f0;
            line-height: 1.6;
        }

        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 0;
        }

        /* Header */
        .header {
            background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
            padding: 24px 32px;
            border-bottom: 1px solid #334155;
        }

        .header-top {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
        }

        .header-title {
            display: flex;
            gap: 8px;
            align-items: center;
        }

        .header-title h1 {
            font-size: 28px;
            font-weight: 700;
            color: #f1f5f9;
        }

        .header-title .subtitle {
            font-size: 13px;
            color: #94a3b8;
            font-weight: 500;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        .header-status {
            display: flex;
            gap: 16px;
            align-items: center;
            font-size: 12px;
        }

        .status-item {
            display: flex;
            gap: 6px;
            align-items: center;
            color: #cbd5e1;
        }

        .status-indicator {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: #10b981;
            animation: pulse 2s infinite;
        }

        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }

        .secure-badge {
            background: rgba(16, 185, 129, 0.1);
            border: 1px solid #10b981;
            color: #10b981;
            padding: 4px 12px;
            border-radius: 4px;
            font-size: 11px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        .feeds-info {
            display: flex;
            gap: 24px;
            color: #94a3b8;
            font-size: 12px;
        }

        .feed-item {
            display: flex;
            gap: 6px;
            align-items: center;
        }

        .feed-dot {
            width: 6px;
            height: 6px;
            border-radius: 50%;
            background: #3b82f6;
        }

        .last-scan {
            color: #64748b;
            font-size: 12px;
            margin-top: 8px;
        }

        /* Controls */
        .controls {
            background: #1e293b;
            padding: 16px 32px;
            display: flex;
            gap: 12px;
            border-bottom: 1px solid #334155;
        }

        .btn {
            padding: 10px 20px;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            font-size: 13px;
            font-weight: 600;
            transition: all 0.2s ease;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        .btn-primary {
            background: #3b82f6;
            color: white;
        }

        .btn-primary:hover {
            background: #2563eb;
            transform: translateY(-1px);
        }

        .btn-secondary {
            background: #475569;
            color: white;
        }

        .btn-secondary:hover {
            background: #64748b;
        }

        /* Main Content */
        .main {
            padding: 32px;
        }

        /* Stats Grid */
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }

        .stat-card {
            background: #1e293b;
            border: 1px solid #334155;
            border-radius: 8px;
            padding: 24px;
            transition: all 0.3s ease;
        }

        .stat-card:hover {
            border-color: #475569;
            box-shadow: 0 8px 24px rgba(3, 102, 214, 0.1);
        }

        .stat-number {
            font-size: 32px;
            font-weight: 700;
            margin-bottom: 8px;
        }

        .stat-label {
            font-size: 12px;
            color: #94a3b8;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 4px;
        }

        .stat-desc {
            font-size: 11px;
            color: #64748b;
        }

        .stat-card.high .stat-number { color: #ef4444; }
        .stat-card.pep .stat-number { color: #3b82f6; }
        .stat-card.medium .stat-number { color: #f59e0b; }
        .stat-card.low .stat-number { color: #10b981; }
        .stat-card.total .stat-number { color: #8b5cf6; }

        /* Filter Buttons */
        .filter-buttons {
            display: flex;
            gap: 8px;
            margin-bottom: 24px;
            flex-wrap: wrap;
        }

        .filter-btn {
            padding: 8px 16px;
            border: 1px solid #475569;
            background: transparent;
            color: #cbd5e1;
            border-radius: 6px;
            cursor: pointer;
            font-size: 12px;
            font-weight: 600;
            transition: all 0.2s ease;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        .filter-btn.active {
            background: #3b82f6;
            color: white;
            border-color: #3b82f6;
        }

        .filter-btn:hover {
            border-color: #64748b;
        }

        /* Search Bar */
        .search-bar {
            margin-bottom: 24px;
        }

        .search-input {
            width: 100%;
            padding: 12px 16px;
            background: #1e293b;
            border: 1px solid #334155;
            border-radius: 6px;
            color: #e2e8f0;
            font-size: 13px;
        }

        .search-input::placeholder {
            color: #64748b;
        }

        .search-input:focus {
            outline: none;
            border-color: #3b82f6;
            box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
        }

        /* Table */
        .table-wrapper {
            background: #1e293b;
            border: 1px solid #334155;
            border-radius: 8px;
            overflow: hidden;
        }

        table {
            width: 100%;
            border-collapse: collapse;
        }

        thead {
            background: #0f172a;
            border-bottom: 2px solid #334155;
        }

        th {
            padding: 16px;
            text-align: left;
            font-size: 12px;
            font-weight: 700;
            color: #94a3b8;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        td {
            padding: 14px 16px;
            border-bottom: 1px solid #334155;
            font-size: 13px;
        }

        tr:hover td {
            background: rgba(59, 130, 246, 0.05);
        }

        .entity-name {
            font-weight: 600;
            color: #f1f5f9;
        }

        .headline-source {
            color: #cbd5e1;
        }

        .source-badge {
            display: inline-block;
            font-size: 10px;
            padding: 4px 8px;
            background: #334155;
            border-radius: 4px;
            color: #94a3b8;
            margin-top: 4px;
        }

        .risk-high {
            color: #ef4444;
            font-weight: 700;
        }

        .risk-pep {
            color: #3b82f6;
            font-weight: 700;
        }

        .risk-medium {
            color: #f59e0b;
            font-weight: 700;
        }

        .risk-low {
            color: #10b981;
            font-weight: 700;
        }

        .score {
            font-weight: 600;
            color: #f1f5f9;
        }

        .timestamp {
            color: #64748b;
            font-size: 12px;
        }

        /* Footer */
        .footer {
            padding: 24px 32px;
            border-top: 1px solid #334155;
            color: #64748b;
            font-size: 12px;
            text-align: center;
        }

        .footer-item {
            display: inline-block;
            margin: 0 16px;
        }

        @media (max-width: 768px) {
            .header-top {
                flex-direction: column;
                align-items: flex-start;
                gap: 12px;
            }

            .controls {
                flex-direction: column;
            }

            th, td {
                padding: 12px 8px;
                font-size: 12px;
            }

            .stat-card {
                padding: 16px;
            }
        }
    </style>
</head>

<body>
<div class="container">
    <div class="header">
        <div class="header-top">
            <div class="header-title">
                <h1>AML Monitor</h1>
                <div style="display: flex; flex-direction: column; gap: 2px;">
                    <div class="subtitle">Compliance Suite</div>
                    <div style="display: flex; gap: 8px; align-items: center;">
                        <span class="status-indicator"></span>
                        <span style="font-size: 11px; color: #10b981;">System Online</span>
                    </div>
                </div>
            </div>
            <div class="secure-badge">🔒 SECURE</div>
        </div>

        <div class="feeds-info">
            <div class="feed-item">
                <span class="feed-dot"></span>
                KE Regulatory Feed
            </div>
            <div class="feed-item">
                <span class="feed-dot"></span>
                Threat Intelligence Feed
            </div>
            <div class="feed-item">
                <span class="feed-dot"></span>
                <span style="color: #10b981;">Live</span>
            </div>
        </div>

        <div class="last-scan">
            Last scan: <span id="lastScanTime">No scan recorded</span>
        </div>
    </div>

    <div class="controls">
        <button class="btn btn-primary" onclick="triggerScan()">📡 Scan Now</button>
        <button class="btn btn-secondary" onclick="window.location='/export-csv'">📥 Export CSV</button>
    </div>

    <div class="main">
        <div class="stats-grid" id="statsGrid">
            <div class="stat-card total">
                <div class="stat-label">Total Flags</div>
                <div class="stat-number" id="totalCount">0</div>
                <div class="stat-desc">All risk levels</div>
            </div>
            <div class="stat-card high">
                <div class="stat-label">High Risk</div>
                <div class="stat-number" id="highCount">0</div>
                <div class="stat-desc">Critical threats</div>
            </div>
            <div class="stat-card pep">
                <div class="stat-label">PEP Alerts</div>
                <div class="stat-number" id="pepCount">0</div>
                <div class="stat-desc">Political exposure</div>
            </div>
            <div class="stat-card medium">
                <div class="stat-label">Medium Risk</div>
                <div class="stat-number" id="mediumCount">0</div>
                <div class="stat-desc">Elevated concern</div>
            </div>
            <div class="stat-card low">
                <div class="stat-label">Low Risk</div>
                <div class="stat-number" id="lowCount">0</div>
                <div class="stat-desc">Routine monitoring</div>
            </div>
        </div>

        <div class="filter-buttons">
            <button class="filter-btn active" onclick="filterAlerts('ALL')">All Alerts</button>
            <button class="filter-btn" onclick="filterAlerts('HIGH')">High Risk</button>
            <button class="filter-btn" onclick="filterAlerts('PEP')">PEP</button>
            <button class="filter-btn" onclick="filterAlerts('MEDIUM')">Medium</button>
            <button class="filter-btn" onclick="filterAlerts('LOW')">Low</button>
        </div>

        <div class="search-bar">
            <input type="text" class="search-input" id="searchInput" placeholder="Search entity or headline…" onkeyup="applySearch()">
        </div>

        <div class="table-wrapper">
            <table>
                <thead>
                    <tr>
                        <th>Entity</th>
                        <th>Headline & Source</th>
                        <th>Risk</th>
                        <th style="width: 80px;">Score</th>
                        <th style="width: 140px;">Date</th>
                    </tr>
                </thead>
                <tbody id="tableBody">
                    <tr>
                        <td colspan="5" style="text-align: center; color: #64748b; padding: 40px;">Loading alerts...</td>
                    </tr>
                </tbody>
            </table>
        </div>

        <div class="footer">
            <div class="footer-item"><span id="recordCount">0</span> records displayed</div>
            <div class="footer-item">Auto-refresh every 10s</div>
            <div class="footer-item" style="color: #475569;">Development preview</div>
        </div>
    </div>
</div>

<script>
    let allData = [];
    let currentFilter = 'ALL';
    let searchQuery = '';

    async function loadAlerts() {
        try {
            const res = await fetch('/data?filter=ALL');
            allData = await res.json();
            updateStats();
            updateLastScanTime();
            applyFiltersAndSearch();
        } catch (e) {
            console.error('Error loading alerts:', e);
        }
    }

    async function updateLastScanTime() {
        try {
            const res = await fetch('/last-scan');
            const data = await res.json();
            document.getElementById('lastScanTime').textContent = data.formatted;
        } catch (e) {
            console.error('Error fetching last scan time:', e);
        }
    }

    function updateStats() {
        const stats = {
            total: allData.length,
            high: 0,
            pep: 0,
            medium: 0,
            low: 0
        };

        allData.forEach(row => {
            const risk = (row.risk_level || '').toUpperCase();
            if (risk.includes('HIGH')) stats.high++;
            else if (risk.includes('PEP')) stats.pep++;
            else if (risk.includes('MEDIUM')) stats.medium++;
            else if (risk.includes('LOW')) stats.low++;
        });

        document.getElementById('totalCount').textContent = stats.total;
        document.getElementById('highCount').textContent = stats.high;
        document.getElementById('pepCount').textContent = stats.pep;
        document.getElementById('mediumCount').textContent = stats.medium;
        document.getElementById('lowCount').textContent = stats.low;
    }

    function filterAlerts(filter) {
        currentFilter = filter;
        document.querySelectorAll('.filter-btn').forEach(btn => btn.classList.remove('active'));
        event.target.classList.add('active');
        applyFiltersAndSearch();
    }

    function applySearch() {
        searchQuery = document.getElementById('searchInput').value.toLowerCase();
        applyFiltersAndSearch();
    }

    function applyFiltersAndSearch() {
        let filtered = allData.filter(row => {
            const risk = (row.risk_level || '').toUpperCase();
            
            // Filter by risk level
            if (currentFilter === 'HIGH' && !risk.includes('HIGH')) return false;
            if (currentFilter === 'PEP' && !risk.includes('PEP')) return false;
            if (currentFilter === 'MEDIUM' && !risk.includes('MEDIUM')) return false;
            if (currentFilter === 'LOW' && !risk.includes('LOW')) return false;

            // Filter by search
            if (searchQuery) {
                const searchFields = [
                    row.name,
                    row.headline,
                    row.source
                ].join(' ').toLowerCase();
                
                if (!searchFields.includes(searchQuery)) return false;
            }

            return true;
        });

        renderTable(filtered);
    }

    function renderTable(data) {
        const tbody = document.getElementById('tableBody');
        const recordCount = document.getElementById('recordCount');

        if (data.length === 0) {
            tbody.innerHTML = '<tr><td colspan="5" style="text-align: center; color: #64748b; padding: 40px;">No alerts match your criteria</td></tr>';
            recordCount.textContent = '0';
            return;
        }

        let html = '';
        data.forEach(row => {
            const risk = (row.risk_level || '').toUpperCase();
            let riskClass = '';
            let riskLabel = '';

            if (risk.includes('HIGH')) {
                riskClass = 'risk-high';
                riskLabel = 'HIGH';
            } else if (risk.includes('PEP')) {
                riskClass = 'risk-pep';
                riskLabel = 'PEP';
            } else if (risk.includes('MEDIUM')) {
                riskClass = 'risk-medium';
                riskLabel = 'MEDIUM';
            } else {
                riskClass = 'risk-low';
                riskLabel = 'LOW';
            }

            const date = new Date(row.timestamp);
            const dateStr = date.toLocaleDateString('en-KE', { year: 'numeric', month: 'short', day: 'numeric' });
            const timeStr = date.toLocaleTimeString('en-KE', { hour: '2-digit', minute: '2-digit' });

            html += `
            <tr>
                <td class="entity-name">${row.name}</td>
                <td>
                    <div class="headline-source">${row.headline}</div>
                    <div class="source-badge">${row.source || 'Unknown'}</div>
                </td>
                <td class="${riskClass}">${riskLabel}</td>
                <td class="score">${row.score}</td>
                <td class="timestamp">${dateStr}<br>${timeStr}</td>
            </tr>`;
        });

        tbody.innerHTML = html;
        recordCount.textContent = data.length;
    }

    async function triggerScan() {
        const btn = event.target;
        btn.disabled = true;
        btn.textContent = '⏳ Scanning...';

        try {
            await fetch('/scan', { method: 'POST' });
            
            // Wait a moment for scan to start processing
            setTimeout(async () => {
                await loadAlerts();
                btn.disabled = false;
                btn.textContent = '📡 Scan Now';
            }, 2000);
        } catch (e) {
            console.error('Scan failed:', e);
            btn.disabled = false;
            btn.textContent = '📡 Scan Now';
        }
    }

    // Initial load and auto-refresh
    loadAlerts();
    setInterval(loadAlerts, 10000);
</script>
</body>
</html>
"""

# -------------------------
# DASHBOARD
# -------------------------
@app.route("/")
def dashboard():
    return render_template_string(HTML)

# -------------------------
# LIVE API
# -------------------------
@app.route("/data")
def data():
    rows = get_alerts()

    cleaned = []
    for r in rows:
        cleaned.append({
            "name": r[0],
            "headline": r[1],
            "keyword": r[2],
            "risk_level": r[3],
            "score": r[4],
            "source": r[5],
            "source_url": r[6],
            "timestamp": r[7]
        })

    return jsonify(cleaned)

@app.route("/last-scan")
def last_scan():
    """Get the timestamp of the last alert added (last scan time)"""
    last_time = get_last_scan_time()
    return jsonify({
        "last_scan": last_time,
        "formatted": format_timestamp(last_time) if last_time else "No scan recorded"
    })

def format_timestamp(ts):
    """Format timestamp for display"""
    if not ts:
        return "No scan recorded"
    try:
        dt = datetime.fromisoformat(ts)
        return dt.strftime("%d %b %Y, %H:%M")
    except:
        return ts

# -------------------------
# INITIATE SCAN
# -------------------------
@app.route("/scan", methods=["POST"])
def scan_now():
    from threading import Thread
    from app import run_scan

    Thread(target=run_scan, daemon=True).start()
    return jsonify({"status": "Scan started"}), 202

# -------------------------
# CSV EXPORT
# -------------------------
@app.route("/export-csv")
def export_csv():
    rows = get_alerts()

    buffer = io.StringIO()
    writer = csv.writer(buffer)
    
    # Write header
    writer.writerow(["Entity", "Headline", "Risk Level", "Score", "Source", "Keyword", "Timestamp"])
    
    # Write data rows
    for r in rows:
        writer.writerow([r[0], r[1], r[3], r[4], r[5], r[2], r[7]])
    
    # Convert StringIO to BytesIO
    output = io.BytesIO()
    output.write(buffer.getvalue().encode('utf-8'))
    output.seek(0)

    return send_file(
        output,
        mimetype='text/csv',
        as_attachment=True,
        download_name=f"aml_alerts_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    )

# -------------------------
# PDF EXPORT (COMPLIANCE REPORT)
# -------------------------
@app.route("/export")
def export_pdf():

    rows = get_alerts()

    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)

    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, 750, "AML COMPLIANCE REPORT")

    c.setFont("Helvetica", 10)

    y = 720

    for r in rows[:40]:
        text = f"{r[0]} | {r[1][:60]} | {r[5] or '-'} | {r[6] or '-'} | {r[2]} | {r[3]} | {r[4]}"
        c.drawString(50, y, text)
        y -= 15

        if y < 50:
            c.showPage()
            y = 750

    c.save()
    buffer.seek(0)

    return send_file(buffer,
                     as_attachment=True,
                     download_name="aml_report.pdf",
                     mimetype="application/pdf")

# -------------------------
# RUN
# -------------------------
if __name__ == "__main__":
    app.run(debug=True)
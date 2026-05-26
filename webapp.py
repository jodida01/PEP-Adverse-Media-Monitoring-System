from flask import Flask, render_template_string, jsonify, request, send_file
from database import get_alerts
from datetime import datetime
import io
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

app = Flask(__name__)

# -------------------------
# DASHBOARD UI (PRODUCTION STYLE)
# -------------------------
HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>AML Production Dashboard</title>

    <style>
        body {
            font-family: 'Inter', Arial, sans-serif;
            margin: 0;
            padding: 0;
            background: linear-gradient(180deg, #e7f5ff 0%, #f8fdff 100%);
            color: #0f172a;
        }

        .page {
            max-width: 1200px;
            margin: 0 auto;
            padding: 24px;
        }

        h1 {
            margin-bottom: 8px;
            color: #0f4c81;
        }

        p.subtitle {
            margin-top: 0;
            margin-bottom: 24px;
            color: #334155;
        }

        .controls {
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            margin-bottom: 18px;
        }

        .controls button {
            padding: 12px 18px;
            border: none;
            cursor: pointer;
            background: #0f766e;
            color: white;
            border-radius: 999px;
            transition: transform 0.16s ease, background 0.16s ease;
        }

        .controls button.scan {
            background: #1d4ed8;
        }

        .controls button.refresh {
            background: #0f766e;
        }

        .controls button.export {
            background: #2563eb;
        }

        .controls button:hover {
            transform: translateY(-1px);
            opacity: 0.95;
        }

        .status {
            margin-bottom: 18px;
            padding: 12px 16px;
            border-radius: 12px;
            background: #e0f2fe;
            color: #0f4c81;
            border: 1px solid #bae6fd;
            min-height: 48px;
        }

        table {
            width: 100%;
            border-collapse: collapse;
            background: white;
            border-radius: 18px;
            overflow: hidden;
            box-shadow: 0 18px 50px rgba(15, 23, 42, 0.08);
        }

        thead {
            background: #0f4c81;
            color: white;
        }

        th, td {
            padding: 14px 16px;
            text-align: left;
            font-size: 14px;
            line-height: 1.5;
        }

        td {
            border-bottom: 1px solid #e2e8f0;
        }

        tr:nth-child(even) td {
            background: #f8fbff;
        }

        .HIGH {
            color: #b91c1c;
            font-weight: 700;
        }

        .PEP {
            color: #1d4ed8;
            font-weight: 700;
        }

        .MEDIUM {
            color: #0f766e;
            font-weight: 700;
        }

        .LOW {
            color: #065f46;
        }

        .headline-cell {
            max-width: 420px;
            white-space: normal;
            word-wrap: break-word;
            overflow-wrap: anywhere;
        }

        @media (max-width: 960px) {
            th, td {
                padding: 12px;
            }
        }
    </style>
</head>

<body>
<div class="page">
    <h1>🔥 AML / PEP Real-Time Monitoring System</h1>
    <p class="subtitle">Source-based alerts from Kenyan regulators, courts, gazettes, and media feeds. Click Scan to refresh live data.</p>

    <div class="controls">
        <button onclick="loadData('ALL')">All Alerts</button>
        <button onclick="loadData('HIGH')">High Risk</button>
        <button onclick="loadData('PEP')">PEP Alerts</button>
        <button class="scan" onclick="triggerScan()">Scan Now</button>
        <button class="refresh" onclick="loadData(currentFilter)">Refresh</button>
        <button class="export" onclick="window.location='/export'">Export PDF</button>
    </div>

    <div id="status" class="status">Loading alerts...</div>

    <table>
        <thead>
            <tr>
                <th>Name</th>
                <th>Headline</th>
                <th>Source</th>
                <th>Link</th>
                <th>Keyword</th>
                <th>Risk Level</th>
                <th>Score</th>
                <th>Timestamp</th>
            </tr>
        </thead>
        <tbody id="table"></tbody>
    </table>
</div>

<script>
    let currentFilter = 'ALL';
    const statusEl = document.getElementById('status');

    async function triggerScan() {
        statusEl.textContent = 'Starting scan...';
        await fetch('/scan', { method: 'POST' });
        statusEl.textContent = 'Scan started. Refresh in a moment.';
    }

    async function loadData(filter='ALL') {
        currentFilter = filter;
        statusEl.textContent = 'Loading alerts...';

        const res = await fetch('/data?filter=' + filter);
        const data = await res.json();

        let rows = '';

        data.forEach(r => {
            let riskClass = '';
            if (r.risk_level && r.risk_level.includes('HIGH')) {
                riskClass = 'HIGH';
            } else if (r.risk_level && r.risk_level.includes('PEP')) {
                riskClass = 'PEP';
            } else if (r.risk_level && r.risk_level.includes('MEDIUM')) {
                riskClass = 'MEDIUM';
            } else {
                riskClass = 'LOW';
            }

            rows += `
            <tr>
                <td>${r.name}</td>
                <td class="headline-cell">${r.headline}</td>
                <td>${r.source || '-'}</td>
                <td>${r.source_url ? `<a href="${r.source_url}" target="_blank">Open</a>` : '-'}</td>
                <td>${r.keyword}</td>
                <td class="${riskClass}">${r.risk_level || ''}</td>
                <td>${r.score}</td>
                <td>${r.timestamp}</td>
            </tr>`;
        });

        document.getElementById('table').innerHTML = rows;
        statusEl.textContent = data.length ? `Showing ${data.length} alerts.` : 'No alerts found.';
    }

    setInterval(() => loadData(currentFilter), 10000);
    loadData('ALL');
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
    filter_type = request.args.get("filter", "ALL")

    rows = get_alerts()

    cleaned = []
    for r in rows:
        risk = (r[3] or "").upper()

        if filter_type == "HIGH" and "HIGH" not in risk:
            continue
        if filter_type == "PEP" and "PEP" not in risk:
            continue

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
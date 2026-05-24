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
            font-family: Arial;
            margin: 25px;
            background: #f4f6f9;
        }

        h1 {
            color: #2c3e50;
        }

        .controls {
            margin-bottom: 15px;
        }

        button {
            padding: 10px 14px;
            margin-right: 8px;
            border: none;
            cursor: pointer;
            background: #2c3e50;
            color: white;
            border-radius: 5px;
        }

        button:hover {
            background: #1a252f;
        }

        table {
            width: 100%;
            border-collapse: collapse;
            background: white;
            margin-top: 15px;
        }

        th, td {
            padding: 10px;
            border: 1px solid #ddd;
            font-size: 14px;
        }

        th {
            background: #2c3e50;
            color: white;
        }

        .HIGH {
            color: red;
            font-weight: bold;
        }

        .PEP {
            color: purple;
            font-weight: bold;
        }
    </style>
</head>

<body>

<h1>🔥 AML / PEP Real-Time Monitoring System</h1>

<div class="controls">
    <button onclick="loadData('ALL')">All Alerts</button>
    <button onclick="loadData('HIGH')">High Risk</button>
    <button onclick="loadData('PEP')">PEP Alerts</button>
    <button onclick="window.location='/export'">Export PDF</button>
</div>

<table>
    <thead>
        <tr>
            <th>Name</th>
            <th>Headline</th>
            <th>Keyword</th>
            <th>Risk Level</th>
            <th>Score</th>
            <th>Timestamp</th>
        </tr>
    </thead>

    <tbody id="table"></tbody>
</table>

<script>

async function loadData(filter="ALL") {

    const res = await fetch("/data?filter=" + filter);
    const data = await res.json();

    let rows = "";

    data.forEach(r => {

        let riskClass = "";

        if (r.risk_level && r.risk_level.includes("HIGH")) {
            riskClass = "HIGH";
        } else if (r.risk_level && r.risk_level.includes("PEP")) {
            riskClass = "PEP";
        }

        rows += `
        <tr>
            <td>${r.name}</td>
            <td>${r.headline}</td>
            <td>${r.keyword}</td>
            <td class="${riskClass}">${r.risk_level || ""}</td>
            <td>${r.score}</td>
            <td>${r.timestamp}</td>
        </tr>
        `;
    });

    document.getElementById("table").innerHTML = rows;
}

// auto refresh every 5 seconds
setInterval(() => loadData("ALL"), 5000);
loadData("ALL");

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
            "timestamp": r[5]
        })

    return jsonify(cleaned)

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
        text = f"{r[0]} | {r[1][:60]} | {r[2]} | {r[3]} | {r[4]}"
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
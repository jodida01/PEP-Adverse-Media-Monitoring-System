from flask import Flask, render_template_string, redirect, url_for
import csv
import subprocess

app = Flask(__name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>AML Monitoring Dashboard</title>
    <style>
        body { font-family: Arial; margin: 40px; background: #f4f6f9; }
        h1 { color: #333; }

        .btn {
            background-color: #2c3e50;
            color: white;
            padding: 10px 20px;
            border: none;
            cursor: pointer;
            margin-bottom: 20px;
            font-size: 16px;
        }

        .btn:hover {
            background-color: #1a252f;
        }

        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }

        th, td {
            padding: 12px;
            border: 1px solid #ddd;
            text-align: left;
        }

        th {
            background-color: #2c3e50;
            color: white;
        }

        tr:nth-child(even) {
            background-color: #f2f2f2;
        }

        .risk {
            color: red;
            font-weight: bold;
        }
    </style>
</head>
<body>

<h1>AML / PEP Monitoring Dashboard</h1>

<a href="/run">
    <button class="btn">RUN SCAN</button>
</a>

<table>
    <tr>
        <th>Name</th>
        <th>Headline</th>
        <th>Keyword</th>
    </tr>

    {% for row in data %}
    <tr>
        <td>{{ row[0] }}</td>
        <td>{{ row[1] }}</td>
        <td class="risk">{{ row[2] }}</td>
    </tr>
    {% endfor %}

</table>

</body>
</html>
"""

# =========================
# DASHBOARD PAGE
# =========================
@app.route("/")
def dashboard():

    data = []

    try:
        with open("alerts.csv", "r", encoding="utf-8") as file:
            reader = csv.reader(file)
            next(reader)
            data = list(reader)
    except:
        data = []

    return render_template_string(HTML_TEMPLATE, data=data)

# =========================
# RUN SCAN BUTTON ACTION
# =========================
@app.route("/run")
def run_scan():

    # Run your AML script
    subprocess.run(["python", "app.py"])

    return redirect(url_for("dashboard"))

if __name__ == "__main__":
    app.run(debug=True)
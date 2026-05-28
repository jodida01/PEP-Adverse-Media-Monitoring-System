PEP & Adverse Media Monitoring System
A compliance-focused web application designed to support Anti-Money Laundering (AML) operations through automated Politically Exposed Person (PEP) screening and adverse media monitoring.
This system helps analysts identify high-risk individuals, assess reputational risks, and streamline suspicious activity reviews.
Key Features


🔍 PEP Screening

Identify politically exposed persons from structured datasets
Flag high-risk individuals for enhanced due diligence (EDD)



📰 Adverse Media Monitoring

Scan and retrieve negative news related to individuals/entities
Highlight risk indicators such as fraud, corruption, or sanctions



⚠️ Risk Scoring Engine

Assign risk levels (Low / Medium / High)
Combine PEP status and adverse media signals



📊 Compliance Dashboard

View alerts and monitoring results in real time
Simplified interface for AML analysts



📝 Case Review Support

Generate investigation summaries
Support STR/SAR reporting workflows




🧱 System Architecture
Plain TextFrontend (Web UI)        │        ▼Backend (Python / Flask or FastAPI)        │        ├── PEP Dataset        ├── News / Media Sources

Frontend (Web UI)
        │
        ▼
Backend (Python / Flask or FastAPI)
        │
        ├── PEP Dataset
        ├── News / Media Sources
        └── Risk Scoring Logic

 Clone the repository

git clone https://github.com/jodida01/PEP-Adverse-Media-Monitoring-System.git
cd PEP-Adverse-Media-Monitoring-System

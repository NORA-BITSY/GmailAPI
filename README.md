# Gmail Forensic Export System

A robust, legally defensible, and cryptographically verifiable tool for extracting targeted Gmail communications for legal, forensic, and compliance investigations.

## 🚀 Key Features

-   **Surgical Extraction**: Targeted searches by domain, name, case number, or keywords.
-   **Forensic Integrity**: Full metadata, message body (txt/html), and attachment collection.
-   **Data Verification**: Automatic SHA-256 hashing of all artifacts and generation of a `MANIFEST.json`.
-   **Timeline Generation**: Automatically builds CSV and Markdown timelines, tagging critical events and windows.
-   **Stateful Resumption**: Tracks progress in a local SQLite database to handle interruptions and skip already processed messages.
-   **Auditability**: Provides structured JSONL logs and a comprehensive export summary report detailing any failures.

---

## 📚 Documentation

Detailed documentation is available in the [`docs/`](docs/) directory:

-   **[Authentication Guide](docs/authentication.md)**: How to set up OAuth 2.0 and authenticate in headless or local environments.
-   **[Configuration Guide](docs/configuration.md)**: Detailed breakdown of `config.yml` parameters.
-   **[Export Logic & Integrity](docs/export_logic.md)**: Technical details on search queries, extraction, and cryptographic verification.
-   **[North Star Alignment](NORTHSTAR.md)**: The core pillars and future roadmap for the project's development.

---

## 🛠️ Quick Start

### 1. Prerequisites
-   Python 3.10+
-   A Google Cloud Project with the Gmail API enabled.
-   A `credentials.json` file from your Google Cloud Desktop app credential.

### 2. Setup
Clone the repository and install dependencies:
```bash
pip install -r requirements.txt
```

### 3. Authentication
If on a headless server, use the helper scripts:
```bash
python3 generate_auth.py
# Visit the URL, authorize, and then:
python3 complete_auth.py "YOUR_CODE"
```
*(See the [Authentication Guide](docs/authentication.md) for more details.)*

### 4. Configuration
Edit `config.yml` to define your search targets, date ranges, and critical windows.

### 5. Run Export
Execute the wrapper script:
```bash
./run_export.sh
```

---

## 📂 Output Structure

All extracted data is stored in the `export_results/` directory:

```text
export_results/
├── MANIFEST.json           # Cryptographic manifest of all files
├── run_log.jsonl          # Structured audit log
├── bodies/                # Raw metadata and message bodies (txt/html)
├── attachments/           # Downloaded attachments
├── timelines/             # CSV and Markdown forensic timelines
└── reports/               # Export summary and failure reports
```

## ⚖️ License & Ethics

This tool is designed for authorized forensic and legal investigations. Users are responsible for ensuring all data collection complies with local laws, privacy regulations (GDPR, CCPA), and organizational policies.

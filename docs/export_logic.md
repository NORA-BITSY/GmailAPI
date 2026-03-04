# Export Logic & Data Integrity

The Gmail Forensic Export tool is designed with a focus on **defensibility, auditability, and data integrity**. This document details the technical processes that ensure the exported data is reliable for legal or forensic review.

## 1. Surgical Search Logic

The tool does not perform a "full dump" of the inbox. Instead, it generates a series of targeted Gmail search queries based on your `config.yml`. These queries are combined with date filters and executed in batches to ensure thoroughness while respecting API limits.

- **Domain Filters**: Uses `from:domain.com OR to:domain.com`.
- **Name/Keyword Filters**: Uses `OR` operators to group terms.
- **Deduplication**: The tool collects all message IDs from all queries and deduplicates them into a unique set before extraction begins.

## 2. Forensic Extraction Process

For each message, the tool performs the following:

### A. Full Metadata Capture
The entire raw message JSON object from the Gmail API is saved as a `.meta.json` file. This captures all original headers, labels, and thread IDs.

### B. Body Extraction
The system parses the multi-part MIME structure to extract:
- **`text/plain`**: Saved as a `.txt` file.
- **`text/html`**: Saved as an `.html` file.
These files are extracted exactly as they appear in the source, without modification.

### C. Atomic Attachment Collection
Attachments are downloaded individually. The system:
- Verifies the extension against the `priority_exts` list.
- Checks the file size before attempting to download.
- Uses exponential backoff for large attachment transfers.

## 3. Data Integrity & Verification

### SHA-256 Hashing
A cryptographic SHA-256 hash is calculated for **every file** written to the disk (metadata, bodies, attachments, and reports). These hashes are stored in the `MANIFEST.json` at the end of the export session.

### Manifest Integrity
The `MANIFEST.json` acts as the "Source of Truth" for the export. It includes:
- **`export_id`**: A unique UUID for each run.
- **`export_timestamp_utc`**: Precise time of extraction.
- **`file_manifest`**: A list of every file, its relative path, its size in bytes, and its SHA-256 hash.

## 4. Error Handling & State (Stateful Resumption)

The `export_cache.db` (SQLite) is used to ensure the tool's reliability:
- **`processed_messages`**: Tracks every message ID that has been successfully exported. If the script is interrupted, it will skip already processed IDs.
- **`extraction_errors`**: Tracks every specific failure (e.g., a single attachment that failed to download). This ensures that failures are **auditable** rather than silent.

## 5. Output Artifacts

The `export_results/` directory is structured as follows:
- **`bodies/`**: Contains `.meta.json`, `.txt`, and `.html` files for each message.
- **`attachments/`**: Contains original files, prefixed with the Gmail message ID.
- **`timelines/`**: Contains `forensic_timeline.csv` and `forensic_timeline.md`.
- **`reports/`**: Contains `export_summary.md`, providing a high-level overview and a failure report.
- **`run_log.jsonl`**: A structured audit log of every operation performed by the script.
- **`MANIFEST.json`**: The cryptographically verifiable manifest of all artifacts.

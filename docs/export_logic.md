# Export Logic & Data Integrity (v2.0)

The Gmail Forensic Export tool is built on the **Dual-Stream Output Mandate**. It separates raw evidentiary data from human-readable investigative narratives to ensure courtroom defensibility.

## 1. Contextual Search (Thread Expansion)

Unlike standard search tools, this system prioritizes **Contextual Completeness**.
1.  **Initial Search**: Executes targeted queries (Domains, Names, Case Numbers, Keywords) to find matching messages.
2.  **Thread Identification**: Collects every unique `threadId` from the initial results.
3.  **Expansion**: Fetches **every message** in those threads, even if individual replies do not match the search terms. This prevents "evidence cherry-picking" and ensures the full conversation history is preserved.

## 2. Dual-Stream Output Structure

Extracted data is strictly divided into two root directories:

### A. The Forensic Archive (`archive/`) - "The Lockbox"
This directory contains the immutable, raw evidence required for expert verification.
*   **`metadata/`**: Contains raw `.meta.json` files for every message, preserving original headers and Gmail-specific system metadata.
*   **`attachments/`**: Bit-for-bit copies of all attachments, prefixed by the message ID.
*   **Integrity**: Files here are never modified or "beautified."

### B. The Investigative Narrative (`narrative/`) - "The Story"
This directory contains derived artifacts designed for human analysis and rapid investigation.
*   **`metadata/`**: Decoded `text/plain` and `text/html` bodies for searchable review.
*   **`timelines/`**: Chronological CSV and Markdown reports.
*   **`reports/`**: High-level export summaries and failure logs.

## 3. Data Integrity & Chain of Custody

### SHA-256 Cryptographic Manifest
At the conclusion of an export, the system hashes every file written to the disk. The resulting `MANIFEST.json` includes:
*   **Environmental Metadata**: OS, Platform, Python version, and the executing User.
*   **Search Space Documentation**: Every query and date range used, providing "Negative Auditability."
*   **File Registry**: Filename, size in bytes, and SHA-256 hash.

### Cross-Validation
The system cross-references the `expected_size` from the Gmail API metadata against the `actual_size` of the downloaded artifact. Any discrepancy is flagged as a `CORRUPTION_ERROR` in the audit log.

## 4. Error Handling (Stateful Resumption)

The tool uses a SQLite database (`export_cache.db`) to ensure reliability:
*   **`processed_messages`**: Ensures that interrupted exports can resume exactly where they left off without duplicating data.
*   **`extraction_errors`**: Every failure (API timeouts, missing attachments, size mismatches) is recorded persistently. **Failures are never silent.**

# 🌟 North Star Alignment: Gmail Forensic Export System

## 1. Vision Statement
To provide a legally defensible, cryptographically verifiable, and highly reliable automated extraction tool for Google Workspace (Gmail) data. The system must empower legal, HR, and forensic investigative teams to precisely target, safely extract, and comprehensively document communication timelines critical to legal proceedings, audits, and compliance reviews.

## 2. Core Mission
The system operates under the assumption that **every extracted byte may be scrutinized in a legal setting**. Therefore, the extraction process must prioritize data integrity, chain-of-custody documentation, and error transparency above speed or user-interface convenience.

---

## 3. The Four Pillars of Alignment

Any future modifications, refactoring, or feature additions **must** align with these four foundational pillars:

### Pillar 1: Defensibility & Data Integrity (The "Chain of Custody")
*   **Immutability:** Extracted artifacts (bodies, attachments, metadata) must never be altered once written.
*   **Cryptographic Verification:** Every extracted file must be immediately hashed (SHA-256) and recorded in an immutable `MANIFEST.json`.
*   **No Silent Failures:** If an attachment cannot be downloaded or a message cannot be parsed, it must be explicitly logged as a failure rather than skipped silently.

### Pillar 2: Precision & Contextual Awareness
*   **Surgical Extraction:** The system must avoid "data dumping." It should intelligently utilize configuration parameters (target domains, specific individuals, case numbers, and keywords) to extract only what is relevant.
*   **Temporal Context:** Features like `critical_windows` (e.g., retaliation periods, specific meetings) must be prominent, allowing investigators to quickly surface emails sent during high-stakes timeframes.

### Pillar 3: Unyielding Reliability
*   **Resilience to API Limits:** The Gmail API imposes strict quotas. The system must respect rate limits, implement exponential backoff, and handle network interruptions gracefully.
*   **Stateful Resumption:** Large exports can take hours. The SQLite cache (`export_cache.db`) must track progress so the script can be interrupted and resumed without duplicating work or missing messages.

### Pillar 4: Machine & Human Auditability
*   **Structured Logging:** Operations must be logged in a machine-readable format (JSONL) for automated ingestion into SIEM or log-analysis tools.
*   **Human-Readable Summaries:** The system must generate clear, actionable artifacts—such as the Markdown timeline and summary report—so non-technical legal staff can immediately understand the output.

---

## 4. Current State vs. Future Upgrades (Roadmap)

As the system undergoes various upgrades, development should be prioritized according to this roadmap to maintain alignment with the North Star.

### Phase 1: Enhanced Forensic Deep-Dive (Near Term)
*   **Thread Reconstruction:** Move beyond individual message extraction to map out full conversation threads, identifying missing messages or deleted replies.
*   **Drive Link Resolution:** Detect Google Drive/Docs links within emails and (if authorized) extract the linked documents, as these often contain the actual evidence.
*   **Advanced Attachment Parsing:** Implement OCR for image attachments or automatic text extraction from PDFs to ensure keywords hidden in attachments are flagged.

### Phase 2: Intelligence & Triage (Mid Term)
*   **Sentiment & Behavioral Analysis:** Utilize NLP to flag emails showing high emotional intensity, aggressive language, or sudden shifts in communication patterns between targets.
*   **Entity Mapping:** Automatically generate communication graphs (who spoke to whom, and how often) to identify undocumented back-channel communications.
*   **De-duplication & Thread Collapsing:** Visually collapse standard email signatures, legal disclaimers, and quoted previous messages to reduce investigator reading fatigue.

### Phase 3: Enterprise Scalability & Packaging (Long Term)
*   **Containerization:** Package the system in a Docker container for reproducible, cross-platform execution without dependency conflicts.
*   **Multi-Account Extraction (Domain-Wide Delegation):** Upgrade authentication from single-user OAuth to Google Workspace Domain-Wide Delegation (Service Accounts) to allow simultaneous extraction across multiple employee inboxes.
*   **Review Platform Integration:** Export data directly into standard eDiscovery load file formats (e.g., Relativity, Concordance) rather than relying solely on raw file structures.

---

## 5. Upgrade Checklist (The Alignment Test)

Before merging any future upgrade, ask the following questions:
1.  *Does this change alter the raw data?* (If yes, reject or isolate to a derivative output).
2.  *Are all new artifacts added to the cryptographic manifest?*
3.  *Does this change respect API rate limits and resumption states?*
4.  *Is the new behavior thoroughly logged in the JSONL audit trail?*
5.  *Does this feature help legal/investigative teams establish facts faster?*

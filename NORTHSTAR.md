# 🌟 North Star: Gmail Forensic Export System (v5.0 - Full Lifecycle Alignment)

## 1. Vision Statement
To provide an **unassailable evidentiary foundation** for digital investigations. We bridge the gap between "Raw Data" and "Legal Truth" by ensuring that every collection is surgical enough to be relevant, yet contextual enough to be fair.

## 2. Core Strategic Goals (The Outcomes)
*   **Evidentiary Integrity (Non-Repudiation):** The primary outcome is a "frozen" archive. No matter how much time passes, an independent expert must be able to verify that the data matches the state of the source at the exact moment of collection.
*   **Contextual Completeness (The Thread Mandate):** A single email is rarely the whole truth. Our goal is to collect the **minimum viable context**—defined as the entire conversation thread for any message matching our criteria—to prevent "cherry-picking" evidence.
*   **Negative Auditability:** We document the "Search Space." Success isn't just finding what you looked for; it's proving that if something wasn't found, it's because it didn't exist within the defined parameters (Queries + Date Ranges + Entity Lists).
*   **Surgical Efficiency:** We eliminate "Reviewer Fatigue" by ensuring that collected data is high-signal, reducing the cost and legal risk of broad, over-broad data dumps.

---

## 3. The Dual-Stream Output Mandate
To survive a stress test in court, the system must produce two strictly separated streams:

1.  **The Forensic Archive (The "Lockbox"):** 
    *   **Content:** Raw JSON metadata, original MIME bodies, and bit-for-bit attachment copies.
    *   **Structure:** Located in `evidence/archive/`.
    *   **Integrity:** Protected by SHA-256 hashes in a signed `MANIFEST.json`.
    *   **Goal:** Defensibility and expert verification.
2.  **The Investigative Narrative (The "Story"):** 
    *   **Content:** Decoded text, searchable timelines, failure summaries, and search queries.
    *   **Structure:** Located in `evidence/narrative/`.
    *   **Enrichment:** Includes window tagging, sentiment flags, and thread visualizations.
    *   **Goal:** Human understanding and investigative speed.

---

## 4. Chain of Custody & Handling Protocol
An export is only evidence if its history is documented.
*   **Collection Metadata:** Every run must log the collector's environment (OS, Python version, User ID) and the exact code version used.
*   **Validation Requirement:** Post-export, the user should be prompted to verify the `MANIFEST.json` against the files to confirm no corruption occurred during transit.
*   **Immutability:** Once the `MANIFEST.json` is generated, the `evidence/` directory should be treated as **Read-Only**.

---

## 5. Entity Resolution & Contextual Logic
*   **The Entity Bridge:** We don't just search for "Names"; we search for "Entities." Future updates should map aliases (e.g., "John Doe" vs "j.doe@company.com") to ensure no context is lost due to varying email formats.
*   **Ghost Message Detection:** If a thread contains a reference to a message ID that the system cannot find (e.g., it was deleted), this must be flagged as a "Missing Link" in the narrative report.

---

## 6. Critical Pitfalls & Blindspots (The "Never" List)
*   **Never allow "Silent Omissions":** If an attachment is skipped due to size, or a body is unreadable, it is a **loud failure**.
*   **Never mix Archive and Narrative:** Narrative files (like timelines) should never be stored in the same folder as raw artifacts.
*   **Never assume "API Success" equals "Data Success":** Cross-validate file sizes and checksums.
*   **Never ignore the "Search Space":** Always document what was *not* found by logging the exact queries executed.

---

## 7. The "Courtroom" Alignment Test
Before any update, ask:
1.  **Could a hostile expert witness prove we cherry-picked data?** (If yes, expand context/threads).
2.  **Is the "Lockbox" protected from interpretation bias?** (Ensure raw data remains raw).
3.  **Is the narrative easily explainable to a non-technical judge?**
4.  **Are we logging the *process* as well as the *data*?**

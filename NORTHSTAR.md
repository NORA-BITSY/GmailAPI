# 🌟 North Star: Gmail Forensic Export System (v4.0 - Forensic Stress-Tested)

## 1. Vision Statement
To provide an **unassailable evidentiary foundation** for digital investigations. We bridge the gap between "Raw Data" and "Legal Truth" by ensuring that every collection is surgical enough to be relevant, yet contextual enough to be fair.

## 2. Core Strategic Goals (The Outcomes)
*   **Evidentiary Integrity (Non-Repudiation):** The primary outcome is a "frozen" archive. No matter how much time passes, an independent expert must be able to verify that the data matches the state of the source at the exact moment of collection.
*   **Contextual Completeness:** We recognize that a single "smoking gun" email is useless without the surrounding conversation. Our goal is to collect the **minimum viable context** (threads, replies, referenced docs) required to tell a fair and complete story.
*   **Negative Auditability:** In forensics, knowing what *isn't* there is as important as what *is*. The system must document the "Search Space"—proving that if an email wasn't collected, it was because it didn't exist within the defined parameters, not because of a system blindspot.
*   **Surgical Efficiency:** We eliminate "Reviewer Fatigue" by ensuring that 90% of the collected data is relevant to the case, thereby reducing the cost and time of legal review.

---

## 3. Real-World Constraints & Non-Goals
To avoid "feature creep" that degrades forensic value, we maintain these boundaries:

*   **Non-Goal: Real-Time Sync:** We are not a backup solution. We capture a **point-in-time snapshot**. We do not attempt to reflect changes made to the source after the extraction begins.
*   **Non-Goal: Data "Cleaning":** We do not alter headers, fix malformed MIME, or "beautify" raw evidence. Usability is handled in the **Narrative Layer**, never the **Archive Layer**.
*   **Non-Goal: Automated Judgment:** The tool flags; it does not judge. We provide indicators (tags, windows, keywords), but we never produce a "Guilty/Innocent" or "True/False" output.

---

## 4. The Dual-Stream Output Mandate
To survive a stress test in court, the system must produce two strictly separated streams:

1.  **The Forensic Archive (The "Lockbox"):** 
    *   Raw, untouched JSON metadata and original MIME bodies.
    *   Cryptographic manifests for every byte.
    *   **Goal:** Defensibility.
2.  **The Investigative Narrative (The "Story"):** 
    *   Extracted text, readable timelines, and tagged windows.
    *   Search summaries and failure reports.
    *   **Goal:** Human understanding and speed.

---

## 5. Critical Pitfalls & Blindspots (The "Never" List)
*   **Never allow "Silent Omissions":** If an attachment is too large or a body is unreadable, it is a **loud failure**. We never assume "no data" means "success."
*   **Never mix Archive and Narrative:** If a user wants to "redact" a timeline, the redacted version is a new file; the original archive remains untouched.
*   **Never ignore the "Search Space":** A report that says "0 results found" is incomplete without a list of the exact queries and date ranges that yielded that zero.
*   **Never assume "API Success" equals "Data Success":** We must cross-validate (e.g., if the metadata says there is a 5MB attachment, but the download is 0 bytes, the system must flag a corruption error).

---

## 6. The "Courtroom" Alignment Test
Before any update, ask:
1.  **If a hostile expert witness analyzed this, could they prove I missed data?**
2.  **Does this update make it easier to prove the data hasn't been tampered with?**
3.  **Does this feature help the investigator explain *why* this data is relevant?**
4.  **Are we maintaining the "Lockbox" vs "Story" separation?**

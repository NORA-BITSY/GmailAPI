# Configuration Guide (`config.yml`)

The `config.yml` file is the master blueprint for the forensic export. It defines the **Search Space**—the legal boundaries of your investigation.

## Core Sections

### `gmail`
*   **`credentials_path`**: Path to your Google Cloud Desktop OAuth credentials.
*   **`token_path`**: Destination for the active OAuth token.

### `export`
*   **`download_attachments`**: Enables/disables attachment collection.
*   **`max_attachment_size_mb`**: Critical for bypassing large, irrelevant files (e.g., video files) while ensuring legal documents are captured.
*   **`attachment_extensions_priority`**: Limits collection to legally relevant formats (PDF, DOCX, EML, etc.).

### `search` (The Temporal Boundary)
*   **`date_range_start`**: Messages sent before this date are ignored.
*   **`date_range_end`**: Messages sent after this date are ignored.

### `targets` (The Investigative Scope)
These parameters define the Gmail search query. The system automatically performs **Thread Expansion** on matches found here.
*   **`domains`**: Filters by sender/recipient domain.
*   **`names`**: Filters by specific individual names.
*   **`case_numbers`**: Searches for specific litigation or reference IDs.
*   **`keywords`**: Searches for high-value terms (e.g., "retaliation", "dispute").

### `critical_windows` (Narrative Enrichment)
Defines sub-periods within the search range that require special attention.
*   Emails falling within these windows are tagged in the `narrative/timelines/` reports.
*   Useful for highlighting periods surrounding key events (e.g., a specific board meeting or a termination date).

### `reliability`
*   **`cache_db`**: The SQLite state tracker (`export_cache.db`).
*   **`rate_limit_units_per_second`**: Controls API throughput to prevent 429 errors.

---

## Technical Note on Search Space
Every parameter defined in `targets` and `search` is logged in the final `MANIFEST.json`. This ensures **Negative Auditability**: you can prove to a third party exactly what was requested, and therefore why certain data was excluded from the final evidence package.

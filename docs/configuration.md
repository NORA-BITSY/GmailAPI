# Configuration Guide (`config.yml`)

The `config.yml` file is the central control point for the Gmail Forensic Export tool. It defines what to search for, how to export it, and the operational parameters of the system.

## Sections

### `gmail`
- **`credentials_path`**: Absolute or relative path to your `credentials.json` file.
- **`token_path`**: Where to save/read the OAuth `token.json` file.
- **`scopes`**: The permissions the tool will request (defaults to `gmail.readonly`).

### `export`
- **`include_spam`**: Boolean. If true, include spam messages in the search.
- **`include_trash`**: Boolean. If true, include trash in the search.
- **`download_attachments`**: Boolean. Whether to download and verify message attachments.
- **`max_attachment_size_mb`**: Maximum size of a single attachment to download (e.g., `25`).
- **`attachment_extensions_priority`**: A list of extensions (e.g., `.pdf`, `.docx`) that the tool will prioritize for forensic collection.

### `search`
- **`date_range_start`**: Start date for extraction (Format: `YYYY-MM-DD`).
- **`date_range_end`**: End date for extraction (defaults to `null` which is today).

### `targets`
- **`domains`**: List of email domains (e.g., `company.com`) to filter by in `from:` or `to:` fields.
- **`names`**: Specific people or entities whose names should be included in the search query.
- **`case_numbers`**: Case reference IDs (e.g., `"2025FA000041"`) to search for within message contents.
- **`keywords`**: High-value search terms (e.g., `"retaliation"`, `"settlement"`) to target specific areas of investigation.

### `critical_windows`
These define specific periods of interest that will be tagged in the final forensic timeline.
- **`start`**: ISO timestamp (e.g., `"2025-09-14T00:00:00"`).
- **`end`**: ISO timestamp.
- **`tag`**: The label (e.g., `"RETALIATION_WINDOW"`) to appear in reports for emails sent during this window.

### `reliability`
- **`cache_db`**: Path to the SQLite database (`export_cache.db`) that tracks progress and resumption status.
- **`rate_limit_units_per_second`**: Max API requests per second to avoid Google quota errors (default: `200`).
- **`max_retries`**: Number of times to retry a failed API request with exponential backoff.
- **`batch_size`**: Number of message IDs to process in a single batch.

## Best Practices
1.  **Iterate Small**: Start with a very narrow `date_range_start` to test that the tool is capturing exactly what you expect.
2.  **Use Quotes**: For case numbers or complex names in `targets`, use double quotes in the YAML (e.g., `"46-CR-25-845"`).
3.  **Portability**: Use relative paths for `cache_db` if you plan to move the repository.

# Authentication Guide

This guide explains how to authenticate the Gmail Forensic Export tool, especially in headless or remote environments.

## Overview

Authentication is a multi-step process that utilizes Google OAuth 2.0. The repository contains several helper scripts to facilitate this:

1.  `generate_auth.py`: Generates an authorization URL.
2.  `complete_auth.py`: Exchanges an authorization code for a `token.json` file.
3.  `exchange_code.py`: A legacy helper for manual token exchange (use `complete_auth.py` for standard flows).

## Standard Authentication Flow

### 1. Generate Authorization URL
Run `generate_auth.py` on the target machine:
```bash
python3 generate_auth.py
```
This script will:
- Read your `credentials.json` path from `config.yml`.
- Output an `auth_url.txt` file containing the link you need to visit.
- Create a `flow_state.json` file to store the state (verifier) for the next step.

### 2. Authorize via Browser
Copy the URL from `auth_url.txt` and open it in a web browser where you are logged into the target Google account.
- Complete the Google OAuth consent screens.
- Once finished, you will be redirected to `localhost`. Copy the full redirect URL (even if the page doesn't load) or just the value of the `code=` parameter.

### 3. Complete the Flow
Return to the CLI and run `complete_auth.py` with the code:
```bash
python3 complete_auth.py "<PASTE_CODE_OR_URL_HERE>"
```
This script will:
- Use the state stored in `flow_state.json`.
- Fetch the access and refresh tokens from Google.
- Save them to `token.json` (the path is defined in `config.yml`).

## Automatic Authentication (Local Server)

If you are running the tool in a local environment with a graphical browser, the main script `export_gmail_pierce.py` can handle this automatically by launching a local server (port 41595). 

However, for headless remote servers (e.g., EC2, VPS), the **Standard Authentication Flow** above is required.

## Security Warning
- **`credentials.json`**: Contains your Google Cloud project credentials. Keep it secure.
- **`token.json`**: Contains active access/refresh tokens. **Never share this file or commit it to version control.**
- Both files are excluded by the `.gitignore` provided in this repository.

import os
import json
import sqlite3
import hashlib
import base64
import logging
import time
import uuid
import yaml
import argparse
from datetime import datetime, timezone
from typing import List, Dict, Any, Set

import pytz
from dateutil import parser as date_parser
from bs4 import BeautifulSoup
from tqdm import tqdm
from colorama import Fore, Style, init

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Initialize colorama
init(autoreset=True)

# Forensic Logger Setup
class ForensicLogger:
    def __init__(self, log_file):
        self.log_file = log_file
        self.logger = logging.getLogger("ForensicExport")
        self.logger.setLevel(logging.INFO)
        
        # Standard stream handler for console
        ch = logging.StreamHandler()
        ch.setFormatter(logging.Formatter(f'{Fore.CYAN}%(asctime)s{Style.RESET_ALL} [%(levelname)s] %(message)s'))
        self.logger.addHandler(ch)

    def _log_json(self, level, msg):
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": level,
            "message": msg
        }
        with open(self.log_file, 'a') as f:
            f.write(json.dumps(entry) + '\n')

    def info(self, msg):
        self.logger.info(msg)
        self._log_json("INFO", msg)

    def error(self, msg):
        self.logger.error(msg)
        self._log_json("ERROR", msg)

    def warning(self, msg):
        self.logger.warning(msg)
        self._log_json("WARNING", msg)

class GmailForensicExporter:
    def __init__(self, config_path, export_dir):
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        self.export_dir = export_dir
        os.makedirs(self.export_dir, exist_ok=True)
        os.makedirs(os.path.join(self.export_dir, 'bodies'), exist_ok=True)
        os.makedirs(os.path.join(self.export_dir, 'attachments'), exist_ok=True)
        os.makedirs(os.path.join(self.export_dir, 'timelines'), exist_ok=True)
        os.makedirs(os.path.join(self.export_dir, 'reports'), exist_ok=True)

        self.log = ForensicLogger(os.path.join(self.export_dir, 'run_log.jsonl'))
        self.db_path = self.config['reliability']['cache_db']
        self.init_db()
        
        self.creds = None
        self.service = None
        self.manifest = {
            "export_id": str(uuid.uuid4()),
            "export_timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "file_manifest": []
        }

    def init_db(self):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS processed_messages 
                     (gmail_id TEXT PRIMARY KEY, thread_id TEXT, processed_at TEXT, status TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS extraction_errors 
                     (gmail_id TEXT, error_type TEXT, error_msg TEXT, timestamp TEXT)''')
        conn.commit()
        conn.close()

    def log_error_to_db(self, msg_id, error_type, error_msg):
        conn = sqlite3.connect(self.db_path, timeout=10)
        c = conn.cursor()
        c.execute("INSERT INTO extraction_errors (gmail_id, error_type, error_msg, timestamp) VALUES (?, ?, ?, ?)",
                  (msg_id, error_type, error_msg, datetime.now(timezone.utc).isoformat()))
        conn.commit()
        conn.close()

    def authenticate(self):
        token_path = self.config['gmail']['token_path']
        creds_path = self.config['gmail']['credentials_path']
        scopes = self.config['gmail']['scopes']

        if os.path.exists(token_path):
            self.creds = Credentials.from_authorized_user_file(token_path, scopes)
        
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                self.creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(creds_path, scopes)
                # Headless environment handling
                auth_url, _ = flow.authorization_url(prompt='consent', access_type='offline')
                print(f"\n{Fore.YELLOW}Authorize the application by visiting this URL:{Style.RESET_ALL}")
                print(f"{Fore.CYAN}{auth_url}{Style.RESET_ALL}")
                
                try:
                    # Try local server first, with a longer timeout
                    print(f"\n{Fore.WHITE}Waiting for authorization via local server (timeout 5 mins)...{Style.RESET_ALL}")
                    self.creds = flow.run_local_server(port=41595, open_browser=False, timeout_seconds=300)
                except Exception as e:
                    print(f"\n{Fore.RED}Local server auth failed or timed out: {e}{Style.RESET_ALL}")
                    print(f"{Fore.YELLOW}Please provide the 'code' from the redirect URL manually.{Style.RESET_ALL}")
                    code = input("Enter the authorization code: ")
                    flow.fetch_token(code=code)
                    self.creds = flow.credentials
            
            with open(token_path, 'w') as token:
                token.write(self.creds.to_json())

        self.service = build('gmail', 'v1', credentials=self.creds)
        profile = self.service.users().getProfile(userId='me').execute()
        self.log.info(f"Authenticated as: {profile['emailAddress']}")
        
        # Rate Limiting setup
        self.rate_delay = 1.0 / self.config['reliability']['rate_limit_units_per_second']
        self.max_retries = self.config['reliability']['max_retries']
        
        return profile['emailAddress']

    def _execute_with_retry(self, request):
        for attempt in range(self.max_retries):
            try:
                time.sleep(self.rate_delay)
                return request.execute()
            except HttpError as e:
                status_code = e.resp.status
                if status_code in [403, 429]: # Rate limit or Forbidden
                    wait_time = (2 ** attempt) + (time.time() % 1)
                    self.log.warning(f"Rate limited (status {status_code}). Retrying in {wait_time:.2f}s...")
                    time.sleep(wait_time)
                elif status_code == 404:
                    self.log.error(f"Resource not found (404).")
                    return None
                else:
                    if attempt == self.max_retries - 1: raise
                    time.sleep(2 ** attempt)
            except Exception as e:
                if attempt == self.max_retries - 1:
                    raise
                self.log.warning(f"Request failed (attempt {attempt+1}/{self.max_retries}): {e}. Retrying...")
                time.sleep(2 ** attempt)  # Exponential backoff
        return None

    def get_search_queries(self) -> List[str]:
        targets = self.config['targets']
        search_cfg = self.config.get('search', {})
        
        # Build date filter
        date_filter = ""
        if search_cfg.get('date_range_start'):
            # Convert YYYY-MM-DD to YYYY/MM/DD for Gmail
            start = search_cfg['date_range_start'].replace("-", "/")
            date_filter += f" after:{start}"
        if search_cfg.get('date_range_end'):
            end = search_cfg['date_range_end'].replace("-", "/")
            date_filter += f" before:{end}"
        
        queries = []
        
        # Batch 1 - Names
        names = targets['names']
        for i in range(0, len(names), 5):
            batch = " OR ".join([f'"{n}"' for n in names[i:i+5]])
            queries.append(f"({batch}){date_filter}")
            
        # Batch 2 - Domains
        domains = targets['domains']
        domain_query = " OR ".join([f"from:{d} OR to:{d}" for d in domains])
        queries.append(f"({domain_query}){date_filter}")
        
        # Batch 3 - Case Numbers
        cases = targets['case_numbers']
        case_query = " OR ".join([f'"{c}"' for c in cases])
        queries.append(f"({case_query}){date_filter}")

        # Batch 4 - Keywords
        keywords = targets.get('keywords', [])
        if keywords:
            keyword_query = " OR ".join([f'"{kw}"' for kw in keywords])
            queries.append(f"({keyword_query}){date_filter}")
        
        return queries

    def execute_search(self):
        queries = self.get_search_queries()
        all_ids = set()
        
        for q in queries:
            self.log.info(f"Executing query: {q}")
            messages = []
            try:
                request = self.service.users().messages().list(userId='me', q=q)
                while request is not None:
                    result = self._execute_with_retry(request)
                    if 'messages' in result:
                        messages.extend(result['messages'])
                    request = self.service.users().messages().list_next(request, result)
            except Exception as e:
                self.log.error(f"Search error for query '{q}': {e}")
            
            self.log.info(f"Query returned {len(messages)} results.")
            for m in messages:
                all_ids.add(m['id'])
        
        self.log.info(f"Total unique candidate messages: {len(all_ids)}")
        return list(all_ids)

    def fetch_message_full(self, msg_id):
        try:
            request = self.service.users().messages().get(userId='me', id=msg_id, format='full')
            return self._execute_with_retry(request)
        except Exception as e:
            self.log.error(f"Error fetching message {msg_id}: {e}")
            return None

    def process_messages(self, msg_ids):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        exported_count = 0
        error_count = 0
        timeline_data = []
        
        for msg_id in tqdm(msg_ids, desc="Processing Messages"):
            c.execute("SELECT status FROM processed_messages WHERE gmail_id=?", (msg_id,))
            if c.fetchone():
                continue
            
            try:
                msg = self.fetch_message_full(msg_id)
                if not msg:
                    self.log_error_to_db(msg_id, "FETCH_FAILURE", "Failed to fetch full message content")
                    error_count += 1
                    continue
                    
                # Forensic extraction
                artifact_info = self.save_forensic_artifact(msg)
                timeline_data.append(artifact_info)
                
                status = 'completed' if artifact_info.get('all_attachments_saved', True) else 'completed_with_errors'
                if status == 'completed_with_errors':
                    error_count += 1
                
                c.execute("INSERT INTO processed_messages (gmail_id, thread_id, processed_at, status) VALUES (?, ?, ?, ?)",
                          (msg_id, msg['threadId'], datetime.now(timezone.utc).isoformat(), status))
                conn.commit()
                exported_count += 1
            except Exception as e:
                self.log_error_to_db(msg_id, "PROCESSING_EXCEPTION", str(e))
                self.log.error(f"Critical error processing message {msg_id}: {e}")
                error_count += 1
                conn.rollback()
            
        conn.close()
        self.log.info(f"Export session complete. Success: {exported_count}, Errors/Failures: {error_count}")
        
        if timeline_data:
            self.generate_timeline(timeline_data)

    def get_header(self, headers, name):
        for h in headers:
            if h['name'].lower() == name.lower():
                return h['value']
        return ""

    def save_forensic_artifact(self, msg):
        msg_id = msg['id']
        headers = msg['payload'].get('headers', [])
        
        # Extract metadata for timeline
        subject = self.get_header(headers, 'Subject')
        sender = self.get_header(headers, 'From')
        recipient = self.get_header(headers, 'To')
        date_str = self.get_header(headers, 'Date')
        
        # 1. Save Full Metadata JSON
        meta_path = os.path.join(self.export_dir, 'bodies', f"{msg_id}.meta.json")
        with open(meta_path, 'w') as f:
            json.dump(msg, f, indent=2)
        self.add_to_manifest(meta_path)

        # 2. Extract and Save Body
        parts = self.get_message_parts(msg['payload'])
        for mime_type, content in parts.items():
            ext = 'txt' if mime_type == 'text/plain' else 'html'
            body_path = os.path.join(self.export_dir, 'bodies', f"{msg_id}.{ext}")
            with open(body_path, 'w', encoding='utf-8') as f:
                f.write(content)
            self.add_to_manifest(body_path)

        # 3. Handle Attachments
        all_attachments_saved = True
        if self.config['export']['download_attachments']:
            results = self.download_attachments(msg_id, msg['payload'])
            if False in results:
                all_attachments_saved = False

        return {
            "id": msg_id,
            "date": date_str,
            "from": sender,
            "to": recipient,
            "subject": subject,
            "threadId": msg['threadId'],
            "all_attachments_saved": all_attachments_saved
        }

    def get_message_parts(self, payload):
        parts = {}
        if 'parts' in payload:
            for part in payload['parts']:
                parts.update(self.get_message_parts(part))
        else:
            mime_type = payload.get('mimeType')
            if mime_type in ['text/plain', 'text/html'] and 'data' in payload.get('body', {}):
                data = payload['body']['data']
                content = base64.urlsafe_b64decode(data).decode('utf-8')
                parts[mime_type] = content
        return parts

    def download_attachments(self, msg_id, payload):
        results = []
        if 'parts' in payload:
            for part in payload['parts']:
                if part.get('filename'):
                    results.append(self.save_attachment(msg_id, part))
                results.extend(self.download_attachments(msg_id, part))
        return results

    def save_attachment(self, msg_id, part):
        filename = part['filename']
        ext = os.path.splitext(filename)[1].lower()
        
        # Filters
        priority_exts = self.config['export']['attachment_extensions_priority']
        max_size = self.config['export']['max_attachment_size_mb'] * 1024 * 1024
        
        if ext not in priority_exts:
            return True # Not a failure, just skipped

        body = part.get('body', {})
        size = body.get('size', 0)
        
        if size > max_size:
            self.log.warning(f"Skipping large attachment: {filename} ({size} bytes)")
            return True

        attachment_id = body.get('attachmentId')
        if not attachment_id:
            return True

        try:
            request = self.service.users().messages().attachments().get(
                userId='me', messageId=msg_id, id=attachment_id)
            attachment = self._execute_with_retry(request)
            data = base64.urlsafe_b64decode(attachment['data'])
            
            # Save to attachments/msg_id_filename
            safe_filename = "".join([c for c in filename if c.isalnum() or c in ('.','_','-')]).strip()
            save_path = os.path.join(self.export_dir, 'attachments', f"{msg_id}_{safe_filename}")
            
            with open(save_path, 'wb') as f:
                f.write(data)
            
            self.add_to_manifest(save_path)
            self.log.info(f"Saved attachment: {filename} for message {msg_id}")
            return True
        except Exception as e:
            err_msg = f"Error downloading attachment {filename}: {e}"
            self.log.error(err_msg)
            self.log_error_to_db(msg_id, "ATTACHMENT_FAILURE", err_msg)
            return False

    def generate_timeline(self, timeline_data):
        # Sort by date
        def parse_dt(d):
            try: return date_parser.parse(d)
            except: return datetime.min.replace(tzinfo=timezone.utc)

        timeline_data.sort(key=lambda x: parse_dt(x['date']))
        
        # Check for critical windows
        windows = self.config.get('critical_windows', {})
        for item in timeline_data:
            item['tags'] = []
            item_dt = parse_dt(item['date'])
            for win_name, win_cfg in windows.items():
                start = date_parser.parse(win_cfg['start']).replace(tzinfo=item_dt.tzinfo)
                end = date_parser.parse(win_cfg['end']).replace(tzinfo=item_dt.tzinfo)
                if start <= item_dt <= end:
                    item['tags'].append(win_cfg.get('tag', win_name.upper()))

        csv_path = os.path.join(self.export_dir, 'timelines', 'forensic_timeline.csv')
        import csv
        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=["date", "from", "to", "subject", "id", "threadId", "tags"])
            writer.writeheader()
            for row in timeline_data:
                row_copy = row.copy()
                row_copy['tags'] = ";".join(row['tags'])
                writer.writerow(row_copy)
        
        self.add_to_manifest(csv_path)
        self.log.info(f"Timeline generated at {csv_path}")

        # Also generate a simple Markdown version for quick review
        md_path = os.path.join(self.export_dir, 'timelines', 'forensic_timeline.md')
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write("# Forensic Email Timeline\n\n")
            for item in timeline_data:
                tag_str = ""
                if item['tags']:
                    tag_str = " " + " ".join([f"`[{t}]`" for t in item['tags']])
                
                f.write(f"### {item['date']}{tag_str}\n")
                f.write(f"- **From:** {item['from']}\n")
                f.write(f"- **To:** {item['to']}\n")
                f.write(f"- **Subject:** {item['subject']}\n")
                f.write(f"- **ID:** `{item['id']}` | **Thread:** `{item['threadId']}`\n\n")
        
        self.add_to_manifest(md_path)
        self.generate_summary_report(timeline_data)

    def generate_summary_report(self, timeline_data):
        report_path = os.path.join(self.export_dir, 'reports', 'export_summary.md')
        critical_count = sum(1 for item in timeline_data if item['tags'])
        
        # Fetch errors for the report
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("SELECT gmail_id, error_type, error_msg FROM extraction_errors")
        errors = c.fetchall()
        conn.close()

        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("# Gmail Forensic Export Summary\n\n")
            f.write(f"- **Export ID:** `{self.manifest['export_id']}`\n")
            f.write(f"- **Timestamp:** {self.manifest['export_timestamp_utc']}\n")
            f.write(f"- **Total Messages Successfully Exported:** {len(timeline_data)}\n")
            f.write(f"- **Total Failures:** {len(errors)}\n")
            f.write(f"- **Critical Window Matches:** {critical_count}\n\n")
            
            f.write("## Search Parameters\n")
            f.write(f"```yaml\n{yaml.dump(self.config['targets'], default_flow_style=False)}```\n\n")
            
            if errors:
                f.write("## Extraction Failures\n")
                f.write("| Gmail ID | Error Type | Message |\n")
                f.write("| --- | --- | --- |\n")
                for eid, etype, emsg in errors:
                    f.write(f"| `{eid}` | {etype} | {emsg} |\n")
                f.write("\n")

            if critical_count > 0:
                f.write("## Critical Findings\n")
                for item in timeline_data:
                    if item['tags']:
                        f.write(f"- {item['date']}: {item['subject']} ([{', '.join(item['tags'])}])\n")
        
        self.add_to_manifest(report_path)
        self.log.info(f"Summary report generated at {report_path}")

    def add_to_manifest(self, file_path):
        # Just track the path, hashing happens in finalize()
        if not hasattr(self, '_pending_manifest_files'):
            self._pending_manifest_files = set()
        self._pending_manifest_files.add(file_path)

    def finalize(self):
        self.log.info("Finalizing export manifest and calculating hashes...")
        
        if not hasattr(self, '_pending_manifest_files'):
            self._pending_manifest_files = set()

        for file_path in self._pending_manifest_files:
            if not os.path.exists(file_path):
                continue
                
            sha256 = hashlib.sha256()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    sha256.update(chunk)
            
            self.manifest['file_manifest'].append({
                "filename": os.path.relpath(file_path, self.export_dir),
                "sha256": sha256.hexdigest(),
                "size_bytes": os.path.getsize(file_path)
            })

        manifest_path = os.path.join(self.export_dir, 'MANIFEST.json')
        with open(manifest_path, 'w') as f:
            json.dump(self.manifest, f, indent=2)
        self.log.info(f"Manifest written to {manifest_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Gmail Forensic Export Tool")
    parser.add_argument("--config", default="/home/ubuntu/config.yml")
    parser.add_argument("--export-dir", required=True)
    parser.add_argument("--verify-auth-only", action="store_true")
    args = parser.parse_args()

    exporter = GmailForensicExporter(args.config, args.export_dir)
    email = exporter.authenticate()
    
    if args.verify_auth_only:
        print(f"{Fore.GREEN}Authentication successful for: {email}")
    else:
        ids = exporter.execute_search()
        exporter.process_messages(ids)
        exporter.finalize()

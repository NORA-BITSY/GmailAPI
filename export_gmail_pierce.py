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
        self.logger = logging.getLogger("ForensicExport")
        self.logger.setLevel(logging.INFO)
        fh = logging.FileHandler(log_file)
        fh.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s] %(message)s'))
        self.logger.addHandler(fh)
        ch = logging.StreamHandler()
        ch.setFormatter(logging.Formatter(f'{Fore.CYAN}%(asctime)s{Style.RESET_ALL} [%(levelname)s] %(message)s'))
        self.logger.addHandler(ch)

    def info(self, msg): self.logger.info(msg)
    def error(self, msg): self.logger.error(msg)
    def warning(self, msg): self.logger.warning(msg)

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
                print(f"\n{Fore.YELLOW}Authorize the application by visiting this URL:{Style.RESET_ALL}")
                self.creds = flow.run_local_server(port=0, open_browser=False)
            
            with open(token_path, 'w') as token:
                token.write(self.creds.to_json())

        self.service = build('gmail', 'v1', credentials=self.creds)
        profile = self.service.users().getProfile(userId='me').execute()
        self.log.info(f"Authenticated as: {profile['emailAddress']}")
        return profile['emailAddress']

    def get_search_queries(self) -> List[str]:
        targets = self.config['targets']
        queries = []
        
        # Batch 1 - Names
        names = targets['names']
        for i in range(0, len(names), 5):
            batch = " OR ".join([f'"{n}"' for n in names[i:i+5]])
            queries.append(batch)
            
        # Batch 2 - Domains
        domains = targets['domains']
        domain_query = " OR ".join([f"from:{d} OR to:{d}" for d in domains])
        queries.append(domain_query)
        
        # Batch 3 - Case Numbers
        cases = targets['case_numbers']
        case_query = " OR ".join([f'"{c}"' for c in cases])
        queries.append(case_query)
        
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
                    result = request.execute()
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
            return self.service.users().messages().get(userId='me', id=msg_id, format='full').execute()
        except Exception as e:
            self.log.error(f"Error fetching message {msg_id}: {e}")
            return None

    def process_messages(self, msg_ids):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        exported_count = 0
        for msg_id in tqdm(msg_ids, desc="Processing Messages"):
            c.execute("SELECT status FROM processed_messages WHERE gmail_id=?", (msg_id,))
            if c.fetchone():
                continue
            
            msg = self.fetch_message_full(msg_id)
            if not msg:
                continue
                
            # Forensic extraction logic here...
            self.save_forensic_artifact(msg)
            
            c.execute("INSERT INTO processed_messages (gmail_id, thread_id, processed_at, status) VALUES (?, ?, ?, ?)",
                      (msg_id, msg['threadId'], datetime.now(timezone.utc).isoformat(), 'completed'))
            conn.commit()
            exported_count += 1
            
        conn.close()
        self.log.info(f"Exported {exported_count} new messages.")

    def save_forensic_artifact(self, msg):
        # Simplified for now: save JSON metadata
        msg_id = msg['id']
        path = os.path.join(self.export_dir, 'bodies', f"{msg_id}.meta.json")
        with open(path, 'w') as f:
            json.dump(msg, f, indent=2)
        
        # Add to manifest
        self.add_to_manifest(path)

    def add_to_manifest(self, file_path):
        sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256.update(chunk)
        
        self.manifest['file_manifest'].append({
            "filename": os.path.relpath(file_path, self.export_dir),
            "sha256": sha256.hexdigest(),
            "size_bytes": os.path.getsize(file_path)
        })

    def finalize(self):
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

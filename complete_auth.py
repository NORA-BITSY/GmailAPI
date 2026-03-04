import json
import yaml
import sys
from google_auth_oauthlib.flow import InstalledAppFlow

def complete():
    if len(sys.argv) < 2:
        print("Usage: python complete_auth.py <code>")
        return

    code = sys.argv[1]
    
    # Extract code if full URL was provided
    if 'code=' in code:
        from urllib.parse import urlparse, parse_qs
        query = urlparse(code).query
        params = parse_qs(query)
        if 'code' in params:
            code = params['code'][0]

    with open('config.yml', 'r') as f:
        config = yaml.safe_load(f)
    
    with open('flow_state.json', 'r') as f:
        state = json.load(f)

    creds_path = config['gmail']['credentials_path']
    token_path = config['gmail']['token_path']
    scopes = config['gmail']['scopes']

    flow = InstalledAppFlow.from_client_secrets_file(
        creds_path,
        scopes=scopes,
        redirect_uri=state['redirect_uri']
    )
    flow.code_verifier = state['verifier']

    try:
        flow.fetch_token(code=code)
        creds = flow.credentials
        
        with open(token_path, 'w') as token:
            token.write(creds.to_json())
        print(f"Token successfully saved to {token_path}")
    except Exception as e:
        print(f"Error exchanging code: {e}")

if __name__ == "__main__":
    complete()

import yaml
import json
from google_auth_oauthlib.flow import InstalledAppFlow

# Load config to get paths
with open('config.yml', 'r') as f:
    config = yaml.safe_load(f)

creds_path = config['gmail']['credentials_path']
scopes = config['gmail']['scopes']

# Use the same redirect URI as before
redirect_uri = 'http://localhost:41595/'

flow = InstalledAppFlow.from_client_secrets_file(
    creds_path,
    scopes=scopes,
    redirect_uri=redirect_uri
)

auth_url, _ = flow.authorization_url(prompt='consent', access_type='offline')

with open('auth_url.txt', 'w') as f:
    f.write(auth_url)

# Save the code_verifier to resume the flow later
with open('flow_state.json', 'w') as f:
    json.dump({'verifier': flow.code_verifier, 'redirect_uri': redirect_uri}, f)

print(f"Authorization URL has been written to auth_url.txt")
print(f"Please visit the URL, authorize the app, and then provide the 'code' from the redirect URL.")

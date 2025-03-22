import json
import sys
from datetime import datetime, timedelta

import requests
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

# Expected input schema
# {"sp": "/servicePrincipals/<id>", "kv_name": "name", "kv_secret_name": "name",  "app_name": "name", "rotation_days": 30}

args = json.loads(sys.argv[1])

GRAPH_API_URL = f"https://graph.microsoft.com/v1.0/{args['sp']}/addPassword"

# Authenticate to Azure
credential = DefaultAzureCredential()
token = credential.get_token("https://graph.microsoft.com/.default").token
secret_client = SecretClient(vault_url=f"https://{args['kv_name']}.vault.azure.net/", credential=credential)

# Generate new secret
payload = {
    "passwordCredential": {
        "displayName": f"{args['app_name']}-secret",
        "endDateTime": (datetime.utcnow() + timedelta(days=args["rotation_days"])).isoformat() + "Z",
    }
}
headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
response = requests.post(GRAPH_API_URL, headers=headers, json=payload)

# Store in Key Vault
if response.status_code == 200:
    new_secret = response.json()["secretText"]
    secret = secret_client.set_secret(
        args["kv_secret_name"], new_secret, content_type=f"Secret of {args['app_name']} application"
    )
    print("✅ New secret value stored in Azure Key Vault.")
else:
    print(f"❌ Error: {response.status_code}, {response.text}")

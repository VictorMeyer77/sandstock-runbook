from datetime import datetime, timedelta

import requests
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

ENV = "dev"
SERVICE_PRINCIPAL_ID = "2798ab7b-7cc5-4844-8f0d-33e85c996ca3"
ROTATION_DAYS = 30

GRAPH_API_URL = f"https://graph.microsoft.com/v1.0/servicePrincipals/{SERVICE_PRINCIPAL_ID}/addPassword"

# Authenticate to Azure
credential = DefaultAzureCredential()
token = credential.get_token("https://graph.microsoft.com/.default").token
secret_client = SecretClient(vault_url=f"https://{ENV}-sandstock-kv.vault.azure.net/", credential=credential)

# Generate new secret
payload = {
    "passwordCredential": {
        "displayName": f"{ENV}-sandstock-dbk-app-secret",
        "endDateTime": (datetime.utcnow() + timedelta(days=ROTATION_DAYS)).isoformat() + "Z",
    }
}
headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
response = requests.post(GRAPH_API_URL, headers=headers, json=payload)

# Store in Key Vault
if response.status_code == 200:
    new_secret = response.json()["secretText"]
    secret = secret_client.set_secret(
        "dev-sandstock-dbk-app-secret", new_secret, content_type=f"Secret of {ENV}-sandstock-dbk-app application"
    )
    print("✅ New secret value stored in Azure Key Vault.")
else:
    print(f"❌ Error: {response.status_code}, {response.text}")

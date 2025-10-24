from __future__ import annotations

from typing import Optional
from azure.keyvault.secrets import SecretClient
from .managed_identity import get_default_credential


def get_secret(vault_uri: str, name: str, *, version: Optional[str] = None) -> Optional[str]:
    """Fetch a secret value from Azure Key Vault using Managed Identity/AAD.

    Returns None if the secret cannot be fetched (e.g., not found or access denied).
    """
    cred = get_default_credential()
    client = SecretClient(vault_url=vault_uri, credential=cred)
    try:
        if version:
            sec = client.get_secret(name, version=version)
        else:
            sec = client.get_secret(name)
        return sec.value
    except Exception:
        return None

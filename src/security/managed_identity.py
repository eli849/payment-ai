from __future__ import annotations

import logging
from typing import Optional

from azure.identity import DefaultAzureCredential

logger = logging.getLogger(__name__)


def get_default_credential(authority_host: Optional[str] = None) -> DefaultAzureCredential:
    """
    Returns a DefaultAzureCredential configured for server and local dev.

    - Uses Managed Identity in Azure
    - Falls back to Azure CLI / Visual Studio Code signed-in account locally
    - Avoids environment credentials unless explicitly configured
    """
    # In highly locked-down environments, you may want to set exclude_* flags.
    # We keep defaults but log the resolved chain for visibility.
    credential = DefaultAzureCredential(authority=authority_host)
    logger.debug("Initialized DefaultAzureCredential with authority=%s", authority_host)
    return credential

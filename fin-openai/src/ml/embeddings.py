from __future__ import annotations

import os
from typing import List

from openai import OpenAI

from ..config import get_settings
from ..security.key_vault import get_secret


def _get_openai_client_for_embeddings() -> OpenAI:
    settings = get_settings()
    if not (
        settings.azure_openai_endpoint
        and settings.azure_openai_embeddings_deployment
        and settings.key_vault_uri
        and settings.azure_openai_api_key_secret_name
    ):
        raise RuntimeError(
            "Embeddings not configured. Set AZURE_OPENAI_ENDPOINT, "
            "AZURE_OPENAI_EMBEDDINGS_DEPLOYMENT, KEY_VAULT_URI, and "
            "AZURE_OPENAI_API_KEY_SECRET_NAME."
        )

    api_key = get_secret(settings.key_vault_uri, settings.azure_openai_api_key_secret_name)
    if not api_key:
        raise RuntimeError("Failed to retrieve Azure OpenAI API key from Key Vault")

    base_url = (
        f"{settings.azure_openai_endpoint}/openai/deployments/"
        f"{settings.azure_openai_embeddings_deployment}"
    )
    api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-06-01")
    return OpenAI(base_url=base_url, api_key=api_key, default_headers={"api-version": api_version})


def embed_texts(texts: List[str]) -> List[List[float]]:
    """Return embeddings for a list of texts using the configured Azure OpenAI deployment.

    Notes:
    - For text-embedding-3-large the vector length is 3072.
    - Input size/throughput limits depend on your deployment SKU/region.
    """
    client = _get_openai_client_for_embeddings()
    settings = get_settings()
    # The SDK requires model param; for Azure, pass the deployment name
    model = settings.azure_openai_embeddings_deployment  # type: ignore[arg-type]
    resp = client.embeddings.create(model=model, input=texts)
    return [d.embedding for d in resp.data]

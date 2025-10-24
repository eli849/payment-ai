from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential  # type: ignore
from azure.core.credentials import TokenCredential

from ..config import get_settings
from ..security.managed_identity import get_default_credential

logger = logging.getLogger(__name__)


class AzureSearch:
    """Thin wrapper around Azure AI Search for query operations using AAD tokens.

    For production, prefer RBAC with Managed Identity on the Search service.
    """

    def __init__(
        self,
        credential: Optional[TokenCredential] = None,
        service_name: Optional[str] = None,
        index_name: Optional[str] = None,
    ) -> None:
        settings = get_settings()
        self._service = service_name or settings.azure_search_service
        self._index = index_name or settings.azure_search_index

        if not self._service or not self._index:
            raise ValueError("Azure Search service/index are not configured")

        endpoint = f"https://{self._service}.search.windows.net"

        # Prefer AAD via DefaultAzureCredential
        cred = credential or get_default_credential()
        self.client = SearchClient(
            endpoint=endpoint,
            index_name=self._index,
            credential=cred,
        )
        logger.info("AzureSearch initialized for index '%s' at '%s'", self._index, endpoint)

    def query(
        self,
        query_text: str,
        *,
        top: int = 5,
        semantic: bool = False,
        filters: Optional[str] = None,
        select: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        from azure.search.documents.models import QueryType

        logger.debug("Search query: %s", query_text)

        results_iter = self.client.search(
            search_text=query_text,
            top=top,
            include_total_count=False,
            filter=filters,
            select=select,
            query_type=QueryType.SEMANTIC if semantic else QueryType.SIMPLE,
        )
        results: List[Dict[str, Any]] = []
        for r in results_iter:
            results.append(dict(r))
        return results

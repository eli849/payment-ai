from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential  # type: ignore
from azure.core.credentials import TokenCredential

from ..config import get_settings
from ..security.managed_identity import get_default_credential
from ..ml.embeddings import embed_texts

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

    def vector_query(
        self,
        query_text: str,
        *,
        top: int = 5,
        vector_field: str = "contentVector",
        filters: Optional[str] = None,
        select: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """Vector similarity search using pre-computed embeddings stored in the index.

        Requires the index to have a vector field (e.g., 'contentVector') and vector search profile.
        """
        from azure.search.documents.models import VectorizedQuery

        vec = embed_texts([query_text])[0]
        vq = VectorizedQuery(vector=vec, k_nearest_neighbors=top, fields=vector_field)

        results_iter = self.client.search(
            search_text=None,
            vector_queries=[vq],
            top=top,
            include_total_count=False,
            filter=filters,
            select=select,
        )
        results: List[Dict[str, Any]] = []
        for r in results_iter:
            results.append(dict(r))
        return results

    def hybrid_query(
        self,
        query_text: str,
        *,
        top: int = 5,
        vector_field: str = "contentVector",
        filters: Optional[str] = None,
        select: Optional[List[str]] = None,
        semantic: bool = False,
    ) -> List[Dict[str, Any]]:
        """Hybrid search: combines keyword/semantic search with vector similarity.

        Set semantic=True to use the service's semantic ranking on the text query part.
        """
        from azure.search.documents.models import QueryType, VectorizedQuery

        vec = embed_texts([query_text])[0]
        vq = VectorizedQuery(vector=vec, k_nearest_neighbors=top, fields=vector_field)

        results_iter = self.client.search(
            search_text=query_text,
            vector_queries=[vq],
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

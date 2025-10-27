from __future__ import annotations

import csv
import os
from typing import List, Dict, Any

from azure.identity import DefaultAzureCredential
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    SearchIndex,
    SimpleField,
    SearchableField,
    SearchField,
    SearchFieldDataType,
    VectorSearch,
    HnswVectorSearchAlgorithmConfiguration,
    VectorSearchProfile,
    edm,
)
from azure.search.documents import SearchClient


def get_service_endpoint() -> str:
    service = os.getenv("AZURE_SEARCH_SERVICE")
    if not service:
        raise ValueError("AZURE_SEARCH_SERVICE env var is required")
    return f"https://{service}.search.windows.net"


def ensure_index(index_name: str, *, vector_dim: int = 3072, vector_field: str = "contentVector") -> None:
    endpoint = get_service_endpoint()
    cred = DefaultAzureCredential()
    ic = SearchIndexClient(endpoint=endpoint, credential=cred)

    # id as key; other fields typical for payments demo
    fields = [
        SimpleField(name="transaction_id", type=edm.String, key=True, filterable=True, sortable=True),
        SimpleField(name="amount", type=edm.Double, filterable=True, sortable=True),
        SimpleField(name="currency", type=edm.String, filterable=True, sortable=True, facetable=True),
        SimpleField(name="status", type=edm.String, filterable=True, sortable=True, facetable=True),
        SimpleField(name="merchant_id", type=edm.String, filterable=True, sortable=True),
        SimpleField(name="created_utc", type=edm.DateTimeOffset, filterable=True, sortable=True),
        # Add a combined text field if you want full-text search
        SearchableField(name="content", type=edm.String, analyzer_name="en.lucene"),
        # Vector field for embeddings (e.g., text-embedding-3-large => 3072 dims)
        SearchField(
            name=vector_field,
            type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
            vector_search_dimensions=vector_dim,
            vector_search_profile_name="vector-profile",
        ),
    ]

    vector_search = VectorSearch(
        algorithms=[HnswVectorSearchAlgorithmConfiguration(name="hnsw-config")],
        profiles=[VectorSearchProfile(name="vector-profile", algorithm_configuration_name="hnsw-config")],
    )

    index = SearchIndex(name=index_name, fields=fields, vector_search=vector_search)

    try:
        # If exists, no-op
        ic.get_index(index_name)
    except Exception:
        ic.create_index(index)


def load_csv(path: str) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    with open(path, newline="", encoding="utf-8") as f:
        r = csv.DictReader(f)
        for row in r:
            # Map to index schema; add a concatenated content field for search
            content = (
                f"txn {row['transaction_id']} amount {row['amount']} {row['currency']} "
                f"status {row['status']} merchant {row['merchant_id']}"
            )
            rows.append({
                "transaction_id": row["transaction_id"],
                "amount": float(row["amount"]),
                "currency": row["currency"],
                "status": row["status"],
                "merchant_id": row["merchant_id"],
                "created_utc": row["created_utc"],
                "content": content,
            })
    return rows


def upload_docs(index_name: str, docs: List[Dict[str, Any]]) -> int:
    endpoint = get_service_endpoint()
    cred = DefaultAzureCredential()
    sc = SearchClient(endpoint=endpoint, index_name=index_name, credential=cred)
    # upload in batches; SDK handles chunking reasonably
    res = sc.upload_documents(docs)
    # count successes
    return sum(1 for r in res if r.succeeded)


from src.ml.embeddings import embed_texts


def main() -> None:
    index = os.getenv("AZURE_SEARCH_INDEX", "transactions")
    csv_path = os.getenv("CSV_PATH", os.path.join("data", "payments", "sample_transactions.csv"))
    vector_field = os.getenv("VECTOR_FIELD", "contentVector")
    vector_dim = int(os.getenv("VECTOR_DIM", "3072"))

    ensure_index(index, vector_dim=vector_dim, vector_field=vector_field)
    docs = load_csv(csv_path)

    # Compute embeddings for docs' content in small batches (optional if configured)
    try:
        batch_size = 32
        all_embeddings: List[List[float]] = []
        contents = [d["content"] for d in docs]
        for i in range(0, len(contents), batch_size):
            batch = contents[i : i + batch_size]
            embs = embed_texts(batch)
            all_embeddings.extend(embs)

        for d, vec in zip(docs, all_embeddings):
            d[vector_field] = vec
        print(f"Computed embeddings for {len(all_embeddings)} documents")
    except Exception as e:
        print(
            "Embeddings generation skipped (configuration missing or error). "
            f"Proceeding without vectors. Details: {e}"
        )

    succeeded = upload_docs(index, docs)
    print(f"Uploaded {succeeded}/{len(docs)} documents to index '{index}' (vector field: {vector_field})")


if __name__ == "__main__":
    main()

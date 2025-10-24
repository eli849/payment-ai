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
    edm,
)
from azure.search.documents import SearchClient


def get_service_endpoint() -> str:
    service = os.getenv("AZURE_SEARCH_SERVICE")
    if not service:
        raise ValueError("AZURE_SEARCH_SERVICE env var is required")
    return f"https://{service}.search.windows.net"


def ensure_index(index_name: str) -> None:
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
    ]

    index = SearchIndex(name=index_name, fields=fields)

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


def main() -> None:
    index = os.getenv("AZURE_SEARCH_INDEX", "transactions")
    csv_path = os.getenv("CSV_PATH", os.path.join("data", "payments", "sample_transactions.csv"))

    ensure_index(index)
    docs = load_csv(csv_path)
    succeeded = upload_docs(index, docs)
    print(f"Uploaded {succeeded}/{len(docs)} documents to index '{index}'")


if __name__ == "__main__":
    main()

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class Transaction:
    id: str
    amount: float
    currency: str
    status: str  # authorized | captured | settled | refunded | chargeback


def calculate_fees(amount: float, rate: float = 0.029, fixed: float = 0.30) -> float:
    """Calculate processing fees using a typical blended model."""
    return round(amount * rate + fixed, 2)


def can_refund(status: str) -> bool:
    return status in {"captured", "settled"}

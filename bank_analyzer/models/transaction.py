"""Transaction model for normalized bank transactions."""

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Optional
import hashlib


@dataclass
class Transaction:
    """
    Normalized bank transaction.

    This class represents a single bank transaction in a normalized format,
    regardless of the source bank's CSV format.
    """

    # Core data
    date: datetime
    description: str
    amount: Decimal

    # Classification
    transaction_type: str  # 'expense' or 'income'
    currency: str = "PLN"
    counterparty: str = ""

    # Source metadata
    source_bank: str = ""
    source_file: str = ""
    processed_at: datetime = field(default_factory=datetime.now)

    # Categorization
    category_main: Optional[str] = None
    category_sub: Optional[str] = None
    manual_override: bool = False

    # Unique identifier (generated automatically)
    id: str = field(default="", init=True)

    def __post_init__(self):
        """Generate ID based on transaction data if not provided."""
        if not self.id:
            hash_input = f"{self.date.isoformat()}{self.description}{self.amount}"
            self.id = hashlib.sha256(hash_input.encode()).hexdigest()[:16]

        # Ensure amount is Decimal
        if not isinstance(self.amount, Decimal):
            self.amount = Decimal(str(self.amount))

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            'id': self.id,
            'date': self.date.isoformat(),
            'description': self.description,
            'counterparty': self.counterparty,
            'amount': float(self.amount),
            'transaction_type': self.transaction_type,
            'currency': self.currency,
            'category_main': self.category_main,
            'category_sub': self.category_sub,
            'source_bank': self.source_bank,
            'source_file': self.source_file,
            'manual_override': self.manual_override,
            'processed_at': self.processed_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Transaction':
        """Create Transaction from dictionary."""
        data = data.copy()
        data['date'] = datetime.fromisoformat(data['date'])
        data['amount'] = Decimal(str(data['amount']))
        if 'processed_at' in data:
            data['processed_at'] = datetime.fromisoformat(data['processed_at'])
        # Remove id from data to avoid double initialization
        trans_id = data.pop('id', None)
        trans = cls(**data)
        if trans_id:
            trans.id = trans_id
        return trans

    def __str__(self) -> str:
        """Human-readable string representation."""
        return (
            f"{self.date.strftime('%Y-%m-%d')} | "
            f"{self.counterparty[:20]:<20} | "
            f"{float(self.amount):>10.2f} {self.currency} | "
            f"{self.category_main or 'N/A'}"
        )

    def __repr__(self) -> str:
        return (
            f"Transaction(id={self.id!r}, date={self.date.date()}, "
            f"amount={self.amount}, counterparty={self.counterparty!r})"
        )

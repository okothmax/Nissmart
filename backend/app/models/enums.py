"""Domain enumerations used across the ledger system."""

from enum import Enum


class Currency(str, Enum):
    KES = "KES"
    USD = "USD"
    EUR = "EUR"


class AccountType(str, Enum):
    USER = "user"
    TREASURY = "treasury"
    ESCROW = "escrow"
    EXTERNAL = "external"


class AccountStatus(str, Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    CLOSED = "closed"


class TransactionType(str, Enum):
    DEPOSIT = "deposit"
    TRANSFER = "transfer"
    WITHDRAWAL = "withdrawal"


class TransactionStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"


class RequestStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class LedgerEntryDirection(str, Enum):
    DEBIT = "debit"
    CREDIT = "credit"

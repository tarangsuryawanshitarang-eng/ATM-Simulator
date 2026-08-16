"""
Domain-specific custom exceptions for the Advanced ATM Simulator.
Provides structured error handling for security, vault, and transaction operations.
"""


class AtmBaseException(Exception):
    """Base class for all domain-specific ATM exceptions."""
    def __init__(self, message: str, failure_reason: str = "SYSTEM_ERROR"):
        super().__init__(message)
        self.message = message
        self.failure_reason = failure_reason


class AuthenticationFailedException(AtmBaseException):
    """Raised when user enters an incorrect PIN."""
    def __init__(self, message: str = "Invalid PIN entered.", remaining_attempts: int = 0):
        super().__init__(message, failure_reason="INVALID_PIN")
        self.remaining_attempts = remaining_attempts


class AccountLockedException(AtmBaseException):
    """Raised when an account is locked due to excessive failed attempts."""
    def __init__(self, message: str = "Account is locked. Please contact customer support."):
        super().__init__(message, failure_reason="ACCOUNT_LOCKED")


class AccountNotFoundException(AtmBaseException):
    """Raised when the specified account number does not exist."""
    def __init__(self, message: str = "Account number not found."):
        super().__init__(message, failure_reason="ACCOUNT_NOT_FOUND")


class InsufficientFundsException(AtmBaseException):
    """Raised when account balance is lower than the requested withdrawal amount."""
    def __init__(self, message: str = "Insufficient account balance."):
        super().__init__(message, failure_reason="INSUFFICIENT_FUNDS")


class AtmCashExhaustedException(AtmBaseException):
    """Raised when the ATM vault cannot satisfy the withdrawal amount due to lack of notes."""
    def __init__(self, message: str = "ATM does not have sufficient physical cash to fulfill request."):
        super().__init__(message, failure_reason="ATM_CASH_EXHAUSTED")


class UnsupportedDenominationException(AtmBaseException):
    """Raised when the requested amount cannot be composed using available cassette denominations."""
    def __init__(self, message: str = "Requested amount cannot be dispensed with available denominations."):
        super().__init__(message, failure_reason="UNSUPPORTED_DENOMINATION")


class InvalidAmountException(AtmBaseException):
    """Raised when an invalid transaction amount is supplied (e.g. non-positive or non-numeric)."""
    def __init__(self, message: str = "Transaction amount must be a positive number."):
        super().__init__(message, failure_reason="INVALID_AMOUNT")


class DatabaseTransactionError(AtmBaseException):
    """Raised when a database transaction fails or encounters integrity conflicts."""
    def __init__(self, message: str = "Database transaction failed."):
        super().__init__(message, failure_reason="DATABASE_ERROR")

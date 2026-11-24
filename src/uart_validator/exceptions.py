"""Custom exception hierarchy for UART protocol errors."""


class ProtocolError(Exception):
    """Base exception for all UART protocol errors."""


class FramingError(ProtocolError):
    """Raised when frame structure is invalid (bad SOF, EOF, or length mismatch)."""


class CRCMismatchError(ProtocolError):
    """Raised when the CRC integrity check fails."""


class PayloadLengthError(ProtocolError):
    """Raised when the payload length exceeds the allowed maximum."""


class TransportTimeoutError(ProtocolError):
    """Raised when a transport read operation times out."""


class TelemetryRangeError(ProtocolError):
    """Raised when a telemetry value is outside the permitted operating range."""

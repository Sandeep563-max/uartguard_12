"""Protocol constants, message IDs, and sensor operating limits."""

from enum import IntEnum

SOF_BYTE = 0xAA
EOF_BYTE = 0x55
MAX_PAYLOAD_LEN = 64

DEFAULT_BAUDRATE = 115200
DEFAULT_TIMEOUT = 0.5


class MessageID(IntEnum):
    """Defined message types for the UART protocol."""
    HEARTBEAT = 0x01
    TELEMETRY = 0x02
    CONFIG_ACK = 0x03
    ERROR_REPORT = 0xFF


# Sensor operating limits
TEMP_MIN_C = -40.0
TEMP_MAX_C = 125.0
VOLTAGE_MIN_V = 0.0
VOLTAGE_MAX_V = 24.0
CURRENT_MIN_MA = 0.0
CURRENT_MAX_MA = 5000.0

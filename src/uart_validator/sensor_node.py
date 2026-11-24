"""Telemetry reading encoding, decoding, and limit validation.

Payload struct format: '>fffB' (13 bytes total)
    temperature_c  : float  (4 bytes)
    voltage_v      : float  (4 bytes)
    current_ma     : float  (4 bytes)
    status_flags   : uint8  (1 byte)
"""

from __future__ import annotations

import struct
from dataclasses import dataclass

from .config import (
    TEMP_MIN_C, TEMP_MAX_C,
    VOLTAGE_MIN_V, VOLTAGE_MAX_V,
    CURRENT_MIN_MA, CURRENT_MAX_MA,
)
from .exceptions import TelemetryRangeError

TELEMETRY_FORMAT = ">fffB"
TELEMETRY_SIZE = 13


@dataclass
class TelemetryReading:
    """A single telemetry sample from a sensor node."""
    temperature_c: float
    voltage_v: float
    current_ma: float
    status_flags: int


def encode_telemetry(reading: TelemetryReading) -> bytes:
    """Pack a TelemetryReading into a 13-byte payload."""
    return struct.pack(
        TELEMETRY_FORMAT,
        reading.temperature_c,
        reading.voltage_v,
        reading.current_ma,
        reading.status_flags,
    )


def decode_telemetry(payload: bytes) -> TelemetryReading:
    """Unpack a 13-byte payload into a TelemetryReading."""
    if len(payload) != TELEMETRY_SIZE:
        raise ValueError(
            f"Telemetry payload must be {TELEMETRY_SIZE} bytes, got {len(payload)}"
        )
    temp, voltage, current, flags = struct.unpack(TELEMETRY_FORMAT, payload)
    return TelemetryReading(
        temperature_c=temp,
        voltage_v=voltage,
        current_ma=current,
        status_flags=flags,
    )


def validate_telemetry_limits(reading: TelemetryReading) -> None:
    """Raise TelemetryRangeError if any sensor value is outside the permitted range."""
    if not (TEMP_MIN_C <= reading.temperature_c <= TEMP_MAX_C):
        raise TelemetryRangeError(
            f"Temperature {reading.temperature_c} C outside [{TEMP_MIN_C}, {TEMP_MAX_C}]"
        )
    if not (VOLTAGE_MIN_V <= reading.voltage_v <= VOLTAGE_MAX_V):
        raise TelemetryRangeError(
            f"Voltage {reading.voltage_v} V outside [{VOLTAGE_MIN_V}, {VOLTAGE_MAX_V}]"
        )
    if not (CURRENT_MIN_MA <= reading.current_ma <= CURRENT_MAX_MA):
        raise TelemetryRangeError(
            f"Current {reading.current_ma} mA outside [{CURRENT_MIN_MA}, {CURRENT_MAX_MA}]"
        )

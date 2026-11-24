"""Boundary value analysis tests for payload sizes and sensor limits."""

import pytest

from uart_validator.config import (
    MAX_PAYLOAD_LEN, MessageID,
    TEMP_MIN_C, TEMP_MAX_C,
    VOLTAGE_MIN_V, VOLTAGE_MAX_V,
    CURRENT_MIN_MA, CURRENT_MAX_MA,
)
from uart_validator.protocol import Packet, encode_packet, decode_packet
from uart_validator.sensor_node import TelemetryReading, validate_telemetry_limits
from uart_validator.exceptions import PayloadLengthError, TelemetryRangeError


@pytest.mark.boundary
def test_empty_payload():
    """A zero-length payload encodes and decodes correctly."""
    pkt = Packet(msg_id=MessageID.HEARTBEAT, payload=b"")
    decoded = decode_packet(encode_packet(pkt))
    assert decoded.payload == b""


@pytest.mark.boundary
def test_one_byte_payload():
    """A single-byte payload encodes and decodes correctly."""
    pkt = Packet(msg_id=MessageID.HEARTBEAT, payload=b"\xFF")
    decoded = decode_packet(encode_packet(pkt))
    assert decoded.payload == b"\xFF"


@pytest.mark.boundary
def test_max_payload_64_bytes():
    """The maximum 64-byte payload encodes and decodes correctly."""
    payload = bytes(range(64))
    pkt = Packet(msg_id=MessageID.TELEMETRY, payload=payload)
    decoded = decode_packet(encode_packet(pkt))
    assert decoded.payload == payload
    assert len(decoded.payload) == MAX_PAYLOAD_LEN


@pytest.mark.boundary
@pytest.mark.negative
def test_oversized_payload_65_bytes():
    """A 65-byte payload is rejected by encode_packet."""
    pkt = Packet(msg_id=MessageID.TELEMETRY, payload=bytes(65))
    with pytest.raises(PayloadLengthError):
        encode_packet(pkt)


@pytest.mark.boundary
@pytest.mark.parametrize("temp,voltage,current", [
    (TEMP_MIN_C, 12.0, 500.0),
    (TEMP_MAX_C, 12.0, 500.0),
    (25.0, VOLTAGE_MIN_V, 500.0),
    (25.0, VOLTAGE_MAX_V, 500.0),
    (25.0, 12.0, CURRENT_MIN_MA),
    (25.0, 12.0, CURRENT_MAX_MA),
])
def test_valid_boundary_values(temp, voltage, current):
    """Exact min/max sensor values pass validation."""
    reading = TelemetryReading(
        temperature_c=temp, voltage_v=voltage, current_ma=current, status_flags=0,
    )
    validate_telemetry_limits(reading)


@pytest.mark.boundary
@pytest.mark.negative
@pytest.mark.parametrize("temp,voltage,current", [
    (TEMP_MIN_C - 0.1, 12.0, 500.0),
    (TEMP_MAX_C + 0.1, 12.0, 500.0),
    (25.0, VOLTAGE_MIN_V - 0.1, 500.0),
    (25.0, VOLTAGE_MAX_V + 0.1, 500.0),
    (25.0, 12.0, CURRENT_MIN_MA - 0.1),
    (25.0, 12.0, CURRENT_MAX_MA + 0.1),
])
def test_values_outside_limits(temp, voltage, current):
    """Values just outside the permitted range raise TelemetryRangeError."""
    reading = TelemetryReading(
        temperature_c=temp, voltage_v=voltage, current_ma=current, status_flags=0,
    )
    with pytest.raises(TelemetryRangeError):
        validate_telemetry_limits(reading)


@pytest.mark.boundary
@pytest.mark.negative
@pytest.mark.parametrize("bad_msg_id", [-1, 256, 1000])
def test_invalid_message_ids(bad_msg_id):
    """Message IDs outside 0-255 are rejected with ProtocolError."""
    from uart_validator.exceptions import ProtocolError
    pkt = Packet(msg_id=bad_msg_id, payload=b"")
    with pytest.raises(ProtocolError):
        encode_packet(pkt)


@pytest.mark.boundary
@pytest.mark.negative
def test_invalid_telemetry_payload_size():
    """decode_telemetry rejects payloads that are not exactly 13 bytes."""
    from uart_validator.sensor_node import decode_telemetry
    with pytest.raises(ValueError):
        decode_telemetry(b"\x00" * 12)
    with pytest.raises(ValueError):
        decode_telemetry(b"\x00" * 14)


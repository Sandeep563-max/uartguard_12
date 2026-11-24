"""Smoke tests -- quick sanity checks for core functionality."""

import pytest

from uart_validator.crc import calculate_crc16
from uart_validator.config import MessageID
from uart_validator.protocol import Packet, encode_packet, decode_packet
from uart_validator.sensor_node import (
    TelemetryReading, encode_telemetry, decode_telemetry,
)
from uart_validator.transport import SerialLoopbackTransport


@pytest.mark.smoke
def test_crc_known_vector():
    """CRC-16/CCITT-FALSE of '123456789' must equal 0x29B1."""
    assert calculate_crc16(b"123456789") == 0x29B1


@pytest.mark.smoke
def test_heartbeat_encode_decode():
    """Round-trip a heartbeat packet through encode and decode."""
    pkt = Packet(msg_id=MessageID.HEARTBEAT, payload=b"\x01")
    frame = encode_packet(pkt)
    decoded = decode_packet(frame)
    assert decoded.msg_id == MessageID.HEARTBEAT
    assert decoded.payload == b"\x01"


@pytest.mark.smoke
def test_telemetry_encode_decode():
    """Round-trip a telemetry reading through struct pack/unpack."""
    reading = TelemetryReading(
        temperature_c=25.0, voltage_v=12.0, current_ma=500.0, status_flags=0x00,
    )
    payload = encode_telemetry(reading)
    decoded = decode_telemetry(payload)
    assert decoded.temperature_c == pytest.approx(25.0)
    assert decoded.voltage_v == pytest.approx(12.0)
    assert decoded.current_ma == pytest.approx(500.0)
    assert decoded.status_flags == 0x00


@pytest.mark.smoke
def test_loopback_open_close():
    """Verify the loopback transport opens and closes correctly."""
    transport = SerialLoopbackTransport(timeout=0.1)
    with transport as t:
        assert t._port is not None
        assert t._port.is_open
    assert not t._port.is_open

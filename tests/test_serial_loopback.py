"""Integration tests using the pyserial virtual loopback transport."""

import pytest

from uart_validator.config import MessageID
from uart_validator.protocol import Packet, encode_packet
from uart_validator.sensor_node import (
    TelemetryReading, encode_telemetry, decode_telemetry,
)
from uart_validator.exceptions import TransportTimeoutError


@pytest.mark.integration
def test_single_packet_loopback(loopback_transport):
    """Send and receive a single packet over the loopback."""
    pkt = Packet(msg_id=MessageID.HEARTBEAT, payload=b"\x01")
    loopback_transport.send_packet(pkt)
    received = loopback_transport.receive_packet()
    assert received.msg_id == pkt.msg_id
    assert received.payload == pkt.payload


@pytest.mark.integration
def test_multiple_back_to_back_packets(loopback_transport):
    """Send three packets back-to-back, then receive all three in order."""
    packets = [
        Packet(msg_id=MessageID.HEARTBEAT, payload=b"\x01"),
        Packet(msg_id=MessageID.TELEMETRY, payload=b"\x02\x03"),
        Packet(msg_id=MessageID.CONFIG_ACK, payload=b"\x04\x05\x06"),
    ]
    for pkt in packets:
        loopback_transport.send_packet(pkt)
    for pkt in packets:
        received = loopback_transport.receive_packet()
        assert received.msg_id == pkt.msg_id
        assert received.payload == pkt.payload


@pytest.mark.integration
def test_telemetry_packet_loopback(loopback_transport):
    """Send a telemetry payload over the loopback and verify decoded values."""
    reading = TelemetryReading(
        temperature_c=36.6, voltage_v=5.0, current_ma=250.0, status_flags=0x0F,
    )
    payload = encode_telemetry(reading)
    pkt = Packet(msg_id=MessageID.TELEMETRY, payload=payload)
    loopback_transport.send_packet(pkt)
    received = loopback_transport.receive_packet()
    decoded = decode_telemetry(received.payload)
    assert decoded.temperature_c == pytest.approx(36.6)
    assert decoded.voltage_v == pytest.approx(5.0)
    assert decoded.current_ma == pytest.approx(250.0)
    assert decoded.status_flags == 0x0F


@pytest.mark.integration
@pytest.mark.negative
def test_corrupted_packet_handling(loopback_transport):
    """A packet with corrupted CRC cannot be decoded; transport times out."""
    pkt = Packet(msg_id=MessageID.HEARTBEAT, payload=b"\x01")
    frame = encode_packet(pkt)
    corrupted = bytearray(frame)
    corrupted[-3] ^= 0xFF
    loopback_transport.send_bytes(bytes(corrupted))
    with pytest.raises(TransportTimeoutError):
        loopback_transport.receive_packet()


@pytest.mark.integration
@pytest.mark.negative
def test_read_timeout(loopback_transport):
    """Receiving with no data sent raises TransportTimeoutError."""
    with pytest.raises(TransportTimeoutError):
        loopback_transport.receive_packet()


@pytest.mark.integration
def test_correct_packet_decoding(loopback_transport):
    """Verify correct decoding of multiple sequential packets with varying payloads."""
    payloads = [b"\x10\x20\x30", b"\xFF", b""]
    for payload in payloads:
        pkt = Packet(msg_id=MessageID.CONFIG_ACK, payload=payload)
        loopback_transport.send_packet(pkt)
        received = loopback_transport.receive_packet()
        assert received.msg_id == MessageID.CONFIG_ACK
        assert received.payload == payload


@pytest.mark.integration
def test_raw_bytes_transfer(loopback_transport):
    """Verify raw byte transmission and reception using send_bytes and receive_bytes."""
    test_data = b"\xAA\xBB\xCC\xDD"
    written = loopback_transport.send_bytes(test_data)
    assert written == len(test_data)
    read_data = loopback_transport.receive_bytes(len(test_data))
    assert read_data == test_data


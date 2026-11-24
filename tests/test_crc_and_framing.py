"""CRC verification, framing, and stream-parsing tests."""

import pytest

from uart_validator.config import MessageID
from uart_validator.protocol import Packet, encode_packet, decode_packet, StreamParser
from uart_validator.sensor_node import (
    TelemetryReading, encode_telemetry, decode_telemetry,
)


@pytest.mark.functional
@pytest.mark.parametrize("msg_id", list(MessageID))
def test_message_id_encode_decode(msg_id):
    """Encode/decode round-trip for every defined MessageID."""
    pkt = Packet(msg_id=msg_id, payload=b"\xAB")
    decoded = decode_packet(encode_packet(pkt))
    assert decoded.msg_id == msg_id
    assert decoded.payload == b"\xAB"


@pytest.mark.functional
@pytest.mark.parametrize("size", [0, 1, 10, 32, 64])
def test_multiple_payload_sizes(size):
    """Round-trip packets with varying payload sizes."""
    payload = bytes(i % 256 for i in range(size))
    pkt = Packet(msg_id=MessageID.TELEMETRY, payload=payload)
    decoded = decode_packet(encode_packet(pkt))
    assert decoded.msg_id == MessageID.TELEMETRY
    assert decoded.payload == payload


@pytest.mark.functional
def test_encode_decode_roundtrip():
    """Verify payload integrity through a full round-trip."""
    original = Packet(msg_id=MessageID.TELEMETRY, payload=b"\x01\x02\x03\x04\x05")
    decoded = decode_packet(encode_packet(original))
    assert decoded.msg_id == original.msg_id
    assert decoded.payload == original.payload


@pytest.mark.functional
def test_concatenated_packets(stream_parser):
    """StreamParser extracts multiple packets from a single concatenated buffer."""
    packets = [
        Packet(msg_id=MessageID.HEARTBEAT, payload=b"\x01"),
        Packet(msg_id=MessageID.TELEMETRY, payload=b"\x02\x03"),
        Packet(msg_id=MessageID.CONFIG_ACK, payload=b"\x04"),
    ]
    combined = b"".join(encode_packet(p) for p in packets)
    result = stream_parser.feed(combined)
    assert len(result) == 3
    for orig, dec in zip(packets, result):
        assert dec.msg_id == orig.msg_id
        assert dec.payload == orig.payload


@pytest.mark.functional
def test_recovery_after_garbage(stream_parser):
    """StreamParser skips leading noise and still decodes the valid frame."""
    garbage = b"\xDE\xAD\xBE\xEF"
    pkt = Packet(msg_id=MessageID.HEARTBEAT, payload=b"\x42")
    frame = encode_packet(pkt)
    result = stream_parser.feed(garbage + frame)
    assert len(result) == 1
    assert result[0].msg_id == pkt.msg_id
    assert result[0].payload == pkt.payload


@pytest.mark.functional
def test_fragmented_input(stream_parser):
    """StreamParser reassembles a packet delivered one byte at a time."""
    pkt = Packet(msg_id=MessageID.HEARTBEAT, payload=b"\x01\x02\x03")
    frame = encode_packet(pkt)
    result = []
    for byte_val in frame:
        result.extend(stream_parser.feed(bytes([byte_val])))
    assert len(result) == 1
    assert result[0].msg_id == pkt.msg_id
    assert result[0].payload == pkt.payload


@pytest.mark.functional
def test_telemetry_float_precision():
    """Verify float precision through telemetry encode/decode using pytest.approx."""
    reading = TelemetryReading(
        temperature_c=25.5, voltage_v=12.3, current_ma=1500.75, status_flags=0x03,
    )
    decoded = decode_telemetry(encode_telemetry(reading))
    assert decoded.temperature_c == pytest.approx(25.5)
    assert decoded.voltage_v == pytest.approx(12.3)
    assert decoded.current_ma == pytest.approx(1500.75)
    assert decoded.status_flags == 0x03


@pytest.mark.functional
def test_stream_parser_recovery_corrupted_crc(stream_parser):
    """StreamParser skips a corrupted-CRC frame and parses the subsequent valid packet."""
    valid_pkt1 = Packet(msg_id=MessageID.HEARTBEAT, payload=b"\x01")
    frame1 = bytearray(encode_packet(valid_pkt1))
    frame1[-3] ^= 0xFF  # Corrupt CRC

    valid_pkt2 = Packet(msg_id=MessageID.TELEMETRY, payload=b"\x02\x03")
    frame2 = encode_packet(valid_pkt2)

    packets = stream_parser.feed(bytes(frame1) + frame2)
    assert len(packets) == 1
    assert packets[0].msg_id == valid_pkt2.msg_id
    assert packets[0].payload == valid_pkt2.payload


@pytest.mark.functional
def test_stream_parser_recovery_corrupted_eof(stream_parser):
    """StreamParser skips a frame with invalid EOF and parses subsequent valid packet."""
    valid_pkt1 = Packet(msg_id=MessageID.HEARTBEAT, payload=b"\x01")
    frame1 = bytearray(encode_packet(valid_pkt1))
    frame1[-1] = 0x00  # Corrupt EOF

    valid_pkt2 = Packet(msg_id=MessageID.CONFIG_ACK, payload=b"\x99")
    frame2 = encode_packet(valid_pkt2)

    packets = stream_parser.feed(bytes(frame1) + frame2)
    assert len(packets) == 1
    assert packets[0].msg_id == valid_pkt2.msg_id
    assert packets[0].payload == valid_pkt2.payload


@pytest.mark.functional
def test_stream_parser_recovery_oversized_length(stream_parser):
    """StreamParser skips a frame with declared LEN > 64 and recovers."""
    bad_frame = bytes([0xAA, 0x01, 70]) + bytes(70) + bytes([0x00, 0x00, 0x55])
    valid_pkt = Packet(msg_id=MessageID.HEARTBEAT, payload=b"\x42")
    good_frame = encode_packet(valid_pkt)

    packets = stream_parser.feed(bad_frame + good_frame)
    assert len(packets) == 1
    assert packets[0].msg_id == valid_pkt.msg_id
    assert packets[0].payload == valid_pkt.payload


@pytest.mark.functional
def test_stream_parser_noise_followed_by_partial_frame(stream_parser):
    """Feed noise followed by partial frame, then remaining frame."""
    valid_pkt = Packet(msg_id=MessageID.HEARTBEAT, payload=b"\x01")
    frame = encode_packet(valid_pkt)
    # 2 noise bytes + first 4 bytes of frame -> total 6 bytes, then remaining bytes
    packets = stream_parser.feed(b"\xFF\xFE" + frame[:4])
    assert len(packets) == 0
    packets = stream_parser.feed(frame[4:])
    assert len(packets) == 1
    assert packets[0].msg_id == valid_pkt.msg_id
    assert packets[0].payload == valid_pkt.payload



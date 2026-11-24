"""Fault injection tests -- verify that corrupted frames are detected."""

import pytest

from uart_validator.config import MessageID
from uart_validator.protocol import Packet, encode_packet, decode_packet, StreamParser
from uart_validator.exceptions import CRCMismatchError, FramingError, PayloadLengthError


@pytest.mark.fault_injection
def test_bit_flip_header(fault_injector, valid_packet):
    """Flipping a bit in MSG_ID causes a CRC mismatch."""
    frame = encode_packet(valid_packet)
    corrupted = fault_injector.flip_bit(frame, byte_index=1, bit_index=0)
    with pytest.raises(CRCMismatchError):
        decode_packet(corrupted)


@pytest.mark.fault_injection
def test_bit_flip_payload(fault_injector):
    """Flipping a bit in the payload causes a CRC mismatch."""
    pkt = Packet(msg_id=MessageID.HEARTBEAT, payload=b"\x00\x01\x02\x03")
    frame = encode_packet(pkt)
    corrupted = fault_injector.flip_bit(frame, byte_index=3, bit_index=0)
    with pytest.raises(CRCMismatchError):
        decode_packet(corrupted)


@pytest.mark.fault_injection
def test_crc_corruption(fault_injector, valid_packet):
    """Inverting the CRC bytes causes a CRC mismatch."""
    frame = encode_packet(valid_packet)
    corrupted = fault_injector.corrupt_crc(frame)
    with pytest.raises(CRCMismatchError):
        decode_packet(corrupted)


@pytest.mark.fault_injection
def test_sof_corruption(fault_injector, valid_packet):
    """Replacing SOF with 0x00 causes a framing error."""
    frame = encode_packet(valid_packet)
    corrupted = fault_injector.corrupt_sof(frame)
    with pytest.raises(FramingError):
        decode_packet(corrupted)


@pytest.mark.fault_injection
def test_eof_corruption(fault_injector, valid_packet):
    """Replacing EOF with 0xFF causes a framing error."""
    frame = encode_packet(valid_packet)
    corrupted = fault_injector.corrupt_eof(frame)
    with pytest.raises(FramingError):
        decode_packet(corrupted)


@pytest.mark.fault_injection
def test_truncated_frame(fault_injector, valid_packet):
    """A truncated frame is rejected as too short."""
    frame = encode_packet(valid_packet)
    truncated = fault_injector.truncate(frame, keep_bytes=4)
    with pytest.raises(FramingError):
        decode_packet(truncated)


@pytest.mark.fault_injection
@pytest.mark.negative
def test_invalid_length_field(valid_packet):
    """A LEN value exceeding MAX_PAYLOAD_LEN raises PayloadLengthError."""
    frame = encode_packet(valid_packet)
    corrupted = bytearray(frame)
    corrupted[2] = 65
    with pytest.raises(PayloadLengthError):
        decode_packet(bytes(corrupted))


@pytest.mark.fault_injection
@pytest.mark.negative
def test_mismatched_length_field(valid_packet):
    """Changing the LEN field to a different value causes a framing or CRC error."""
    frame = encode_packet(valid_packet)
    corrupted = bytearray(frame)
    corrupted[2] = 0  # Original is 1
    with pytest.raises((FramingError, CRCMismatchError)):
        decode_packet(bytes(corrupted))


@pytest.mark.fault_injection
def test_one_byte_fragmentation(fault_injector, valid_packet):
    """StreamParser reassembles a valid frame delivered one byte at a time."""
    frame = encode_packet(valid_packet)
    chunks = fault_injector.fragment(frame, chunk_size=1)
    parser = StreamParser()
    result = []
    for chunk in chunks:
        result.extend(parser.feed(chunk))
    assert len(result) == 1
    assert result[0].msg_id == valid_packet.msg_id
    assert result[0].payload == valid_packet.payload


@pytest.mark.fault_injection
def test_three_byte_fragmentation(fault_injector, valid_packet):
    """StreamParser reassembles a valid frame delivered in 3-byte chunks."""
    frame = encode_packet(valid_packet)
    chunks = fault_injector.fragment(frame, chunk_size=3)
    parser = StreamParser()
    result = []
    for chunk in chunks:
        result.extend(parser.feed(chunk))
    assert len(result) == 1
    assert result[0].msg_id == valid_packet.msg_id
    assert result[0].payload == valid_packet.payload


@pytest.mark.fault_injection
def test_inject_leading_noise(fault_injector, valid_packet):
    """Prepend noise to a valid frame and verify parser recovery."""
    frame = encode_packet(valid_packet)
    noisy_frame = fault_injector.inject_leading_noise(frame, b"\xDE\xAD\xBE\xEF")
    parser = StreamParser()
    packets = parser.feed(noisy_frame)
    assert len(packets) == 1
    assert packets[0].msg_id == valid_packet.msg_id
    assert packets[0].payload == valid_packet.payload


@pytest.mark.fault_injection
@pytest.mark.negative
def test_fault_injector_invalid_indices(fault_injector, valid_packet):
    """FaultInjector validates byte and bit index boundaries."""
    frame = encode_packet(valid_packet)
    with pytest.raises(IndexError):
        fault_injector.flip_bit(frame, byte_index=len(frame), bit_index=0)
    with pytest.raises(IndexError):
        fault_injector.flip_bit(frame, byte_index=-1, bit_index=0)
    with pytest.raises(ValueError):
        fault_injector.flip_bit(frame, byte_index=0, bit_index=-1)
    with pytest.raises(ValueError):
        fault_injector.flip_bit(frame, byte_index=0, bit_index=8)


@pytest.mark.fault_injection
@pytest.mark.negative
def test_fault_injector_invalid_parameters(fault_injector, valid_packet):
    """FaultInjector validates frame length, keep_bytes, and chunk_size."""
    frame = encode_packet(valid_packet)
    with pytest.raises(ValueError):
        fault_injector.corrupt_crc(b"\xAA\x01\x00")
    with pytest.raises(ValueError):
        fault_injector.corrupt_sof(b"")
    with pytest.raises(ValueError):
        fault_injector.corrupt_eof(b"")
    with pytest.raises(ValueError):
        fault_injector.truncate(frame, keep_bytes=-1)
    with pytest.raises(ValueError):
        fault_injector.truncate(frame, keep_bytes=len(frame) + 1)
    with pytest.raises(ValueError):
        fault_injector.fragment(frame, chunk_size=0)
    with pytest.raises(ValueError):
        fault_injector.fragment(frame, chunk_size=-2)


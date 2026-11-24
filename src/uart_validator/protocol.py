"""Binary frame encoding, decoding, and stream parsing.

Frame format:
    [SOF: 1B] [MSG_ID: 1B] [LEN: 1B] [PAYLOAD: 0-64B] [CRC16: 2B BE] [EOF: 1B]

CRC-16 is calculated over MSG_ID + LEN + PAYLOAD.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

from .config import SOF_BYTE, EOF_BYTE, MAX_PAYLOAD_LEN
from .crc import calculate_crc16, verify_crc16
from .exceptions import FramingError, CRCMismatchError, PayloadLengthError, ProtocolError

logger = logging.getLogger(__name__)

FRAME_OVERHEAD = 6  # SOF(1) + MSG_ID(1) + LEN(1) + CRC(2) + EOF(1)


@dataclass
class Packet:
    """A decoded protocol packet containing a message ID and payload."""
    msg_id: int
    payload: bytes


def encode_packet(packet: Packet) -> bytes:
    """Encode a Packet into a complete binary frame."""
    if not 0 <= packet.msg_id <= 255:
        raise ProtocolError(f"msg_id must be 0-255, got {packet.msg_id}")
    if len(packet.payload) > MAX_PAYLOAD_LEN:
        raise PayloadLengthError(
            f"Payload length {len(packet.payload)} exceeds maximum {MAX_PAYLOAD_LEN}"
        )

    payload_len = len(packet.payload)
    crc_data = bytes([packet.msg_id, payload_len]) + packet.payload
    crc = calculate_crc16(crc_data)

    return (
        bytes([SOF_BYTE, packet.msg_id, payload_len])
        + packet.payload
        + crc.to_bytes(2, "big")
        + bytes([EOF_BYTE])
    )


def decode_packet(raw: bytes) -> Packet:
    """Decode a complete binary frame into a Packet.

    Validates SOF, EOF, payload length, frame length, and CRC.
    """
    if len(raw) < FRAME_OVERHEAD:
        raise FramingError(f"Frame too short: {len(raw)} bytes")
    if raw[0] != SOF_BYTE:
        raise FramingError(f"Invalid SOF: 0x{raw[0]:02X}")
    if raw[-1] != EOF_BYTE:
        raise FramingError(f"Invalid EOF: 0x{raw[-1]:02X}")

    payload_len = raw[2]
    if payload_len > MAX_PAYLOAD_LEN:
        raise PayloadLengthError(
            f"Payload length {payload_len} exceeds maximum {MAX_PAYLOAD_LEN}"
        )

    expected_len = FRAME_OVERHEAD + payload_len
    if len(raw) != expected_len:
        raise FramingError(
            f"Frame length mismatch: expected {expected_len}, got {len(raw)}"
        )

    crc_data = raw[1 : 3 + payload_len]
    crc_received = int.from_bytes(raw[3 + payload_len : 5 + payload_len], "big")
    if not verify_crc16(crc_data, crc_received):
        raise CRCMismatchError(
            f"CRC mismatch: received 0x{crc_received:04X}, "
            f"calculated 0x{calculate_crc16(crc_data):04X}"
        )

    return Packet(msg_id=raw[1], payload=raw[3 : 3 + payload_len])


class StreamParser:
    """Incrementally parse a byte stream into validated Packets.

    Handles leading noise, fragmented input across multiple feed() calls,
    and multiple concatenated packets in a single buffer.
    """

    def __init__(self):
        self._buffer = bytearray()

    def feed(self, chunk: bytes) -> list[Packet]:
        """Append *chunk* to the internal buffer and return all complete valid packets."""
        self._buffer.extend(chunk)
        packets: list[Packet] = []

        while len(self._buffer) >= FRAME_OVERHEAD:
            try:
                sof_pos = self._buffer.index(SOF_BYTE)
            except ValueError:
                self._buffer.clear()
                break

            if sof_pos > 0:
                logger.debug("Skipping %d noise bytes before SOF", sof_pos)
                del self._buffer[:sof_pos]

            if len(self._buffer) < FRAME_OVERHEAD:
                break

            payload_len = self._buffer[2]
            if payload_len > MAX_PAYLOAD_LEN:
                del self._buffer[0]
                continue

            frame_len = FRAME_OVERHEAD + payload_len
            if len(self._buffer) < frame_len:
                break

            if self._buffer[frame_len - 1] != EOF_BYTE:
                del self._buffer[0]
                continue

            crc_data = bytes(self._buffer[1 : 3 + payload_len])
            crc_received = int.from_bytes(
                self._buffer[3 + payload_len : 5 + payload_len], "big"
            )
            if not verify_crc16(crc_data, crc_received):
                del self._buffer[0]
                continue

            packets.append(
                Packet(
                    msg_id=self._buffer[1],
                    payload=bytes(self._buffer[3 : 3 + payload_len]),
                )
            )
            del self._buffer[:frame_len]

        return packets

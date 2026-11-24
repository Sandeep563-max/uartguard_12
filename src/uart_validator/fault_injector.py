"""Simple fault injection utilities for corrupting binary frames."""

from __future__ import annotations



class FaultInjector:
    """Provides methods to introduce specific faults into encoded frames."""

    def flip_bit(self, frame: bytes, byte_index: int, bit_index: int) -> bytes:
        """Flip a single bit at the given byte and bit position."""
        if byte_index < 0 or byte_index >= len(frame):
            raise IndexError(
                f"byte_index {byte_index} out of range for frame of {len(frame)} bytes"
            )
        if bit_index < 0 or bit_index > 7:
            raise ValueError(f"bit_index must be 0-7, got {bit_index}")
        result = bytearray(frame)
        result[byte_index] ^= 1 << bit_index
        return bytes(result)

    def corrupt_crc(self, frame: bytes) -> bytes:
        """Invert both CRC bytes (the two bytes immediately before EOF)."""
        if len(frame) < 6:
            raise ValueError("Frame too short to contain a CRC field")
        result = bytearray(frame)
        result[-3] ^= 0xFF
        result[-2] ^= 0xFF
        return bytes(result)

    def corrupt_sof(self, frame: bytes, bad_byte: int = 0x00) -> bytes:
        """Replace the SOF byte with *bad_byte*."""
        if not frame:
            raise ValueError("Frame is empty")
        result = bytearray(frame)
        result[0] = bad_byte
        return bytes(result)

    def corrupt_eof(self, frame: bytes, bad_byte: int = 0xFF) -> bytes:
        """Replace the EOF byte with *bad_byte*."""
        if not frame:
            raise ValueError("Frame is empty")
        result = bytearray(frame)
        result[-1] = bad_byte
        return bytes(result)

    def truncate(self, frame: bytes, keep_bytes: int) -> bytes:
        """Return only the first *keep_bytes* of the frame."""
        if keep_bytes < 0:
            raise ValueError(f"keep_bytes must be non-negative, got {keep_bytes}")
        if keep_bytes > len(frame):
            raise ValueError(
                f"keep_bytes ({keep_bytes}) exceeds frame length ({len(frame)})"
            )
        return frame[:keep_bytes]

    def inject_leading_noise(self, frame: bytes, noise: bytes) -> bytes:
        """Prepend *noise* bytes before the frame."""
        return noise + frame

    def fragment(self, frame: bytes, chunk_size: int) -> list[bytes]:
        """Split the frame into chunks of *chunk_size* bytes."""
        if chunk_size <= 0:
            raise ValueError(f"chunk_size must be positive, got {chunk_size}")
        return [frame[i : i + chunk_size] for i in range(0, len(frame), chunk_size)]

"""CRC-16/CCITT-FALSE implementation.

Parameters:
    Polynomial:    0x1021
    Initial value: 0xFFFF
    Reflect input: No
    Reflect output: No
    XOR output:    0x0000

Validation: calculate_crc16(b"123456789") == 0x29B1
"""


def calculate_crc16(data: bytes) -> int:
    """Calculate CRC-16/CCITT-FALSE over the given bytes."""
    crc = 0xFFFF
    for byte in data:
        crc ^= byte << 8
        for _ in range(8):
            if crc & 0x8000:
                crc = (crc << 1) ^ 0x1021
            else:
                crc <<= 1
            crc &= 0xFFFF
    return crc


def verify_crc16(data: bytes, expected_crc: int) -> bool:
    """Return True if the CRC-16 of *data* matches *expected_crc*."""
    return calculate_crc16(data) == expected_crc

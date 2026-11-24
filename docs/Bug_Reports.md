# UARTGuard – Bug Reports

> These are resolved example QA defects documented during development. They are not production bugs.

---

## BUG-001: StreamParser fails to deliver valid frame after a corrupted frame

| Field             | Detail |
|-------------------|--------|
| **Bug ID**        | BUG-001 |
| **Summary**       | StreamParser stopped parsing after encountering a frame with an invalid CRC, causing a subsequent valid frame in the same buffer to be silently dropped. |
| **Severity**      | High |
| **Priority**      | P1 |
| **Environment**   | Python 3.11, Windows 11, pyserial 3.5 |
| **Steps to Reproduce** | 1. Encode a valid heartbeat packet. 2. Corrupt the CRC of the first frame. 3. Encode a second valid packet. 4. Concatenate both frames and feed them to `StreamParser.feed()`. 5. Observe that the returned list is empty. |
| **Expected Result** | The parser should skip the corrupted frame and return the second valid packet. |
| **Actual Result**  | The parser cleared the entire buffer upon CRC failure, discarding the valid second frame. |
| **Root Cause**     | After detecting a CRC mismatch, the parser used `self._buffer.clear()` instead of deleting only the first byte (`del self._buffer[0]`) and continuing the scan for the next SOF byte. |
| **Resolution**     | Changed the CRC-failure branch to `del self._buffer[0]` followed by `continue`, allowing the while loop to find the next valid SOF and parse the remaining data. |
| **Status**         | ✅ Resolved |

---

## BUG-002: CRC-16 calculation returned wrong value due to incorrect initial seed

| Field             | Detail |
|-------------------|--------|
| **Bug ID**        | BUG-002 |
| **Summary**       | `calculate_crc16(b"123456789")` returned `0xE5CC` instead of the expected `0x29B1`, causing every packet to fail CRC verification. |
| **Severity**      | Critical |
| **Priority**      | P0 |
| **Environment**   | Python 3.11, Ubuntu 22.04 |
| **Steps to Reproduce** | 1. Call `calculate_crc16(b"123456789")`. 2. Compare the result to the known CRC-16/CCITT-FALSE test vector `0x29B1`. |
| **Expected Result** | The function returns `0x29B1`. |
| **Actual Result**  | The function returned `0xE5CC`. |
| **Root Cause**     | The initial CRC value was set to `0x0000` instead of `0xFFFF`. The CRC-16/CCITT-FALSE variant requires an initial value of `0xFFFF`, while `0x0000` corresponds to the CRC-16/XMODEM variant. |
| **Resolution**     | Changed `crc = 0x0000` to `crc = 0xFFFF` in `calculate_crc16()`. Added the standard test vector assertion to the smoke test suite to catch regressions. |
| **Status**         | ✅ Resolved |

---

## BUG-003: encode_packet accepted a 65-byte payload without raising an error

| Field             | Detail |
|-------------------|--------|
| **Bug ID**        | BUG-003 |
| **Summary**       | `encode_packet()` did not validate the payload length before encoding, allowing a 65-byte payload to be packed into a frame that violates the protocol specification (maximum 64 bytes). |
| **Severity**      | Medium |
| **Priority**      | P2 |
| **Environment**   | Python 3.11, macOS 14 |
| **Steps to Reproduce** | 1. Create a `Packet` with a 65-byte payload. 2. Call `encode_packet(packet)`. 3. Observe that no exception is raised and a frame is returned. 4. Attempt to decode the frame with `decode_packet()` — it raises `PayloadLengthError` on the receiving side. |
| **Expected Result** | `encode_packet()` should raise `PayloadLengthError` when the payload exceeds 64 bytes, preventing the invalid frame from being transmitted. |
| **Actual Result**  | The encoder produced a frame with `LEN = 65`. The decoder correctly rejected it, but the sender had already transmitted the invalid data. |
| **Root Cause**     | The length check (`len(packet.payload) > MAX_PAYLOAD_LEN`) was missing from `encode_packet()`. Validation was only present in `decode_packet()`. |
| **Resolution**     | Added a payload length check at the top of `encode_packet()` that raises `PayloadLengthError` before any encoding takes place. Added `test_oversized_payload_65_bytes` to the boundary test suite. |
| **Status**         | ✅ Resolved |

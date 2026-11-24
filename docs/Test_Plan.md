# UARTGuard – QA Test Plan

## 1. Objective

Validate the correctness, robustness, and reliability of the UARTGuard binary protocol implementation, including packet framing, CRC integrity, telemetry encoding, fault tolerance, and serial loopback transport.

## 2. Scope

### 2.1 In-Scope

- CRC-16/CCITT-FALSE calculation and verification
- Binary frame encoding and decoding (SOF, MSG_ID, LEN, PAYLOAD, CRC, EOF)
- StreamParser: noise rejection, fragmentation handling, multi-packet buffers
- Telemetry payload struct packing/unpacking and limit validation
- Fault injection: bit flips, CRC corruption, SOF/EOF corruption, truncation, fragmentation
- Serial loopback transport using pyserial's `loop://` virtual port
- Boundary value analysis for payload sizes and sensor operating limits

### 2.2 Out-of-Scope

- Physical UART hardware testing
- Performance and stress testing
- Security and penetration testing
- GUI or web-based interfaces
- Network communication protocols
- Database or persistent storage

## 3. Test Strategy

### 3.1 Smoke Testing

Quick sanity checks executed first to confirm that the core components are operational before running the full suite. Covers the CRC test vector, basic encode/decode, and loopback connectivity.

**Marker:** `@pytest.mark.smoke`

### 3.2 Functional Testing

Thorough verification of protocol encoding/decoding for all defined message IDs, multiple payload sizes, round-trip consistency, concatenated packet parsing, garbage recovery, fragmented input reassembly, and floating-point telemetry precision.

**Marker:** `@pytest.mark.functional`

### 3.3 CRC Verification

Confirms CRC-16/CCITT-FALSE correctness against the standard test vector (`b"123456789"` → `0x29B1`), and verifies that every encoded frame passes CRC validation on decode.

### 3.4 Boundary Value Analysis

Tests the edges of valid input ranges:

| Parameter       | Min     | Max     |
|-----------------|---------|---------|
| Payload length  | 0 bytes | 64 bytes|
| Temperature     | −40.0 °C| 125.0 °C|
| Voltage         | 0.0 V   | 24.0 V  |
| Current         | 0.0 mA  | 5000.0 mA|

Both valid boundary values and values immediately outside the range are tested.

**Marker:** `@pytest.mark.boundary`

### 3.5 Fault Injection Testing

Intentionally corrupts encoded frames to verify that the decoder and StreamParser detect and reject malformed data:

- Single-bit flips in header and payload
- CRC byte inversion
- SOF and EOF byte replacement
- Frame truncation
- Invalid and mismatched length fields
- 1-byte and 3-byte fragmentation (valid frame, delivered in pieces)

**Marker:** `@pytest.mark.fault_injection`

### 3.6 Serial Loopback Integration Testing

End-to-end tests using pyserial's virtual loopback (`loop://`):

- Single and multiple packet send/receive
- Telemetry payload round-trip over serial
- Corrupted packet rejection (transport timeout)
- Read timeout when no data is available

**Marker:** `@pytest.mark.integration`

## 4. Test Environment

| Component       | Detail                                      |
|-----------------|---------------------------------------------|
| Language        | Python 3.10+                                |
| Test framework  | pytest                                      |
| Reporting       | pytest-html (self-contained HTML report)     |
| Coverage        | pytest-cov (line coverage, term-missing)     |
| Serial backend  | pyserial `loop://` virtual loopback          |
| OS              | Cross-platform (Windows, Linux, macOS)       |

## 5. Entry Criteria

- All source modules compile without errors.
- All dependencies install successfully from `requirements.txt`.
- The pyserial loopback port opens without errors.

## 6. Exit Criteria

- 100% of automated tests pass.
- Code coverage is at least 90%.
- No critical or high-severity defects remain open.
- HTML test report is generated at `reports/test_report.html`.

## 7. Pass / Fail Criteria

| Criterion                              | Pass                           |
|----------------------------------------|--------------------------------|
| Individual test                        | No assertion failures or unexpected exceptions |
| CRC known vector                       | `calculate_crc16(b"123456789") == 0x29B1` |
| Packet round-trip                      | Decoded fields match original  |
| Fault detection                        | Appropriate exception raised   |
| Boundary values                        | Valid edges accepted; invalid edges rejected |
| Loopback transport                     | Sent data received identically |
| Timeout                                | `TransportTimeoutError` raised when expected |

## 8. Defect Severity and Priority Matrix

| Severity  | Description                                               | Priority |
|-----------|-----------------------------------------------------------|----------|
| Critical  | CRC validation accepts corrupted data; data loss           | P0       |
| High      | Framing error not detected; incorrect telemetry decode     | P1       |
| Medium    | StreamParser fails to recover after a single bad frame     | P2       |
| Low       | Logging message missing; cosmetic issue in report          | P3       |

Defects are documented in `docs/Bug_Reports.md` with root cause and resolution.

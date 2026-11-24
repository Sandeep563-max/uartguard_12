# UARTGuard – Automated UART/Serial Binary Protocol & Telemetry Validator

UARTGuard is a Python-based QA automation project for validating UART binary protocol framing, CRC integrity, sensor telemetry encoding, and fault tolerance. It uses pyserial's virtual loopback for integration testing — no physical hardware is required.

## Features

- **Binary packet framing** – encode and decode frames with SOF, MSG_ID, LEN, PAYLOAD, CRC-16, and EOF fields.
- **CRC-16/CCITT-FALSE** – pure Python implementation with standard test vector validation.
- **Sensor telemetry** – struct-based encoding/decoding of temperature, voltage, current, and status flags with operating limit validation.
- **Stream parser** – incremental parser that handles leading noise, fragmented input, and multiple concatenated packets.
- **Fault injection** – bit flips, CRC corruption, SOF/EOF corruption, truncation, and frame fragmentation.
- **Serial loopback transport** – send and receive packets over pyserial's `loop://` virtual port.
- **Automated test suite** – 50+ pytest test cases with HTML reporting and code coverage.
- **CI/CD ready** – GitHub Actions and Bitbucket Pipelines configurations included.

## Binary Packet Format

```
+------+--------+-----+------------------+-----------+------+
| SOF  | MSG_ID | LEN |     PAYLOAD      |   CRC16   | EOF  |
| 0xAA | 1 byte | 1 B |   0 – 64 bytes   | 2 B (BE)  | 0x55 |
+------+--------+-----+------------------+-----------+------+
```

- **SOF** – Start of Frame marker (`0xAA`).
- **MSG_ID** – Message type identifier (1 byte).
- **LEN** – Payload length in bytes (0–64).
- **PAYLOAD** – Variable-length data.
- **CRC16** – CRC-16/CCITT-FALSE over `MSG_ID + LEN + PAYLOAD`, big-endian.
- **EOF** – End of Frame marker (`0x55`).

## Message ID Reference

| Name           | Value  | Description              |
|----------------|--------|--------------------------|
| HEARTBEAT      | `0x01` | Keep-alive signal        |
| TELEMETRY      | `0x02` | Sensor data payload      |
| CONFIG_ACK     | `0x03` | Configuration acknowledged|
| ERROR_REPORT   | `0xFF` | Error notification       |

## Sensor Operating Limits

| Parameter   | Min      | Max       | Unit |
|-------------|----------|-----------|------|
| Temperature | −40.0    | 125.0     | °C   |
| Voltage     | 0.0      | 24.0      | V    |
| Current     | 0.0      | 5000.0    | mA   |

## Project Structure

```
├── .github/workflows/ci.yml    # GitHub Actions CI
├── bitbucket-pipelines.yml      # Bitbucket Pipelines CI
├── docs/
│   ├── Test_Plan.md             # QA test plan
│   ├── Test_Cases.csv           # Test case traceability matrix
│   └── Bug_Reports.md           # Resolved QA defect reports
├── reports/                     # Generated test reports
├── src/uart_validator/
│   ├── __init__.py
│   ├── config.py                # Protocol constants and sensor limits
│   ├── exceptions.py            # Custom exception hierarchy
│   ├── crc.py                   # CRC-16/CCITT-FALSE implementation
│   ├── protocol.py              # Packet encode/decode and StreamParser
│   ├── fault_injector.py        # Fault injection utilities
│   ├── sensor_node.py           # Telemetry encoding and validation
│   └── transport.py             # Serial loopback transport
├── tests/
│   ├── conftest.py              # Shared fixtures
│   ├── test_smoke.py            # Smoke tests
│   ├── test_crc_and_framing.py  # CRC and framing tests
│   ├── test_boundary.py         # Boundary value analysis
│   ├── test_fault_injection.py  # Fault injection tests
│   └── test_serial_loopback.py  # Loopback integration tests
├── .gitignore
├── pytest.ini                   # pytest configuration
├── requirements.txt             # Python dependencies
└── README.md
```

## Setup

### Prerequisites

- Python 3.10 or later
- pip (comes with Python)

### Installation

1. Clone the repository or navigate to the project directory:

```bash
cd UARTGuard
```

2. Create and activate a virtual environment (recommended):

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# Linux / macOS
source .venv/bin/activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

## Running Tests

### Full Test Suite

Run all tests with coverage and HTML reporting:

```bash
python -m pytest
```

This generates:
- Terminal output with line-by-line coverage.
- An HTML report at `reports/test_report.html`.

### Run Tests by Marker

Run only smoke tests:

```bash
python -m pytest -m smoke
```

Run only boundary tests:

```bash
python -m pytest -m boundary
```

Run only fault injection tests:

```bash
python -m pytest -m fault_injection
```

Run only integration tests:

```bash
python -m pytest -m integration
```

Available markers: `smoke`, `functional`, `boundary`, `negative`, `fault_injection`, `regression`, `integration`.

### HTML Test Report

After running the tests, open the generated report:

```
reports/test_report.html
```

Open it in any web browser to see a detailed pass/fail summary with timestamps, durations, and error details for any failures.

## QA Documentation

| Document                        | Description                                           |
|---------------------------------|-------------------------------------------------------|
| `docs/Test_Plan.md`             | Test strategy, scope, entry/exit criteria, severity matrix |
| `docs/Test_Cases.csv`           | Test case traceability matrix mapped to automated tests |
| `docs/Bug_Reports.md`           | Three resolved example QA defects with root cause analysis |

## CI/CD

### GitHub Actions

The workflow at `.github/workflows/ci.yml` runs on every push and pull request to `main`:

1. Sets up Python 3.11.
2. Installs dependencies from `requirements.txt`.
3. Runs the full pytest suite.
4. Uploads `reports/test_report.html` as a build artifact.

### Bitbucket Pipelines

The `bitbucket-pipelines.yml` configuration runs the same test suite using the `python:3.11` Docker image on every push.

## License

This project is for educational and demonstration purposes.

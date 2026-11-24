"""Shared pytest fixtures for the UART validator test suite."""

import pytest

from uart_validator.config import MessageID
from uart_validator.protocol import Packet, StreamParser
from uart_validator.fault_injector import FaultInjector
from uart_validator.sensor_node import TelemetryReading
from uart_validator.transport import SerialLoopbackTransport


@pytest.fixture
def sample_telemetry():
    """A typical in-range telemetry reading."""
    return TelemetryReading(
        temperature_c=25.0,
        voltage_v=12.0,
        current_ma=500.0,
        status_flags=0x01,
    )


@pytest.fixture
def valid_packet():
    """A minimal valid heartbeat packet with a one-byte payload."""
    return Packet(msg_id=MessageID.HEARTBEAT, payload=b"\x00")


@pytest.fixture
def stream_parser():
    """A fresh StreamParser instance."""
    return StreamParser()


@pytest.fixture
def fault_injector():
    """A FaultInjector instance."""
    return FaultInjector()


@pytest.fixture
def loopback_transport():
    """An opened SerialLoopbackTransport (closed automatically after the test)."""
    with SerialLoopbackTransport(timeout=0.1) as transport:
        yield transport

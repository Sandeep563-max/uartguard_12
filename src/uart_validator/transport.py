"""Serial loopback transport using pyserial's virtual loop:// URL."""

from __future__ import annotations

import time
import logging

import serial

from .config import DEFAULT_BAUDRATE, DEFAULT_TIMEOUT
from .exceptions import TransportTimeoutError
from .protocol import Packet, encode_packet, StreamParser

logger = logging.getLogger(__name__)


class SerialLoopbackTransport:
    """Context-managed serial transport backed by pyserial's virtual loopback.

    Usage::

        with SerialLoopbackTransport() as transport:
            transport.send_packet(packet)
            received = transport.receive_packet()
    """

    def __init__(
        self,
        baudrate: int = DEFAULT_BAUDRATE,
        timeout: float = DEFAULT_TIMEOUT,
    ):
        self._baudrate = baudrate
        self._timeout = timeout
        self._port: serial.Serial | None = None
        self._parser = StreamParser()
        self._pending: list[Packet] = []

    def __enter__(self):
        self._port = serial.serial_for_url(
            "loop://",
            baudrate=self._baudrate,
            timeout=self._timeout,
        )
        self._parser = StreamParser()
        self._pending = []
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._port and self._port.is_open:
            self._port.close()
        return False

    def send_bytes(self, data: bytes) -> int:
        """Write raw bytes to the serial port and return the count written."""
        return self._port.write(data)

    def receive_bytes(self, size: int) -> bytes:
        """Read up to *size* bytes from the serial port."""
        return self._port.read(size)

    def send_packet(self, packet: Packet) -> None:
        """Encode and transmit a Packet."""
        self._port.write(encode_packet(packet))

    def receive_packet(self) -> Packet:
        """Block until a complete valid packet is decoded, or raise on timeout."""
        if self._pending:
            return self._pending.pop(0)

        deadline = time.monotonic() + self._timeout
        while time.monotonic() < deadline:
            chunk = self._port.read(1)
            if not chunk:
                break
            waiting = self._port.in_waiting
            if waiting > 0:
                chunk += self._port.read(waiting)
            packets = self._parser.feed(chunk)
            if packets:
                self._pending.extend(packets[1:])
                return packets[0]

        raise TransportTimeoutError("No complete packet received within timeout")

"""Gateway connection management for Waveshare Eth2X devices."""

import asyncio
import logging
import time
from typing import Optional

from .exceptions import GatewayConnectionError, GatewayTimeoutError
from .protocol import ModbusRTU

_LOGGER = logging.getLogger(__name__)


class GatewayConnection:
    """Manages TCP connection to a Waveshare Eth2X gateway."""

    def __init__(
        self,
        host: str,
        port: int,
        timeout: float = 10.0,
        keepalive_interval: float = 300.0,
    ):
        """Initialize gateway connection.
        
        Args:
            host: Gateway IP address or hostname
            port: Gateway port (typically 8234)
            timeout: Connection timeout in seconds
            keepalive_interval: Keep-alive probe interval in seconds
        """
        self.host = host
        self.port = port
        self.timeout = timeout
        self.keepalive_interval = keepalive_interval
        
        self._reader: Optional[asyncio.StreamReader] = None
        self._writer: Optional[asyncio.StreamWriter] = None
        self._connected = False
        self._last_activity = time.time()
        self._lock = asyncio.Lock()

    @property
    def connected(self) -> bool:
        """Check if connection is active."""
        return self._connected and self._reader is not None and self._writer is not None

    async def connect(self) -> None:
        """Establish TCP connection to gateway.
        
        Raises:
            GatewayConnectionError: If connection fails
            GatewayTimeoutError: If connection times out
        """
        async with self._lock:
            if self.connected:
                _LOGGER.debug("Already connected to %s:%d", self.host, self.port)
                return
            
            try:
                _LOGGER.debug("Connecting to %s:%d", self.host, self.port)
                self._reader, self._writer = await asyncio.wait_for(
                    asyncio.open_connection(self.host, self.port),
                    timeout=self.timeout,
                )
                self._connected = True
                self._last_activity = time.time()
                _LOGGER.info("Connected to gateway %s:%d", self.host, self.port)
                
            except asyncio.TimeoutError as err:
                self._connected = False
                raise GatewayTimeoutError(
                    f"Connection timeout to {self.host}:{self.port}"
                ) from err
            except (OSError, asyncio.CancelledError) as err:
                self._connected = False
                raise GatewayConnectionError(
                    f"Failed to connect to {self.host}:{self.port}: {err}"
                ) from err

    async def disconnect(self) -> None:
        """Close TCP connection to gateway."""
        async with self._lock:
            if self._writer is not None:
                try:
                    self._writer.close()
                    await self._writer.wait_closed()
                except Exception as err:
                    _LOGGER.warning("Error closing connection: %s", err)
            
            self._reader = None
            self._writer = None
            self._connected = False
            _LOGGER.info("Disconnected from gateway %s:%d", self.host, self.port)

    async def send_modbus_request(
        self,
        request: bytes,
    ) -> bytes:
        """Send Modbus RTU request and receive response.
        
        Args:
            request: Modbus RTU frame (including CRC)
            
        Returns:
            Modbus RTU response frame
            
        Raises:
            GatewayConnectionError: If not connected
            GatewayTimeoutError: If request times out
        """
        if not self.connected:
            raise GatewayConnectionError("Not connected to gateway")
        
        async with self._lock:
            try:
                # Send request
                _LOGGER.debug("Sending Modbus request: %s", request.hex())
                self._writer.write(request)
                await asyncio.wait_for(
                    self._writer.drain(),
                    timeout=self.timeout,
                )
                
                # Read response header (slave_id + function_code + byte_count)
                response_header = await asyncio.wait_for(
                    self._reader.readexactly(3),
                    timeout=self.timeout,
                )
                
                # Get byte count to determine response size
                byte_count = response_header[2]
                
                # Calculate remaining bytes to read
                # Format: slave(1) + func(1) + byte_count(1) + data(byte_count) + crc(2)
                remaining = byte_count + 2  # data + crc
                
                response_data = await asyncio.wait_for(
                    self._reader.readexactly(remaining),
                    timeout=self.timeout,
                )
                
                response = response_header + response_data
                _LOGGER.debug("Received Modbus response: %s", response.hex())
                
                self._last_activity = time.time()
                return response
                
            except asyncio.TimeoutError as err:
                await self.disconnect()
                raise GatewayTimeoutError(
                    f"Request timeout to {self.host}:{self.port}"
                ) from err
            except (OSError, asyncio.CancelledError) as err:
                await self.disconnect()
                raise GatewayConnectionError(
                    f"Connection error with {self.host}:{self.port}: {err}"
                ) from err

    async def keepalive_probe(self) -> None:
        """Send a keep-alive probe to maintain connection.
        
        Uses a read input registers probe with invalid address to keep connection alive
        without affecting device state.
        """
        if not self.connected:
            return
        
        try:
            # Send a probe request (read input register at high address)
            probe_request = ModbusRTU.frame_read_input_registers(
                slave_id=1,
                start_address=0xFFFF,
                quantity=1,
            )
            
            try:
                await self.send_modbus_request(probe_request)
            except (GatewayTimeoutError, GatewayConnectionError):
                # Probe failure is not critical, just log it
                _LOGGER.debug("Keep-alive probe failed")
                
        except Exception as err:
            _LOGGER.warning("Unexpected error in keep-alive probe: %s", err)

    def get_connection_uptime(self) -> float:
        """Get connection uptime in seconds."""
        if not self.connected:
            return 0.0
        return time.time() - self._last_activity

    def get_idle_time(self) -> float:
        """Get time since last activity in seconds."""
        return time.time() - self._last_activity


class ConnectionPool:
    """Connection pool for managing multiple RS485 gateways."""

    def __init__(self):
        """Initialize connection pool."""
        self._connections: dict[str, GatewayConnection] = {}
        self._request_queues: dict[str, asyncio.Queue] = {}
        self._lock = asyncio.Lock()
        self._min_request_delay = 0.1  # 100ms between requests

    def get_connection(
        self,
        gateway_id: str,
        host: str,
        port: int,
        timeout: float = 10.0,
        keepalive_interval: float = 300.0,
    ) -> GatewayConnection:
        """Get or create a connection to a gateway.
        
        Args:
            gateway_id: Unique identifier for this gateway
            host: Gateway IP address
            port: Gateway port
            timeout: Connection timeout
            keepalive_interval: Keep-alive interval
            
        Returns:
            GatewayConnection instance
        """
        if gateway_id not in self._connections:
            self._connections[gateway_id] = GatewayConnection(
                host=host,
                port=port,
                timeout=timeout,
                keepalive_interval=keepalive_interval,
            )
            self._request_queues[gateway_id] = asyncio.Queue()
        
        return self._connections[gateway_id]

    async def send_request(
        self,
        gateway_id: str,
        request: bytes,
    ) -> bytes:
        """Send a request through the connection pool with serialization.
        
        Ensures requests are properly serialized per gateway to avoid collisions
        on the RS485 bus.
        
        Args:
            gateway_id: Target gateway ID
            request: Modbus RTU frame
            
        Returns:
            Modbus RTU response
            
        Raises:
            GatewayConnectionError: If gateway not found or connection fails
        """
        if gateway_id not in self._connections:
            raise GatewayConnectionError(f"Gateway {gateway_id} not found")
        
        connection = self._connections[gateway_id]
        
        # Queue the request to serialize them per gateway
        queue = self._request_queues[gateway_id]
        future = asyncio.Future()
        await queue.put((request, future))
        
        # Wait for the response
        try:
            response = await asyncio.wait_for(future, timeout=connection.timeout + 5)
            return response
        except asyncio.TimeoutError as err:
            raise GatewayTimeoutError(f"Request timed out on {gateway_id}") from err

    async def _process_queue(self, gateway_id: str) -> None:
        """Process request queue for a gateway.
        
        This coroutine should run continuously to serialize requests.
        """
        connection = self._connections.get(gateway_id)
        queue = self._request_queues.get(gateway_id)
        
        if not connection or not queue:
            return
        
        last_request_time = time.time()
        
        while True:
            try:
                request, future = await queue.get()
                
                # Ensure minimum delay between requests
                elapsed = time.time() - last_request_time
                if elapsed < self._min_request_delay:
                    await asyncio.sleep(self._min_request_delay - elapsed)
                
                try:
                    # Ensure connection is established
                    if not connection.connected:
                        await connection.connect()
                    
                    # Send request
                    response = await connection.send_modbus_request(request)
                    future.set_result(response)
                    
                except Exception as err:
                    if not future.done():
                        future.set_exception(err)
                
                last_request_time = time.time()
                queue.task_done()
                
            except asyncio.CancelledError:
                break
            except Exception as err:
                _LOGGER.error("Error processing queue for %s: %s", gateway_id, err)
                await asyncio.sleep(1)

    async def disconnect(self, gateway_id: str) -> None:
        """Disconnect from a specific gateway.
        
        Args:
            gateway_id: Target gateway ID
        """
        if gateway_id in self._connections:
            await self._connections[gateway_id].disconnect()

    async def disconnect_all(self) -> None:
        """Disconnect from all gateways."""
        for connection in self._connections.values():
            await connection.disconnect()

    def remove_connection(self, gateway_id: str) -> None:
        """Remove a connection from the pool.
        
        Args:
            gateway_id: Target gateway ID
        """
        if gateway_id in self._connections:
            del self._connections[gateway_id]
            del self._request_queues[gateway_id]
       
"""Modbus RTU protocol implementation for RS485."""

import logging
from typing import Dict, List, Optional, Tuple, Union

from .exceptions import ModbusCRCError, ModbusResponseError

_LOGGER = logging.getLogger(__name__)


class ModbusRTU:
    """Modbus RTU protocol handler for RS485 communication."""

    # Modbus function codes
    FC_READ_HOLDING_REGISTERS = 3
    FC_READ_INPUT_REGISTERS = 4
    FC_WRITE_SINGLE_REGISTER = 6
    FC_WRITE_MULTIPLE_REGISTERS = 16

    # Exception codes
    EXCEPTION_ILLEGAL_FUNCTION = 1
    EXCEPTION_ILLEGAL_DATA_ADDRESS = 2
    EXCEPTION_ILLEGAL_DATA_VALUE = 3
    EXCEPTION_DEVICE_FAILURE = 4
    EXCEPTION_ACKNOWLEDGE = 5
    EXCEPTION_DEVICE_BUSY = 6
    EXCEPTION_NEGATIVE_ACKNOWLEDGE = 7
    EXCEPTION_MEMORY_PARITY_ERROR = 8
    EXCEPTION_GATEWAY_PATH_UNAVAILABLE = 10
    EXCEPTION_GATEWAY_TARGET_FAILED = 11

    @staticmethod
    def calculate_crc16(data: bytes) -> int:
        """Calculate CRC16 for Modbus RTU.
        
        Uses CRC-16-CCITT (Modbus) polynomial.
        """
        crc = 0xFFFF
        
        for byte in data:
            crc ^= byte
            for _ in range(8):
                if crc & 1:
                    crc = (crc >> 1) ^ 0xA001
                else:
                    crc >>= 1
        
        return crc

    @staticmethod
    def frame_read_holding_registers(
        slave_id: int,
        start_address: int,
        quantity: int,
    ) -> bytes:
        """Build Modbus RTU frame to read holding registers (function 3).
        
        Args:
            slave_id: Modbus slave ID (1-247)
            start_address: Starting register address
            quantity: Number of registers to read
            
        Returns:
            Complete Modbus RTU frame with CRC
        """
        frame = bytearray([
            slave_id,
            ModbusRTU.FC_READ_HOLDING_REGISTERS,
            (start_address >> 8) & 0xFF,
            start_address & 0xFF,
            (quantity >> 8) & 0xFF,
            quantity & 0xFF,
        ])
        
        crc = ModbusRTU.calculate_crc16(frame)
        frame.append(crc & 0xFF)
        frame.append((crc >> 8) & 0xFF)
        
        return bytes(frame)

    @staticmethod
    def frame_read_input_registers(
        slave_id: int,
        start_address: int,
        quantity: int,
    ) -> bytes:
        """Build Modbus RTU frame to read input registers (function 4).
        
        Args:
            slave_id: Modbus slave ID (1-247)
            start_address: Starting register address
            quantity: Number of registers to read
            
        Returns:
            Complete Modbus RTU frame with CRC
        """
        frame = bytearray([
            slave_id,
            ModbusRTU.FC_READ_INPUT_REGISTERS,
            (start_address >> 8) & 0xFF,
            start_address & 0xFF,
            (quantity >> 8) & 0xFF,
            quantity & 0xFF,
        ])
        
        crc = ModbusRTU.calculate_crc16(frame)
        frame.append(crc & 0xFF)
        frame.append((crc >> 8) & 0xFF)
        
        return bytes(frame)

    @staticmethod
    def frame_write_single_register(
        slave_id: int,
        register_address: int,
        value: int,
    ) -> bytes:
        """Build Modbus RTU frame to write single register (function 6).
        
        Args:
            slave_id: Modbus slave ID (1-247)
            register_address: Register address to write to
            value: 16-bit value to write
            
        Returns:
            Complete Modbus RTU frame with CRC
        """
        frame = bytearray([
            slave_id,
            ModbusRTU.FC_WRITE_SINGLE_REGISTER,
            (register_address >> 8) & 0xFF,
            register_address & 0xFF,
            (value >> 8) & 0xFF,
            value & 0xFF,
        ])
        
        crc = ModbusRTU.calculate_crc16(frame)
        frame.append(crc & 0xFF)
        frame.append((crc >> 8) & 0xFF)
        
        return bytes(frame)

    @staticmethod
    def frame_write_multiple_registers(
        slave_id: int,
        start_address: int,
        values: List[int],
    ) -> bytes:
        """Build Modbus RTU frame to write multiple registers (function 16).
        
        Args:
            slave_id: Modbus slave ID (1-247)
            start_address: Starting register address
            values: List of 16-bit values to write
            
        Returns:
            Complete Modbus RTU frame with CRC
        """
        quantity = len(values)
        byte_count = quantity * 2
        
        frame = bytearray([
            slave_id,
            ModbusRTU.FC_WRITE_MULTIPLE_REGISTERS,
            (start_address >> 8) & 0xFF,
            start_address & 0xFF,
            (quantity >> 8) & 0xFF,
            quantity & 0xFF,
            byte_count,
        ])
        
        for value in values:
            frame.append((value >> 8) & 0xFF)
            frame.append(value & 0xFF)
        
        crc = ModbusRTU.calculate_crc16(frame)
        frame.append(crc & 0xFF)
        frame.append((crc >> 8) & 0xFF)
        
        return bytes(frame)

    @staticmethod
    def parse_response(
        response: bytes,
        expected_slave_id: int,
    ) -> Dict[str, Union[int, List[int]]]:
        """Parse Modbus RTU response frame.
        
        Args:
            response: Complete response frame with CRC
            expected_slave_id: Expected slave ID for validation
            
        Returns:
            Dictionary with parsed response data
            
        Raises:
            ModbusCRCError: If CRC check fails
            ModbusResponseError: If response is invalid or contains exception
        """
        if len(response) < 3:
            raise ModbusResponseError(f"Response too short: {len(response)} bytes")
        
        # Check CRC
        received_crc = (response[-1] << 8) | response[-2]
        frame_without_crc = response[:-2]
        calculated_crc = ModbusRTU.calculate_crc16(frame_without_crc)
        
        if received_crc != calculated_crc:
            raise ModbusCRCError(
                f"CRC mismatch: expected {calculated_crc:04X}, got {received_crc:04X}"
            )
        
        # Check slave ID
        slave_id = response[0]
        if slave_id != expected_slave_id:
            raise ModbusResponseError(
                f"Slave ID mismatch: expected {expected_slave_id}, got {slave_id}"
            )
        
        # Check for exception response
        function_code = response[1]
        if function_code & 0x80:
            exception_code = response[2]
            raise ModbusResponseError(
                f"Modbus exception {exception_code}: "
                f"{ModbusRTU._exception_message(exception_code)}"
            )
        
        # Parse based on function code
        if function_code in (ModbusRTU.FC_READ_HOLDING_REGISTERS, 
                            ModbusRTU.FC_READ_INPUT_REGISTERS):
            return ModbusRTU._parse_read_registers(response)
        elif function_code == ModbusRTU.FC_WRITE_SINGLE_REGISTER:
            return ModbusRTU._parse_write_single_register(response)
        elif function_code == ModbusRTU.FC_WRITE_MULTIPLE_REGISTERS:
            return ModbusRTU._parse_write_multiple_registers(response)
        else:
            raise ModbusResponseError(f"Unknown function code: {function_code}")

    @staticmethod
    def _parse_read_registers(response: bytes) -> Dict[str, Union[int, List[int]]]:
        """Parse read registers response (functions 3, 4)."""
        byte_count = response[2]
        
        if len(response) < 3 + byte_count + 2:
            raise ModbusResponseError(
                f"Response too short for byte count {byte_count}"
            )
        
        registers = []
        for i in range(0, byte_count, 2):
            reg_value = (response[3 + i] << 8) | response[4 + i]
            registers.append(reg_value)
        
        return {
            "function_code": response[1],
            "byte_count": byte_count,
            "registers": registers,
        }

    @staticmethod
    def _parse_write_single_register(response: bytes) -> Dict[str, int]:
        """Parse write single register response (function 6)."""
        if len(response) < 8:
            raise ModbusResponseError(
                f"Write single register response too short: {len(response)} bytes"
            )
        
        address = (response[2] << 8) | response[3]
        value = (response[4] << 8) | response[5]
        
        return {
            "function_code": response[1],
            "address": address,
            "value": value,
        }

    @staticmethod
    def _parse_write_multiple_registers(response: bytes) -> Dict[str, int]:
        """Parse write multiple registers response (function 16)."""
        if len(response) < 8:
            raise ModbusResponseError(
                f"Write multiple registers response too short: {len(response)} bytes"
            )
        
        address = (response[2] << 8) | response[3]
        quantity = (response[4] << 8) | response[5]
        
        return {
            "function_code": response[1],
            "address": address,
            "quantity": quantity,
        }

    @staticmethod
    def _exception_message(exception_code: int) -> str:
        """Get human-readable message for exception code."""
        messages = {
            1: "Illegal Function",
            2: "Illegal Data Address",
            3: "Illegal Data Value",
            4: "Device Failure",
            5: "Acknowledge",
            6: "Device Busy",
            7: "Negative Acknowledge",
            8: "Memory Parity Error",
            10: "Gateway Path Unavailable",
            11: "Gateway Target Device Failed to Respond",
        }
        return messages.get(exception_code, f"Unknown Exception {exception_code}")

    @staticmethod
    def parse_register_value(
        registers: List[int],
        data_type: str,
        scale: float = 1.0,
        offset: float = 0.0,
    ) -> Union[int, float]:
        """Parse register value from Modbus response.
        
        Args:
            registers: List of 16-bit register values
            data_type: Data type (uint16, uint32, int16, int32, float)
            scale: Scale factor to apply
            offset: Offset to apply
            
        Returns:
            Parsed value
        """
        if data_type == "uint16":
            if len(registers) < 1:
                raise ValueError("Need at least 1 register for uint16")
            value = registers[0]
        elif data_type == "uint32":
            if len(registers) < 2:
                raise ValueError("Need at least 2 registers for uint32")
            value = (registers[0] << 16) | registers[1]
        elif data_type == "int16":
            if len(registers) < 1:
                raise ValueError("Need at least 1 register for int16")
            value = registers[0]
            if value & 0x8000:
                value = -(0x10000 - value)
        elif data_type == "int32":
            if len(registers) < 2:
                raise ValueError("Need at least 2 registers for int32")
            value = (registers[0] << 16) | registers[1]
            if value & 0x80000000:
                value = -(0x100000000 - value)
        elif data_type == "float":
            if len(registers) < 2:
                raise ValueError("Need at least 2 registers for float")
            # IEEE 754 float from two 16-bit registers
            import struct
            bytes_val = struct.pack(
                ">HH",
                registers[0],
                registers[1],
            )
            value = struct.unpack(">f", bytes_val)[0]
        else:
            raise ValueError(f"Unknown data type: {data_type}")
        
        return (value * scale) + offset

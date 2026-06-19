# Waveshare Eth2X Home Assistant Integration

A complete Home Assistant integration for real-time monitoring and control of Solar Inverters connected via Waveshare Eth2X devices.

## Features

✅ **Multi-Gateway Support**
- Connect multiple Eth2X gateways
- Multiple devices per gateway (different Modbus slave IDs)
- Independent device configuration for each gateway

✅ **Supported Inverter Types**
- Deye Sun 12K
- Deye Sun 8K
- Deye Sun 6K
- Pytes E-Box 48100R (LiFePO4 battery)
- Deye Hybrid GW4137
- Generic Modbus devices (user-configurable)

✅ **Real-Time Monitoring**
- Solar PV input voltage/current/power (dual channels)
- Battery voltage/current/power/SOC/SOH/temperature
- Grid voltage/current/power/frequency/energy
- Inverter temperature, status, and fault codes
- Output voltage/current/power/frequency

✅ **Connection Health Monitoring**
- 5-state health system: healthy → degraded → warning → error → offline
- Real-time signal quality percentage
- Average response time tracking
- Automatic state transitions based on connection reliability

✅ **Comprehensive Error Tracking**
- Total error counter (persistent)
- Daily error counter (auto-reset at midnight)
- Monthly error counter (auto-reset at month boundary)
- Error type breakdown:
  - Modbus timeout errors
  - CRC checksum errors
  - Communication errors
  - Device no-response errors
- Error history (last 100 events)

✅ **Easy Configuration**
- 3-step Home Assistant UI configuration wizard
- Automatic device discovery via Modbus signature
- No manual YAML configuration required
- Live gateway connection validation

✅ **Smart Entity Management**
- Dynamic sensor creation based on device capabilities
- Automatic entity naming and organization
- Per-device entity grouping
- Binary sensors for connection status
- Number entities for writable registers
- Diagnostic entities for health monitoring

✅ **Robust Communication**
- Persistent TCP connections with keep-alive probes
- Per-gateway request serialization (100ms minimum delay)
- Exponential backoff on connection failures
- Automatic reconnection with health state tracking
- CRC16 checksum validation for Modbus frames

## Quick Start

### Requirements
- Home Assistant 2023.12.0 or newer
- Waveshare Eth2X device with default TCP port 8234
- Deye Solar Inverter connected to RS485 gateway
- Network connectivity between Home Assistant and gateway device

### Installation

1. Download the integration to your Home Assistant custom components:
   ```
   custom_components/waveshare_eth2x/
   ```

2. Restart Home Assistant or reload custom components

3. Go to **Settings → Devices & Services → Integrations**

4. Click **Create Integration** and search for "Waveshare Eth2X"

### Configuration

Follow the 3-step configuration wizard:

**Step 1: Gateway Connection**
- Enter gateway IP address (or hostname)
- Gateway port (default: 8234)
- Connection timeout in seconds (default: 10)

The integration will test the connection before proceeding.

**Step 2: Device Discovery**
- The integration scans the gateway for connected Modbus devices
- Auto-detects device type using the device ID register (0x000B)

**Step 3: Device Selection**
- Select which discovered devices to monitor
- Choose devices by their Modbus slave ID

After configuration, entities will automatically be created for:
- Register sensors (power, voltage, current, etc.)
- Health diagnostic sensors (connection state, response time, signal quality)
- Connection status binary sensor
- Writable parameter controls (where supported by device)

## Supported Registers

### Deye Sun 12K/8K/6K
- Solar PV inputs (PV1 & PV2): voltage, current, power
- Battery: voltage, current, power, SOC, SOH, temperature
- Grid: voltage, current, power, frequency, energy
- Inverter: temperature, status, fault code
- Output: voltage, current, power, frequency

### Deye Hybrid GW4137
- All Sun 12K registers
- AC Output: voltage, current, power, frequency (additional)

## Troubleshooting

### Connection Failed During Setup
- Verify the gateway IP address is correct
- Check network connectivity from Home Assistant to gateway
- Ensure gateway port is 8234 (or correct custom port)
- Verify gateway power and network connectivity
- Check firewall rules allowing TCP port 8234

### No Devices Found
- Verify devices are properly connected to RS485
- Check Modbus slave IDs (typically 1-10)
- Ensure device firmware supports Modbus RTU protocol
- Try manual device selection if auto-discovery fails

### Intermittent Connection Failures
- Monitor the "Signal Quality" entity (should be >90% for good connection)
- Check "Response Time" entity for latency issues (typical: 50-200ms)
- Review "Connection State" for health transitions
- Consider adding delays between requests if experiencing timeouts
- Check for RS485 line termination (should be 120Ω at ends)

### Entities Not Updating
- Check device connection status (should show "healthy")
- Verify entity is not in a custom "unavailable" state
- Check Home Assistant logs for error messages
- Try reloading the integration from Developer Tools

### High Error Rates
- Monitor error counters in device diagnostics
- Check Response Time sensor (if >5000ms, signal quality is poor)
- Verify RS485 cable length and quality
- Add termination resistors if not already present
- Consider reducing scan interval if errors occur under load

## Advanced Configuration

### Gateway Configuration
- **Host**: IP address or hostname of Waveshare device
- **Port**: TCP port (default 8234)
- **Timeout**: Connection timeout in seconds (default 10)
- **Keep-Alive Interval**: Seconds between keep-alive probes (default 30)

### Device Configuration
- **Slave ID**: Modbus slave address (1-247)
- **Device Type**: Auto-detected or manually selected
- **Device Name**: Custom name for the device
- **Scan Interval**: Update interval in seconds (default 30)

### Generic Modbus Device
For unsupported device types, use "Generic Modbus":
- Manually configure register definitions
- Specify data type: uint16, uint32, int16, int32, float
- Configure scale and offset factors
- Set unit of measurement

## Entity Naming

Entities are automatically named using the convention:
```
{entity_type}_{gateway_id}_{slave_id}_{register_name}
```

Examples:
- `sensor.waveshare_eth2x_192_168_1_100_1_solar_pv1_power`
- `binary_sensor.waveshare_eth2x_192_168_1_100_1_connection_status`
- `number.waveshare_eth2x_192_168_1_100_1_battery_charge_limit`

## Performance & Limitations

### Performance
- Per-gateway request serialization ensures 100ms minimum delay between requests
- Typical response time: 50-200ms depending on RS485 signal quality
- Recommended scan interval: 30-60 seconds
- Multi-gateway support: Limited by network bandwidth and Home Assistant CPU

### Limitations
- Requires at least one Waveshare Eth2X device
- Does not support serial RS485 connections directly
- Maximum 247 devices per gateway (Modbus limitation)
- Write operations not yet fully implemented (entities created but not functional)

## Architecture

The integration uses a multi-level coordinator pattern:

1. **IntegrationCoordinator**: Top-level orchestration of all gateways
2. **GatewayCoordinator**: Per-gateway device management and Modbus communication
3. **Device Classes**: Type-specific register mapping (Sun 12K, Hybrid, etc.)
4. **Entity Platforms**: Sensor, Binary Sensor, Number, Select entities

Health monitoring and error tracking operate at the per-device level, allowing fine-grained diagnostics for each inverter.

## Debugging

Enable debug logging:
```yaml
logger:
  logs:
    custom_components.waveshare_eth2x: debug
    custom_components.waveshare_eth2x.core: debug
    custom_components.waveshare_eth2x.coordinators: debug
```

## Contributing

To add support for additional inverter models:

1. Create a new device class in `devices/model_name.py`
2. Define register mappings extending `BaseDevice`
3. Register the device type in `devices/registry.py`
4. Add device ID signature to `const.py`

## License

This integration is provided as-is for Home Assistant users.

## Support

For issues, questions, or feature requests, please refer to the Home Assistant community forums.
       
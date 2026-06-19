# Configuration Guide - Waveshare Eth2X Home Assistant Integration

## Configuration Overview

This integration uses a 3-step configuration wizard accessible from **Settings → Devices & Services → Integrations**.

## Step 1: Gateway Connection

The first step configures your Waveshare Eth2X device.

### Fields

| Field | Required | Default | Description |
|-------|----------|---------|-------------|
| **Gateway IP or Hostname** | Yes | - | IP address (e.g., 192.168.1.100) or hostname of your Waveshare device |
| **Gateway Port** | No | 8234 | TCP port (typically 8234 for Waveshare devices) |
| **Connection Timeout** | No | 10 | Connection timeout in seconds |

### Examples

**Local Network (recommended)**:
```
Gateway IP: 192.168.1.100
Port: 8234
Timeout: 10
```

**Hostname Resolution**:
```
Gateway IP: waveshare.local
Port: 8234
Timeout: 10
```

**Custom Port**:
```
Gateway IP: 192.168.1.100
Port: 9000
Timeout: 15
```

### Connection Validation

The integration automatically tests the connection. If validation fails:
- Check the gateway IP/hostname is correct
- Verify the gateway is online and reachable
- Confirm the port number is correct
- Check firewall settings

## Step 2: Device Discovery

Once the gateway connection is established, the integration automatically scans for devices.

### What Happens

1. Scans each Modbus slave address (1-247)
2. Reads device ID register (0x000B) to identify device type
3. Displays list of found devices with:
   - Slave ID (Modbus address)
   - Device Type (e.g., "Deye Sun 12K")
   - Device Status (online/offline)

### Discovery Results

**Successful Discovery**:
- You should see a list of discovered devices
- Each device shows: "Slave X: Deye Sun 12K" (or other model)
- Proceed to Step 3

**No Devices Found**:
- Check that inverters are connected to RS485
- Verify RS485 wiring and termination
- Check Modbus slave IDs are correct
- Try manual configuration in Step 3 (if offered)

### Timeout During Discovery

If discovery takes a long time:
- Device might be offline or unresponsive
- Increase timeout value in Step 1
- Check device power and RS485 connection
- Try discovery again

## Step 3: Device Selection

Select which devices to monitor from the discovered list.

### Selection Process

1. You'll see checkboxes for each discovered device
2. Device format: "Slave X: Device Name"
3. Check the devices you want to monitor
4. Click next/finish to complete configuration

### Examples

**Single Inverter**:
```
☑ Slave 1: Deye Sun 12K
```

**Multiple Inverters**:
```
☑ Slave 1: Deye Sun 12K
☑ Slave 2: Deye Hybrid GW4137
☑ Slave 3: Deye Sun 8K
```

**Selective Monitoring** (only some devices):
```
☑ Slave 1: Deye Sun 12K
☐ Slave 2: Deye Hybrid GW4137
☑ Slave 3: Deye Sun 8K
```

## Configuration Completion

After completing the wizard:

1. Integration creates a config entry
2. Entities are automatically generated
3. Devices appear in **Settings → Devices & Services**
4. Entities start updating (default: every 30 seconds)

## Entity Management

### Automatic Entity Organization

Entities are grouped by device:
- **Settings → Devices & Services → Deye Inverter**
- Each device shows all its sensors and controls
- Entities are named consistently:
  ```
  {entity_type}_{gateway_id}_{slave_id}_{register_name}
  ```

### Entity Categories

| Category | Examples | Purpose |
|----------|----------|---------|
| **Power Sensors** | solar_pv_power, battery_power | Real-time power monitoring |
| **Voltage Sensors** | solar_pv_voltage, grid_voltage | Voltage monitoring |
| **Energy Sensors** | grid_energy | Cumulative energy tracking |
| **Diagnostic** | connection_state, response_time | System health |
| **Binary Sensors** | connection_status | On/off indicators |
| **Controls** | battery_charge_limit | Writable parameters |

## Multi-Gateway Configuration

To add multiple gateways:

1. Repeat the 3-step wizard for each gateway
2. Use different IP addresses for each
3. Each creates a separate config entry
4. Entities are automatically separated by gateway

### Example: 2 Gateways

**Gateway 1** (192.168.1.100):
- Slave 1: Deye Sun 12K
- Slave 2: Deye Hybrid GW4137

**Gateway 2** (192.168.1.101):
- Slave 1: Deye Sun 8K
- Slave 3: Deye Sun 6K

All entities will be properly organized by gateway and device.

## Reconfiguration

To modify an existing configuration:

1. Go to **Settings → Devices & Services**
2. Find the Deye Sun 12K integration
3. Click the three-dot menu
4. Select **Edit**
5. Modify gateway settings
6. Save changes

**Note**: Changing gateway IP requires testing new connection.

## Advanced Configuration (YAML)

While the UI configuration is recommended, you can also configure via YAML in `configuration.yaml`:

```yaml
# Does not override UI configuration
# UI configuration takes precedence
```

Currently, all configuration should be done through the UI. YAML support may be added in future versions.

## Register Mapping

### Deye Sun 12K Standard Registers

| Register | Address | Type | Unit | Scale |
|----------|---------|------|------|-------|
| PV1 Voltage | 0x0100 | uint16 | V | 0.1 |
| PV1 Current | 0x0101 | uint16 | A | 0.01 |
| PV1 Power | 0x0102 | uint16 | W | 1.0 |
| Battery Voltage | 0x0200 | uint16 | V | 0.1 |
| Battery Current | 0x0201 | int16 | A | 0.01 |
| Battery Power | 0x0202 | int16 | W | 1.0 |
| Battery SOC | 0x0203 | uint16 | % | 1.0 |
| Grid Voltage | 0x0300 | uint16 | V | 0.1 |
| Grid Current | 0x0301 | int16 | A | 0.01 |
| Grid Power | 0x0302 | int16 | W | 1.0 |

For a complete register list, see your inverter's Modbus documentation.

## Generic Modbus Device

For unsupported inverter models, use "Generic Modbus":

1. During device selection, if an unknown device is detected
2. Select "Generic Modbus"
3. Manually configure registers:
   - Register address (hex, e.g., 0x0100)
   - Data type: uint16, uint32, int16, int32, float
   - Unit of measurement
   - Scale and offset factors

Example Configuration:
```
Register Name: solar_power
Address: 0x0102
Type: uint16
Unit: W
Scale: 1.0
Offset: 0
```

## Performance Tuning

### Scan Interval

The default scan interval is 30 seconds. To adjust:
- Shorter interval = more frequent updates (increases CPU/network load)
- Longer interval = less frequent updates (reduces responsiveness)
- Recommended: 30-60 seconds

### Request Serialization

The integration automatically serializes Modbus requests to prevent collisions:
- Minimum delay between requests: 100ms
- Per-gateway request queue
- Configurable via Advanced settings (if exposed)

### Connection Pool

Maintains persistent TCP connections:
- Keeps connection open between requests
- Reduces latency
- Automatic reconnection on failure

## Entity Filtering

Home Assistant allows you to customize which entities appear:

1. Go to **Settings → Devices & Services → Deye Inverter**
2. Select individual entities
3. Click the gear icon
4. Choose "Hide from UI" to hide entities
5. Choose "Rename" to customize entity names

## Diagnostics

To download device diagnostics:

1. Go to **Settings → Devices & Services**
2. Find your Deye device
3. Click the menu (three dots)
4. Select **Download Diagnostics**
5. Includes device info, all entities, and error logs

## Troubleshooting Configuration

### "Cannot Connect" Error
- Verify gateway IP and port
- Check firewall allows connection
- Ensure gateway is powered on
- Verify network connectivity

### No Devices Found
- Check RS485 connections
- Verify device slave IDs
- Try manual discovery with different timeout
- Check device firmware version

### Entities Not Updating
- Check device "Connection State" sensor
- Verify device is responsive
- Check network connectivity
- Review error logs

### High Latency
- Check "Response Time" sensor
- Verify RS485 cable quality and length
- Add/check RS485 termination resistors
- Reduce scan interval if experiencing timeouts

## Next Steps

1. View discovered entities in **Settings → Devices & Services**
2. Add entities to your dashboards
3. Create automations based on sensor values
4. Monitor device diagnostics for health status
5. Review [TROUBLESHOOTING.md](TROUBLESHOOTING.md) if issues occur

## Support

For configuration issues:
1. Check this guide completely
2. Review [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
3. Enable debug logging in Home Assistant
4. Check system logs for error messages
       
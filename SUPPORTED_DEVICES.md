# Supported Devices - Waveshare Eth2X Home Assistant Integration

## Supported Inverter Models

This integration supports the following Deye Solar Inverter models and Pytes battery systems natively:

### Deye Sun Series

#### Deye Sun 12K ✅
- **Model**: Sun 12K / Sun 12K-SG04LP3(-EU)
- **Type Code**: 0x0110
- **Features**: 
  - Dual PV inputs (PV1, PV2)
  - Battery management
  - Grid connectivity
  - AC output
- **Firmware**: Compatible with Modbus protocol enabled
- **Status**: Fully supported
- **Registers Supported**: 30+

#### Deye Sun 8K ✅
- **Model**: Sun 8K / Sun 8K-SG04LP3
- **Type Code**: 0x0108
- **Features**:
  - Dual PV inputs (PV1, PV2)
  - Battery management
  - Grid connectivity
  - AC output
- **Firmware**: Compatible with Modbus protocol enabled
- **Status**: Fully supported
- **Notes**: Register mapping same as Sun 12K (power ratings differ)

#### Deye Sun 6K ✅
- **Model**: Sun 6K / Sun 6K-SG04LP1
- **Type Code**: 0x0106
- **Features**:
  - Dual PV inputs (PV1, PV2)
  - Grid connectivity
  - No battery support
  - AC output
- **Firmware**: Compatible with Modbus protocol enabled
- **Status**: Fully supported
- **Notes**: Battery sensors automatically disabled for this model

### Hybrid Inverters

#### Deye Hybrid GW4137 ✅
- **Model**: Hybrid GW4137
- **Type Code**: 0x0200
- **Features**:
  - Dual PV inputs
  - Battery management
  - Grid connectivity
  - AC output (3-phase output available)
- **Firmware**: Compatible with Modbus protocol enabled
- **Status**: Fully supported
- **Registers Supported**: 30+ (Sun 12K set + AC output sensors)

### Battery Systems

#### Pytes E-Box 48100R ✅
- **Model**: E-Box 48100R (48V 100Ah LiFePO4)
- **Type Code**: 0x4810
- **Features**:
  - Battery voltage/current/power monitoring
  - State of charge (SOC)
  - Cell voltage monitoring (min/max/avg)
  - Cell temperature monitoring
  - Charge/discharge status
  - Cycle count tracking
  - Energy counters (charged/discharged)
  - BMS status and fault codes
- **Firmware**: Compatible with Modbus protocol enabled
- **Status**: Fully supported
- **Registers Supported**: 25+

## Unsupported Models (Generic Modbus)

For inverters not listed above, use **Generic Modbus** mode:

### Setup
1. During device configuration, select "Generic Modbus"
2. Manually configure register mappings
3. Specify data types, units, and scale factors

### Known Models (Generic Modbus required)
- Growatt inverters
- SMA inverters
- Sofar inverters
- Fronius inverters
- Other Modbus-compatible inverters

### Supported Data Types
- **uint16**: 0 - 65535 (unsigned 16-bit integer)
- **uint32**: 0 - 4294967295 (unsigned 32-bit integer, 2 registers)
- **int16**: -32768 - 32767 (signed 16-bit integer)
- **int32**: -2147483648 - 2147483647 (signed 32-bit integer, 2 registers)
- **float**: IEEE 754 single precision (2 registers)

## Device Identification

The integration automatically identifies devices using the **Device ID Register** (address 0x000B):

| Register Value | Device Model | Auto-Detection |
|----------------|--------------|-----------------|
| 0x0110 | Deye Sun 12K | ✅ Automatic |
| 0x0108 | Deye Sun 8K | ✅ Automatic |
| 0x0106 | Deye Sun 6K | ✅ Automatic |
| 0x0200 | Deye Hybrid GW4137 | ✅ Automatic |
| 0x4810 | Pytes E-Box 48100R | ✅ Automatic |
| Other | Generic Device | ⚠️ Manual config |

## Register Compatibility

### Deye Sun 12K Registers (30+)

#### Solar PV (Dual Input)
| Register | Address | Type | Unit | Description |
|----------|---------|------|------|-------------|
| PV1 Voltage | 0x0100 | uint16 | V | PV1 input voltage × 0.1 |
| PV1 Current | 0x0101 | uint16 | A | PV1 input current × 0.01 |
| PV1 Power | 0x0102 | uint16 | W | PV1 input power × 1 |
| PV2 Voltage | 0x0110 | uint16 | V | PV2 input voltage × 0.1 |
| PV2 Current | 0x0111 | uint16 | A | PV2 input current × 0.01 |
| PV2 Power | 0x0112 | uint16 | W | PV2 input power × 1 |

#### Battery Management
| Register | Address | Type | Unit | Description |
|----------|---------|------|------|-------------|
| Battery Voltage | 0x0200 | uint16 | V | Battery voltage × 0.1 |
| Battery Current | 0x0201 | int16 | A | Battery current × 0.01 (+ charge, - discharge) |
| Battery Power | 0x0202 | int16 | W | Battery power × 1 (+ charge, - discharge) |
| Battery SOC | 0x0203 | uint16 | % | State of charge × 1 |
| Battery SOH | 0x0204 | uint16 | % | State of health × 1 |
| Battery Temp | 0x0205 | int16 | °C | Battery temperature × 1 |

#### Grid Connection
| Register | Address | Type | Unit | Description |
|----------|---------|------|------|-------------|
| Grid Voltage | 0x0300 | uint16 | V | Grid voltage × 0.1 |
| Grid Current | 0x0301 | int16 | A | Grid current × 0.01 |
| Grid Power | 0x0302 | int16 | W | Grid power × 1 |
| Grid Frequency | 0x0304 | uint16 | Hz | Grid frequency × 0.01 |
| Grid Energy | 0x0308 | uint32 | kWh | Grid energy × 0.1 (combined register pair) |

#### Inverter Status
| Register | Address | Type | Unit | Description |
|----------|---------|------|------|-------------|
| Inverter Temp | 0x0400 | int16 | °C | Inverter temperature × 1 |
| Inverter Status | 0x0401 | uint16 | - | Operating status (bit field) |
| Fault Code | 0x0402 | uint16 | - | Fault code (0 = no fault) |

#### AC Output
| Register | Address | Type | Unit | Description |
|----------|---------|------|------|-------------|
| Output Voltage | 0x0500 | uint16 | V | Output voltage × 0.1 |
| Output Current | 0x0501 | uint16 | A | Output current × 0.01 |
| Output Power | 0x0502 | uint16 | W | Output power × 1 |
| Output Frequency | 0x0504 | uint16 | Hz | Output frequency × 0.01 |

### Deye Sun 6K Specific

- **No Battery Registers**: Battery sensors are disabled for Sun 6K
- **Same Solar/Grid/Inverter**: Uses standard Sun 12K register set
- **All Other Registers**: Compatible with Sun 12K mapping

### Deye Hybrid GW4137 Specific

- **All Sun 12K Registers**: Includes complete Sun 12K register set
- **Additional AC Output**: Extra 3-phase output registers (if equipped)
- **Battery Management**: Enhanced battery features beyond standard Sun 12K

## Firmware Requirements

### Minimum Requirements
- Modbus RTU protocol must be enabled on inverter
- Deye Sun 12K/8K/6K firmware: v1.0.0 or newer
- Deye Hybrid GW4137 firmware: v1.0.0 or newer

### Recommended
- Latest firmware version for your model
- Modbus communications enabled and configured
- RS485 baud rate: 9600 (default)
- Data bits: 8
- Stop bits: 1
- Parity: None
- Slave ID: 1 (or as configured)

### Firmware Updates
Check with Deye for latest firmware updates:
- Improves stability
- May add new registers
- Better Modbus compatibility

## Hardware Requirements

### Modbus Interface
- **Eth2X Device**: Waveshare or compatible converter
- **TCP Port**: 8234 (default, configurable)
- **Baud Rate**: 9600 bps (standard Deye setting)

### Network
- Home Assistant: Must reach gateway via network
- Gateway: Must reach inverter via RS485
- Typical latency: 50-200ms per request

### Power
- Inverter: Must be powered on
- RS485 Gateway: Must be powered on
- Network: Must be stable and connected

## Troubleshooting Device Detection

### Device Not Auto-Detected

**Check**:
1. Device slave ID is correct (typically 1)
2. RS485 wiring is correct
3. Termination resistors are installed
4. Device is powered on and responding
5. Gateway can reach the device

**Solution**:
- Verify slave ID by checking inverter settings
- Test with a Modbus scanner tool
- Check RS485 cable continuity
- Verify baud rate (should be 9600)

### Wrong Device Identified

**Check**:
1. Device ID register (0x000B) reads correctly
2. Firmware version is supported
3. Device type matches actual hardware

**Solution**:
- Check inverter serial number matches purchased model
- Update inverter firmware if available
- Manually select device type if auto-detection incorrect

### Generic Modbus Not Working

**Check**:
1. Register addresses are correct (from documentation)
2. Data types match register format
3. Scale factors are applied correctly
4. Device responds to Modbus requests

**Solution**:
- Verify register addresses in inverter documentation
- Test registers with Modbus scanner first
- Adjust scale factors based on inverter spec
- Check slave ID configuration

## Adding New Device Support

To add support for additional inverter models:

1. **Create Device Class**:
   ```python
   # custom_components/waveshare_eth2x/devices/my_inverter.py
   from .base import BaseDevice, RegisterDef
   
   class MyInverter(BaseDevice):
       def __init__(self, gateway_id, slave_id):
           super().__init__(gateway_id, slave_id)
           self.device_model = "My Inverter"
           self.register_map = {
               "my_register": RegisterDef(
                   address=0x1000,
                   data_type="uint16",
                   unit="W",
                   scale=1.0,
               ),
           }
   ```

2. **Register Device**:
   ```python
   # In custom_components/waveshare_eth2x/devices/registry.py
   DeviceRegistry.register("my_inverter", MyInverter)
   ```

3. **Add to Signatures**:
   ```python
   # In custom_components/waveshare_eth2x/const.py
   DEVICE_SIGNATURES = {
       0x9999: "my_inverter",
   }
   ```

## Getting Help

For device compatibility questions:
1. Check [README.md](README.md) for feature overview
2. Check [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for common issues
3. Enable debug logging to see actual register values
4. Verify device firmware matches Modbus specifications
5. Test device with external Modbus tools first (e.g., QModMaster)

## Contributing Device Support

To contribute support for additional devices:
1. Test device with the integration
2. Document register mapping and data types
3. Create pull request with device class and tests
4. Include device identification signatures
5. Add documentation for the new device

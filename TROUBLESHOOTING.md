# Troubleshooting Guide - Waveshare Eth2X Home Assistant Integration

## Quick Diagnostics

### First Steps
1. Check **Settings → System → Logs** for error messages
2. Enable debug logging (see Enabling Debug Logging below)
3. Check device connection status in entity list
4. Review error counters (if available)

### Common Status Indicators

| Entity | Expected | Issue | Action |
|--------|----------|-------|--------|
| **Connection State** | "healthy" | "degraded"/"error"/"offline" | See Connection Issues |
| **Response Time** | 50-200ms | >2000ms | See Latency Issues |
| **Signal Quality** | >90% | <90% | See Signal Issues |

## Installation Issues

### Integration Not Found After Installation

**Symptoms**: 
- Integration doesn't appear in integration list
- "Waveshare Eth2X" not searchable

**Diagnosis**:
```bash
# SSH into Home Assistant
ls -la /root/.homeassistant/custom_components/waveshare_eth2x/
# Should see __init__.py, config_flow.py, etc.
```

**Solutions**:
1. Verify file permissions (should be readable)
   ```bash
   chmod -R 755 /root/.homeassistant/custom_components/waveshare_eth2x/
   ```

2. Check YAML syntax in manifest.json
   ```bash
   cat /root/.homeassistant/custom_components/waveshare_eth2x/manifest.json
   ```

3. Restart Home Assistant completely
   - Don't just reload, do a full restart

4. Check logs for Python errors
   - **Settings → System → Logs**
- Search for "waveshare_eth2x"

### Dependency Errors

**Error**: `ModuleNotFoundError: No module named 'X'`

**Solution**:
- Most dependencies are built into Home Assistant
- No additional pip packages needed for basic functionality
- Restart Home Assistant after installation

## Configuration Issues

### "Cannot Connect" Error During Setup

**Symptoms**:
- Configuration wizard shows "Cannot connect"
- Error appears on first step (gateway connection)

**Diagnosis Steps**:

1. **Test Network Connectivity**:
   ```bash
   # From Home Assistant shell
   ping <gateway_ip>
   
   # Test TCP port
   nc -zv <gateway_ip> 8234
   ```

2. **Verify IP Address**:
   - Check Waveshare device has power
   - Check it's connected to network (LED indicators)
   - Find IP via router DHCP list

3. **Check Firewall**:
   - Verify port 8234 is open on Home Assistant machine
   - Check router firewall isn't blocking connection
   - Verify Waveshare firewall (if configured)

**Solutions**:

- **Wrong IP Address**:
  - Use router to find correct IP
  - Try hostname instead (e.g., `waveshare.local`)
  - Use static IP for Waveshare device

- **Port Issue**:
  - Verify port 8234 is correct for your device
  - Some devices use port 9000 or other ports
  - Check Waveshare web interface for configured port

- **Network Unreachable**:
  - Verify Home Assistant and Waveshare are on same network
  - Check network segmentation (VLANs, subnets)
  - Restart Waveshare device
  - Check Ethernet connection

- **Timeout**:
  - Increase timeout value (default 10s)
  - Waveshare might be responding slowly
  - Try again - might be temporary

### No Devices Found During Discovery

**Symptoms**:
- Configuration wizard reaches Step 2 (device discovery)
- Shows "No devices found" or "Discovery error"

**Diagnosis**:

1. **Verify RS485 Connections**:
   ```
   Check physical RS485 A/B/GND cables:
   - Connected to inverter RS485 port
   - Connected to Waveshare RS485 port
   - GND (ground) properly connected
   ```

2. **Check Modbus Slave ID**:
   - Typical default: 1
   - Check inverter settings/display
   - Modbus scanner tool can find active slave IDs

3. **Test Device Response**:
   - Power cycle inverter
   - Check inverter display shows normal operation
   - Verify RS485 mode is enabled

**Solutions**:

- **Invalid RS485 Wiring**:
  - Check A/B cable continuity (multimeter)
  - Verify cables aren't swapped (A ↔ B)
  - Add/verify 120Ω termination resistors
  - Check cable shielding is grounded

- **Device Not Responding**:
  - Restart both Waveshare and inverter
  - Check inverter firmware supports Modbus
  - Verify baud rate is 9600
  - Try manual device configuration

- **Wrong Slave ID**:
  - Check inverter Modbus settings
  - Try slave ID 1-10 manually
  - Use Modbus scanner to find correct ID

- **Device Powered Off**:
  - Power on the inverter
  - Check it's in operating mode (not standby)
  - Verify grid connection (some require grid to operate)

### Device Discovery Takes Too Long

**Symptoms**:
- Step 2 is stuck scanning
- Takes >2 minutes to complete

**Causes**:
- Timeout value too long
- Device is slow to respond
- Network latency issues

**Solutions**:
1. Decrease timeout value in Step 1
2. Restart Waveshare device
3. Check network latency:
   ```bash
   ping -c 5 <gateway_ip>
   ```
4. Try discovery again

## Connection Issues

### Connection State Shows "Offline"

**Symptoms**:
- After successful configuration, device shows offline
- Was working, now shows offline
- All entities show "unavailable"

**Diagnosis**:

1. **Check Device Power**:
   - Verify inverter is powered on
   - Check Waveshare has power
   - Look for power indicator LEDs

2. **Check Network**:
   ```bash
   ping <gateway_ip>
   # Should get responses
   ```

3. **Check Modbus**:
   - Verify RS485 cables still connected
   - Check for physical damage
   - Try Modbus scanner to test

**Solutions**:

- **Device Power Lost**:
  - Power on the inverter
  - Wait for startup (2-5 minutes)
  - Integration should recover automatically

- **Network Down**:
  - Check network connectivity
  - Restart router if needed
  - Verify Home Assistant network access

- **RS485 Connection Lost**:
  - Check cable connections
  - Look for loose connectors
  - Test cable continuity

- **Software Issue**:
  - Reload integration: **Settings → Integrations → Menu → Reload**
  - Restart Home Assistant
  - Remove and reconfigure integration

### Connection State Shows "Degraded"

**Symptoms**:
- Device still working but showing "degraded"
- Response time is high
- Signal quality is low (<90%)

**Causes**:
- Intermittent connection failures
- High latency/slow responses
- RS485 signal integrity issues

**Solutions**:

1. **Check Signal Quality** (should be >90%):
   - If <90%: poor RS485 connection
   - Add/verify 120Ω termination resistors
   - Check cable length (<100m recommended)
   - Replace damaged cables

2. **Monitor Response Time**:
   - Typical: 50-200ms
   - If >500ms: connection slow
   - If >2000ms: major issues
   - Check network latency
   - Reduce scan interval to lower load

3. **Check Error Rate**:
   - Monitor error counters
   - If increasing: underlying issues
   - See Error Issues section

4. **Improve Connection**:
   - Reduce cable length if possible
   - Add/upgrade RS485 termination
   - Use better quality RS485 cable
   - Check for electromagnetic interference

### Connection Repeatedly Offline/Online

**Symptoms**:
- Device alternates between online and offline
- Unreliable connection
- Errors logged regularly

**Causes**:
- Intermittent RS485 communication
- Network connectivity issues
- Timeout too short for load

**Solutions**:

1. **Check RS485 Reliability**:
   - Verify termination (120Ω at both ends)
   - Check for loose connectors
   - Look for bent/damaged pins
   - Test with Modbus scanner

2. **Increase Timeout**:
   - Reload integration with longer timeout
   - Default 10s might be too short
   - Try 15-20s for unreliable connections

3. **Reduce Load**:
   - Increase scan interval (30s → 60s)
   - Reduce number of monitored devices
   - Check for other network congestion

4. **Check Inverter**:
   - Restart inverter
   - Check firmware version
   - Look for overheating (temperature)

## Data Issues

### Entities Not Updating

**Symptoms**:
- Entity values stay constant
- Not refreshing from device
- Timestamp not changing

**Diagnosis**:

1. **Check Connection Status**:
   - Look at "Connection State" entity
   - Should be "healthy"
   - If not, see Connection Issues

2. **Check Last Update Time**:
   - Click entity details
   - Check "Last Updated" timestamp
   - Should be recent

3. **Check Logs**:
   - **Settings → System → Logs**
   - Search for error messages
   - Look for timeout errors

**Solutions**:

- **Connection Not Healthy**:
  - Wait 1-2 minutes for recovery
  - Check RS485 connections
  - See Connection Issues section

- **Scan Interval Too Long**:
  - Default is 30 seconds
  - May appear frozen on short observation
  - Reload entity to see latest value

- **Entity Disabled**:
  - Check entity is not hidden
  - Go to entity settings (gear icon)
  - Verify "Not available" not selected

### Incorrect Values

**Symptoms**:
- Entity values seem wrong
- Unrealistic numbers
- Values don't match inverter display

**Diagnosis**:

1. **Check Scale Factors**:
   - Compare with inverter manual
   - Verify register address is correct
   - Check data type (uint16/int16/etc)

2. **Check Device Settings**:
   - Verify slave ID is correct
   - Confirm device type matches
   - Check firmware version

3. **Manual Verification**:
   - Use Modbus scanner to read register
   - Compare raw value with scaled value
   - Check scale factor calculation

**Solutions**:

- **Wrong Scale Factor**:
  - Review register definition
  - Apply correct scale from manual
  - For generic Modbus, adjust scale manually

- **Wrong Register Address**:
  - Verify address in inverter documentation
  - Double-check hex vs decimal
  - Use Modbus scanner to find correct address

- **Wrong Data Type**:
  - Check if register is signed/unsigned
  - Try uint16 vs int16
  - Try uint32 for larger values

- **Device Configuration**:
  - Reload integration with correct device type
  - Remove and reconfigure if needed
  - Try manual device selection

### Zero or Negative Values

**Symptoms**:
- Sensor shows 0 when should have value
- Shows negative when should be positive
- Battery power shows backwards

**Common Causes**:
- Device offline (→ 0)
- Wrong data type (signed vs unsigned)
- Scale factor incorrect
- Register address wrong

**Solutions**:
- See "Incorrect Values" section above
- Check if device is online
- Verify data type (especially for current/power)

## Signal Quality Issues

### Low Signal Quality (<90%)

**Symptoms**:
- "Signal Quality" entity shows <90%
- Frequent connection timeouts
- Intermittent "degraded" state

**Causes**:
- Poor RS485 electrical connection
- Incorrect termination
- Cable quality/length issues
- Electromagnetic interference

**Detailed Fixes**:

1. **Verify Termination**:
   ```
   Required: 120Ω resistor between A and B
   Location: At Waveshare end AND at inverter end
   NOT in middle of line
   
   Test with multimeter:
   - Measure resistance between A-B with power off
   - Should read ~60Ω if dual termination installed
   - Should read ~120Ω if single termination
   ```

2. **Check Cable Quality**:
   - Use twisted pair RS485 cable
   - Shielded preferred for long runs
   - Maximum length: 100m for 9600 baud
   - Check for physical damage

3. **Verify Connections**:
   - All connectors fully seated
   - No bent or broken pins
   - GND (ground) properly connected
   - Test continuity with multimeter

4. **Reduce Interference**:
   - Keep RS485 cable away from power cables
   - Don't run alongside high-voltage lines
   - Check for nearby radio transmitters
   - Shield cable if needed

5. **Check Baud Rate**:
   - Should be 9600 bps on all devices
   - Verify in inverter settings
   - Verify in Waveshare settings

### High Response Times (>500ms)

**Symptoms**:
- "Response Time" sensor shows >500ms
- Occasional timeouts
- Slow data updates

**Causes**:
- Network congestion
- Device slow to respond
- High load on Home Assistant
- Cable/termination issues

**Solutions**:

1. **Check Network**:
   ```bash
   ping -c 10 <gateway_ip>
   # Check for packet loss and latency
   ```

2. **Reduce Load**:
   - Increase scan interval (30s → 60s+)
   - Disable unnecessary entities
   - Reduce number of concurrent requests

3. **Check Device**:
   - Monitor device CPU/temperature
   - Restart device to clear state
   - Check for firmware updates

4. **Improve Connection**:
   - See Signal Quality section above
   - Fix RS485 termination
   - Replace low-quality cables

## Error Counter Issues

### High Error Rate

**Symptoms**:
- Error counters increasing rapidly
- Daily/monthly error counts high
- "Response Time" high

**Diagnosis**:

1. **Check Error Type**:
   - CRC/checksum errors: RS485 connection issue
   - Timeout errors: Device slow or network congestion
   - No-response errors: Device offline
   - Communication errors: Protocol issue

2. **Monitor Success Rate**:
   - Calculate: (Total - Errors) / Total × 100%
   - Should be >95%
   - <90% indicates serious issues

**Solutions**:

- **CRC/Checksum Errors**:
  - Fix RS485 termination
  - Replace damaged cables
  - Check for electromagnetic interference

- **Timeout Errors**:
  - Increase timeout value
  - Reduce scan interval
  - Check device load

- **No-Response Errors**:
  - Verify device power
  - Check RS485 connection
  - Restart device

- **Communication Errors**:
  - Reload integration
  - Check device Modbus settings
  - Verify firmware compatibility

### Resetting Error Counters

**Manual Reset**:
1. Error counters reset automatically:
   - Daily counters at midnight
   - Monthly counters on month boundary
   - Total counter only resets on reload/restart

2. Force Reset (if needed):
   - Reload integration: **Settings → Integrations → Menu → Reload**
   - Or restart Home Assistant

## Debug Logging

### Enabling Debug Logging

Add to `configuration.yaml`:
```yaml
logger:
  logs:
    custom_components.waveshare_eth2x: debug
    custom_components.waveshare_eth2x.core: debug
    custom_components.waveshare_eth2x.coordinators: debug
    custom_components.waveshare_eth2x.health: debug
```

Then:
1. Restart Home Assistant
2. Reproduce the issue
3. Check **Settings → System → Logs**

### Reading Debug Logs

Look for:
- Connection attempts and results
- Register reads and values
- Error messages with timestamps
- State transitions

Example useful entries:
```
Setting up connection to 192.168.1.100:8234
Connected successfully
Reading register: solar_pv1_power
Value: 5432 (raw) → 5432W (scaled)
CRC error on response
Reconnecting after failure
```

### Saving Logs for Analysis

1. Download diagnostics:
   - **Settings → Devices & Services → Select Device → Menu → Download Diagnostics**

2. Or save from web interface:
   - **Settings → System → Logs**
   - Copy full log text
   - Save to file for analysis

## Integration Reload

### When to Reload

Reload the integration if:
- After changing configuration
- To pick up code changes
- When experiencing stuck states
- After updating the integration

### How to Reload

**UI Method**:
1. Go to **Settings → Devices & Services → Integrations**
2. Find "Waveshare Eth2X Gateway"
3. Click the menu (three dots)
4. Select **Reload**

**YAML Method** (if enabled):
1. Add to `configuration.yaml`:
   ```yaml
   homeassistant:
     auto_reload: true
   ```
2. Reload integrations service

### What Reload Does
- Reloads integration code
- Reconnects to gateway
- Rediscoveries devices
- Recreates entities
- Clears cached data

## Contacting Support

Before reaching out:
1. ✅ Review this troubleshooting guide completely
2. ✅ Enable debug logging and check logs
3. ✅ Test network connectivity to gateway
4. ✅ Verify device is online and responding
5. ✅ Check Home Assistant version is supported
6. ✅ Try reloading integration

### Provide When Asking for Help

- Home Assistant version
- Integration version
- Inverter model and firmware
- Error logs (debug output)
- Diagnostic download from integration
- Network diagram (if complex setup)
- Steps to reproduce issue

### Common Resolution

Many issues are resolved by:
1. Restarting the inverter
2. Restarting Waveshare device
3. Reloading the integration
4. Checking RS485 connections
5. Verifying network connectivity
                           
# Home Assistant Recovery and Ring Alarm Integration Guide

## Prerequisites
- A machine (Raspberry Pi, VM, or dedicated server) with Docker installed
- Access to your Home Assistant instance (or ability to reinstall)
- Ring Alarm hardware (Base Station, Contact Sensors, Motion Sensors, Keypad, etc.)
- Ring account credentials (for initial sensor setup)
- Basic knowledge of Docker, YAML, and Home Assistant configuration

## Step 1: Get Home Assistant Running
### Option A: Using Docker (Recommended)
1. Pull the Home Assistant Docker image:
   ```bash
   docker pull ghcr.io/homeassistant/home-assistant:stable
   ```
2. Create a directory for configuration:
   ```bash
   mkdir -p /home/youruser/homeassistant/config
   ```
3. Run Home Assistant:
   ```bash
   docker run -d \
     --name homeassistant \
     --restart=unless-stopped \
     -v /home/youruser/homeassistant/config:/config \
     -e TZ=America/Los_Angeles \
     --network=host \
     ghcr.io/homeassistant/home-assistant:stable
   ```
4. Access HA at `http://<your-ip>:8123` and complete the setup wizard.

### Option B: Using Home Assistant OS (for Raspberry Pi)
1. Download the HAOS image from https://www.home-assistant.io/installation/raspberrypi
2. Flash to SD card using Balena Etcher
3. Boot the Pi and follow on-screen instructions

## Step 2: Basic Configuration
1. Update HA to latest version via Settings > System > Updates
2. Enable Advanced Mode in your user profile
3. Set up backups (Settings > System > Backups)
4. Configure integrations for your existing devices (Z-Wave, Zigbee, MQTT, etc.)

## Step 3: Prepare Ring Integration (Without Paid Service)
### 3.1 Initial Sensor Setup (One-Time)
1. Keep your Ring Base Station powered and connected to internet
2. Use the Ring app to put each sensor into pairing mode and add them to your Ring Alarm system
   - This ensures sensors are registered to the Base Station
3. Verify sensors show as "Online" in the Ring app

### 3.2 Disable Ring Monitoring Service
1. In the Ring app, go to Settings > Alarm Monitoring
2. Cancel or disable professional monitoring (you’ll still get local alerts)
3. Note: You will lose cellular backup and professional response, but local alarms and app notifications remain

### 3.3 Enable Local API Access
1. In Ring app, go to Settings > Account > API Tokens
2. Generate a new token (you’ll need this for HA integration)
3. Enable "Allow access to local API" if available (some firmware versions require this)

## Step 4: Install Ring Integration in Home Assistant
### Using HACS (Recommended)
1. Install HACS if not already present:
   - Open HA > Settings > Devices & Services > Helpers > + > Add Helper
   - Follow HACS installation instructions from https://hacs.xyz/
2. In HACS Frontend:
   - Go to Integrations > Explore & Add Repositories
   - Search for "Ring" or add custom repository: `https://github.com/betterhomeautomation/ring`
   - Install the Ring integration
3. Restart Home Assistant

### Manual Installation (Alternative)
1. Copy the custom component to `<config>/custom_components/ring/`
2. Restart HA

## Step 5: Configure Ring Integration
1. Go to Settings > Devices & Services > + Add Integration
2. Search for "Ring" and select it
3. Enter:
   - Username: Your Ring account email
   - Password: Your Ring account password
   - API Token: The token generated in Step 3.3
   - Scan Interval: 30 seconds (default)
4. Submit and wait for discovery

## Step 6: Expose Ring Sensors as Binary Sensors
After integration loads:
1. Go to Settings > Devices & Services > Ring
3. You should see devices: Base Station, Contact Sensors, Motion Sensors, etc.
4. Enable the entities you want to use in automations (usually all are enabled by default)

## Step 7: Create Local Alarm System in Home Assistant
### 7.1 Create Alarm Control Panel
Add to `configuration.yaml`:
```yaml
alarm_control_panel:
  - platform: manual
    name: Home Alarm
    pending_time: 60
    trigger_time: 120
    disarm_after_trigger: false
    armed_home:
      - delay: 0
    armed_away:
      - delay: 0
    armed_night:
      - delay: 0
```

### 7.2 Automations for Arming/Disarming
Example automation to arm when leaving:
```yaml
alias: Arm Away When Leaving
trigger:
  - platform: state
    entity_id: device_tracker.phone_home
    from: 'home'
    to: 'not_home'
condition:
  - condition: state
    entity_id: alarm_control_panel.home_alarm
    state: 'disarmed'
action:
  - service: alarm_control_panel.alarm_arm_away
    target:
      entity_id: alarm_control_panel.home_alarm
```

### 7.3 Trigger Actions on Sensor Breach
Create automation for when alarm is armed and sensor triggers:
```yaml
alias: Trigger Alarm on Sensor Breach
trigger:
  - platform: state
    entity_id:
      - binary_sensor.front_door_contact
      - binary_sensor.living_room_motion
    to: 'on'
condition:
  - condition: state
    entity_id: alarm_control_panel.home_alarm
    state: ['armed_away', 'armed_home', 'armed_night']
action:
  - service: alarm_control_panel.alarm_trigger
    target:
      entity_id: alarm_control_panel.home_alarm
  - service: notify.mobile_app_phone
    data:
      title: "ALARM TRIGGERED"
      message: "Intrusion detected!"
```

### 7.4 Sirens and Notifications
- Use a siren (Z-Wave/Zigbee) or cast audio via media players
- Add notification actions (mobile app, Telegram, email, etc.)

## Step 8: Optional – Local Only Mode (No Cloud)
If you want to eliminate all Ring cloud dependency:
1. After sensors are paired to Base Station, you can disconnect the Base Station from internet
2. Sensors will still communicate locally with the Base Station (Z-Wave)
3. Use a Ring Alarm Compatible Bridge (e.g., Aeotec Z-Stick) to expose sensors directly to HA as Z-Wave devices
   - This requires putting sensors into Z-Wave pairing mode and adding them to your Z-Wave controller
   - Note: This may void warranty and is more advanced

## Step 9: Testing
1. Arm the alarm via HA or manual control
2. Trigger a sensor (open a door, walk in front of motion)
3. Verify:
   - Alarm triggers in HA
   - Sirens sound (if configured)
   - Notifications sent
   - Alarm can be disarmed via HA

## Step 10: Maintenance
- Regularly check for updates to HA and Ring integration
- Replace sensor batteries as needed (Ring app will show low battery)
- Periodically test the alarm system
- Backup HA configuration weekly

## Troubleshooting
- **Sensors not showing in HA**: Ensure Ring integration is enabled and credentials correct
- **Delayed responses**: Increase scan interval if experiencing rate limits
- **False triggers**: Adjust motion sensor sensitivity in Ring app if available
- **Integration fails after Ring password change**: Re-enter credentials in HA integration

## Conclusion
You now have a fully functional Home Assistant system managing your Ring Alarm sensors without a paid monitoring service. All automations, notifications, and controls are local to your HA instance, giving you flexibility and privacy while retaining use of your existing hardware.

---
*Document created: $(date)*
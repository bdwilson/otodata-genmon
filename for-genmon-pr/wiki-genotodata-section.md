#### genotodata.py (optional)

This program is an addon to genmon that imports data from [Otodata](https://www.otodata.com/) TM5030, TM5040, and TM6030 Bluetooth Low Energy propane tank sensors. The sensor continuously broadcasts its current fill level as a percentage in its BLE advertisement name (e.g., `level: 49.3 % horiz`). The addon reads this advertisement and reports the tank level to genmon via the tank data interface.

**Dependencies:** This addon requires the [bleak](https://github.com/hbldh/bleak) Python library. It is installed automatically by the genmon setup script. A Bluetooth adapter must be present on the system running genmon.

**Configuration**

The configuration file is located at `/etc/genmon/genotodata.conf`. The following settings are available:

| Setting | Default | Description |
|---------|---------|-------------|
| `tank_name` | `Propane Tank` | Display name shown in the genmon web interface |
| `capacity` | `0` | Tank capacity in gallons (0 = not reported) |
| `poll_frequency` | `5` | Minutes between BLE scans |
| `scan_time` | `30` | Seconds to scan for the sensor each poll cycle |
| `mac_address` | *(blank)* | Sensor MAC address — leave blank to use the first Otodata sensor found |

**Bluetooth Setup (Raspberry Pi)**

If you are running genmon on a Raspberry Pi, you may need to enable the Bluetooth serial port adapter. Run the following command and follow the prompts to enable the serial port and disable the serial console. A system restart is required after running this program.

```
sudo python3 /home/pi/genmon/OtherApps/serialconfig.py
```

**Finding Your Sensor MAC Address**

The `mac_address` setting is optional. If left blank the addon uses the first Otodata sensor it detects. If you have neighbours with Otodata sensors nearby, specifying your sensor's MAC address prevents the addon from accidentally reading a neighbour's tank.

To find your sensor's MAC address, run the discovery utility:

```
sudo python3 /home/pi/genmon/OtherApps/otodata_discover.py
```

**No button press is required.** Otodata sensors broadcast their fill level continuously — simply run the utility and your sensor should appear within 30 seconds. If no sensors are found, your sensor may be out of Bluetooth range of your system.

Example output:

```
$ sudo python3 ./otodata_discover.py

NOTE: This program will look for Otodata TM5030, TM5040, and TM6030 propane tank sensors.
      No button press is required. Sensors broadcast their level continuously.

Starting Discovery (30 seconds)...

Finished Discovery. Found 1 sensor(s):

Sensor Address: C1:81:5F:xx:xx:xx
Model:          TM5040
Tank Level:     49.3%


Use the sensor address above as the mac_address parameter in the genotodata addon settings.
If mac_address is left blank, the addon will use the first Otodata sensor it finds.
```

Copy the `Sensor Address` value into the `mac_address` field of `/etc/genmon/genotodata.conf`.

**Tank Configuration**

After enabling the addon in the genmon web interface, configure your tank under **Settings → Tank Data**:

* Set the tank size to match your propane tank's actual capacity in gallons.
* Set the fuel type to **Propane**.

**Notes**

* The genotodata addon supports a single Otodata sensor.
* Each BLE scan takes `scan_time` seconds (default 30 s). Readings are not instantaneous and there is a brief startup delay before the first reading is reported.
* This addon has been tested with the Otodata TM5030, TM5040, and TM6030.

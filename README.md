# otodata-genmon

Monitors an **Otodata TM6030** Bluetooth Low Energy propane tank sensor and
feeds the level into [genmon](https://github.com/jgyates/genmon).

The TM6030 broadcasts its fill level as a percentage in the BLE advertisement
name (e.g. `Otodata level: 72%`).  This addon scans for that advertisement
and forwards the reading to genmon via the `set_tank_data` command, exactly
like the Mopeka addon does.

---

## Manual installation (standalone use)

Use this if you are not submitting a PR to genmon and just want the addon
working on your own system.

### Prerequisites

- genmon installed and running (typically `/home/pi/genmon/`)
- Bluetooth working — verify: `bluetoothctl scan on`
- Python package: `sudo pip3 install bleak`

> **Note:** genmon runs as root (via `startgenmon.sh`), so the bluetooth
> group is not required — root always has access to the BlueZ D-Bus service.

### Steps

```bash
# 1. Copy addon and config template
sudo cp genotodata.py   /home/pi/genmon/addon/
sudo cp genotodata.conf /etc/genmon/

# 2. Edit config (set tank_name, capacity, optional mac_address)
sudo nano /etc/genmon/genotodata.conf

# 3. Add the section below to /etc/genmon/genloader.conf
sudo nano /etc/genmon/genloader.conf
```

Add at the end of `genloader.conf`:

```ini
[genotodata]
module = genotodata.py
enable = True
hardstop = False
conffile = genotodata.conf
args =
priority = 2
postloaddelay = 0
```

```bash
# 4. Install bleak (if not already installed)
sudo pip3 install bleak

# 5. Restart genmon
~/genmon/startgenmon.sh stop
~/genmon/startgenmon.sh start

# 6. Confirm it loaded
tail -f /var/log/genotodata.log
```

### Config options

| Key | Default | Description |
|-----|---------|-------------|
| `tank_name` | `Propane Tank` | Label shown in genmon web UI |
| `capacity` | `0` | Tank size in gallons (0 = omit) |
| `poll_frequency` | `5` | Minutes between BLE scan cycles |
| `scan_time` | `30` | Seconds to listen per scan cycle |
| `mac_address` | *(blank)* | Filter to one specific sensor MAC; blank = first Otodata device found |

---

## Contributing this addon upstream to jgyates/genmon

The following section documents every change required to include this addon
in the official genmon repository so it appears in the web Add-On GUI and is
installed automatically.

### Files to add

| File in genmon repo | Source in this repo |
|---------------------|---------------------|
| `addon/genotodata.py` | `genotodata.py` |
| `conf/genotodata.conf` | `genotodata.conf` |

### Files to modify

#### `conf/genloader.conf` — add section

```ini
[genotodata]
module = genotodata.py
enable = False
hardstop = False
conffile = genotodata.conf
args =
priority = 2
```

#### `requirements.txt` — add dependency

```
bleak
```

Place it near the `bleson` line for grouping.

#### `genserv.py` — register in `GetAddOns()`

Find the block that defines `AddOnCfg["genmopeka"]` and add the following
**immediately after** it.  Also add the `GENOTODATA_CONFIG` constant near the
other `GEN*_CONFIG` constants at the top of the file (follow the same pattern
as `GENMOPEKA_CONFIG`).

**Constant to add near the top of genserv.py:**

```python
GENOTODATA_CONFIG = os.path.join(ConfigPath, "genotodata.conf")
```

Also add it to the `ConfigFiles` dict where the other addon configs are loaded:

```python
ConfigFiles[GENOTODATA_CONFIG] = MyConfig(
    filename=GENOTODATA_CONFIG, section="genotodata", log=log
)
```

**`GetAddOns()` block to add (after the genmopeka block):**

```python
# GENOTODATA
if sys.version_info >= (3, 7):
    Description = "Support Otodata TM6030 Propane Tank Sensor"
    try:
        import bleak
    except Exception as e1:
        Description = (
            Description
            + "<br/><font color='red'>The required libraries for this add on "
            "are not installed, please run the installation script.</font>"
        )

    AddOnCfg["genotodata"] = collections.OrderedDict()
    AddOnCfg["genotodata"]["enable"] = ConfigFiles[GENLOADER_CONFIG].ReadValue(
        "enable", return_type=bool, section="genotodata", default=False
    )
    AddOnCfg["genotodata"]["title"] = "Otodata TM6030 Propane Tank Sensor"
    AddOnCfg["genotodata"]["description"] = Description
    AddOnCfg["genotodata"]["icon"] = "otodata"
    AddOnCfg["genotodata"]["url"] = (
        "https://github.com/jgyates/genmon/wiki/"
        "1----Software-Overview#genototadatapy-optional"
    )
    AddOnCfg["genotodata"]["parameters"] = collections.OrderedDict()

    AddOnCfg["genotodata"]["parameters"]["tank_name"] = CreateAddOnParam(
        ConfigFiles[GENOTODATA_CONFIG].ReadValue(
            "tank_name", return_type=str, default="Propane Tank"
        ),
        "string",
        "Display name for this tank in the genmon web interface.",
        bounds="",
        display_name="Tank Name",
    )
    AddOnCfg["genotodata"]["parameters"]["capacity"] = CreateAddOnParam(
        ConfigFiles[GENOTODATA_CONFIG].ReadValue(
            "capacity", return_type=int, default=0
        ),
        "int",
        "Tank capacity in gallons. Set to 0 to omit from genmon data.",
        bounds="number",
        display_name="Tank Capacity (gallons)",
    )
    AddOnCfg["genotodata"]["parameters"]["poll_frequency"] = CreateAddOnParam(
        ConfigFiles[GENOTODATA_CONFIG].ReadValue(
            "poll_frequency", return_type=int, default=5
        ),
        "int",
        "The time in minutes between BLE scan cycles. Default is 5 minutes.",
        bounds="number",
        display_name="Poll Interval (minutes)",
    )
    AddOnCfg["genotodata"]["parameters"]["scan_time"] = CreateAddOnParam(
        ConfigFiles[GENOTODATA_CONFIG].ReadValue(
            "scan_time", return_type=float, default=30.0
        ),
        "float",
        "Seconds to listen for BLE advertisements per scan cycle. "
        "Increase if the sensor is far from the Pi.",
        bounds="number",
        display_name="Scan Duration (seconds)",
    )
    AddOnCfg["genotodata"]["parameters"]["mac_address"] = CreateAddOnParam(
        ConfigFiles[GENOTODATA_CONFIG].ReadValue(
            "mac_address", return_type=str, default=""
        ),
        "string",
        "Optional: restrict readings to a specific sensor by Bluetooth MAC address "
        "(e.g. aa:bb:cc:dd:ee:ff). Leave blank to use the first Otodata device found.",
        bounds="",
        display_name="Sensor MAC Address",
    )
```

### About the icon

The `icon` field references a web asset served by genmon's Flask app.  Either:
- Reuse an existing icon (e.g. change `"otodata"` to `"mopeka"` as a temporary
  placeholder), or
- Add an SVG/PNG icon named `otodata` to the genmon web assets directory and
  reference it in `genserv.py`.

### PR description template

> **Add Otodata TM6030 BLE propane tank sensor addon (`genotodata`)**
>
> The Otodata TM6030 is a Bluetooth Low Energy sensor that straps to a
> standard propane tank and broadcasts the fill level as a percentage in its
> BLE advertisement name.  This addon scans for that advertisement and
> forwards the reading to genmon via `set_tank_data`, displaying it alongside
> generator fuel data in the web UI.
>
> **Changes:**
> - `addon/genotodata.py` — new addon script using `bleak` for BLE scanning
> - `conf/genotodata.conf` — configuration template
> - `conf/genloader.conf` — add disabled-by-default `[genotodata]` section
> - `requirements.txt` — add `bleak`
> - `genserv.py` — register addon in `GetAddOns()` for web UI toggle support
>
> **Similar to:** `genmopeka.py` (also a BLE propane tank sensor addon).
> The main difference is that the Otodata sensor broadcasts level as a plain
> percentage in the advertisement name, so no tank geometry calculations are
> needed and the `fluids` dependency is not required.
>
> **Tested on:** Raspberry Pi 4, Raspberry Pi OS Bookworm, Python 3.11,
> bleak 0.21, Otodata TM6030.

---

## Standalone fallback (`otodata_receiver.py`)

`otodata_receiver.py` and `otodata.service` are a self-contained script +
systemd service kept for cases where genmon is not available.  Edit the
configuration block at the top of the script, then:

```bash
sudo cp otodata.service /etc/systemd/system/
sudo systemctl enable --now otodata
sudo journalctl -u otodata -f
```

---

Bugs / contact: [@brianwilson](http://twitter.com/brianwilson) or
[email](http://cronological.com/comment.php?ref=bubba).

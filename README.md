# otodata-genmon

Monitors an **Otodata TM6030** BLE propane tank sensor and feeds the level
into [genmon](https://github.com/jgyates/genmon) (and optionally
[Hubitat](https://github.com/bdwilson/hubitat/tree/master/Otodata-Propane)).

---

## Option 1 — Native genmon addon (recommended)

`genotodata.py` integrates directly with genmon's addon loader. Configuration
lives in a plain INI file; no source code editing required.

### Prerequisites

- genmon installed and running (typically `/home/pi/genmon/`)
- Bluetooth working and the TM6030 visible (`bluetoothctl scan on`)
- Python package: `pip3 install bleak`
- User running genmon must be in the `bluetooth` group:
  `sudo usermod -aG bluetooth pi` (then log out / back in)

### Installation

```bash
# 1. Copy the addon and config template
sudo cp genotodata.py  /home/pi/genmon/addon/
sudo cp genotodata.conf /etc/genmon/

# 2. Edit the config — at minimum set tank_name and capacity
sudo nano /etc/genmon/genotodata.conf

# 3. Register the addon with genmon's loader
sudo nano /etc/genmon/genloader.conf
```

Add the following block to `genloader.conf` (after the last existing entry):

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
# 4. Restart genmon to pick up the new addon
sudo systemctl restart genmon
```

Logs appear alongside other genmon addon logs:
```bash
sudo journalctl -u genmon -f
```

### Config options (`/etc/genmon/genotodata.conf`)

| Key | Default | Description |
|-----|---------|-------------|
| `tank_name` | `Propane Tank` | Label shown in the genmon web UI |
| `capacity` | `0` | Tank size in gallons (0 = omit) |
| `poll_frequency` | `5` | Minutes between BLE scan cycles |
| `scan_time` | `30` | Seconds to listen per scan |
| `mac_address` | *(blank)* | Filter to a specific sensor MAC address |
| `do_hubitat` | `False` | Enable Hubitat push |
| `hubitat_url` | — | Hubitat Maker API update URL |
| `hubitat_key` | — | Hubitat OAuth access token |

---

## Option 2 — Standalone script (no genmon required)

`otodata_receiver.py` is a self-contained script with a matching systemd
service. It is useful if you only want Hubitat integration or are running
genmon on a separate host.

### Setup

1. Verify Bluetooth can see the sensor:
   ```bash
   sudo hcitool lescan --duplicates
   ```
2. Edit the configuration block at the top of `otodata_receiver.py`.
3. Allow `hcitool` without a password:
   ```
   # /etc/sudoers
   pi ALL = NOPASSWD: /usr/bin/hcitool
   ```
4. Install and start the systemd service:
   ```bash
   sudo cp otodata.service /etc/systemd/system/
   sudo systemctl enable --now otodata
   sudo journalctl -u otodata -f
   ```

---

## Hubitat setup

Install the Hubitat app and driver from
<https://github.com/bdwilson/hubitat/tree/master/Otodata-Propane>.

1. Import and install the **app** (enable OAuth).
2. Import and install the **driver**.
3. Create a virtual device using that driver.
4. Open the user app, select the virtual device, and copy the generated URL
   and access token into the config.

---

Bugs / contact: [@brianwilson](http://twitter.com/brianwilson) or
[email](http://cronological.com/comment.php?ref=bubba).

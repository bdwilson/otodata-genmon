# otodata-genmon

Monitors an **Otodata TM6030** BLE propane tank sensor and feeds the level
into [genmon](https://github.com/jgyates/genmon).

---

## Installation — native genmon addon

`genotodata.py` integrates directly with genmon's addon loader (`genloader`).
Configuration lives in a plain INI file; no source code editing required.

### Prerequisites

- genmon installed and running (typically `/home/pi/genmon/`)
- Bluetooth working and the TM6030 visible:
  ```bash
  bluetoothctl scan on
  ```
- Python package: `pip3 install bleak`
- User running genmon must be in the `bluetooth` group:
  ```bash
  sudo usermod -aG bluetooth pi   # log out and back in after
  ```

### Steps

```bash
# 1. Copy addon and config template into place
sudo cp genotodata.py   /home/pi/genmon/addon/
sudo cp genotodata.conf /etc/genmon/

# 2. Edit the config (tank name, capacity, optional MAC filter)
sudo nano /etc/genmon/genotodata.conf

# 3. Register with genmon's addon loader
sudo nano /etc/genmon/genloader.conf
```

Add this block anywhere in `genloader.conf` (after the last existing section):

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
# 4. Restart genmon
sudo systemctl restart genmon

# 5. Verify it's running
sudo journalctl -u genmon -f
```

### Config options (`/etc/genmon/genotodata.conf`)

| Key | Default | Description |
|-----|---------|-------------|
| `tank_name` | `Propane Tank` | Label shown in the genmon web UI |
| `capacity` | `0` | Tank size in gallons (0 = omit) |
| `poll_frequency` | `5` | Minutes between BLE scan cycles |
| `scan_time` | `30` | Seconds to listen per scan cycle |
| `mac_address` | *(blank)* | Filter to a specific sensor MAC; blank = first Otodata device found |

### A note on the genmon Add-On web GUI

genmon's Add-On page only shows addons that are hardcoded into `genserv.py`'s
`GetAddOns()` function — there is no auto-discovery.  The addon works fine
when enabled via `genloader.conf`, but it will **not** appear as a toggle in
the web UI unless this project is merged upstream into
[jgyates/genmon](https://github.com/jgyates/genmon).  If that interests you,
the genmon maintainer accepts pull requests for new addons.

---

## Standalone fallback (`otodata_receiver.py`)

A self-contained script with a systemd service is kept in this repo for
cases where genmon is not installed or is running on a different host.
Edit the configuration block at the top of `otodata_receiver.py`, then:

```bash
sudo cp otodata.service /etc/systemd/system/
sudo systemctl enable --now otodata
sudo journalctl -u otodata -f
```

---

Bugs / contact: [@brianwilson](http://twitter.com/brianwilson) or
[email](http://cronological.com/comment.php?ref=bubba).

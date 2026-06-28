#### genhubitat.py (optional)

This program is an addon to genmon that exposes a REST and WebSocket API so that a [Hubitat Elevation](https://hubitat.com/) hub can natively integrate with your generator — no MQTT broker or separate server required. The Hubitat integration driver polls genmon for current status and receives real-time push updates over WebSocket whenever values change.

The Hubitat driver and instructions for installing it on the Hubitat side are available at:
**https://github.com/bdwilson/hubitat/tree/master/Genmon**

**Dependencies:** This addon requires the [aiohttp](https://docs.aiohttp.org/) Python library. Install it with:

```
sudo pip3 install aiohttp
```

**Configuration**

The configuration file is located at `/etc/genmon/genhubitat.conf`. The following settings are available:

| Setting | Default | Description |
|---------|---------|-------------|
| `port` | `9084` | Port the REST/WebSocket API server listens on |
| `api_key` | *(auto-generated)* | Bearer token for authentication — leave blank; genmon generates one automatically on first enable |
| `poll_interval` | `3` | Seconds between genmon data polls |
| `blacklist` | `Tiles` | Comma-separated keywords — any data path containing a keyword (case-insensitive) is excluded from the API response |
| `include_monitor_stats` | `True` | Include monitor/platform statistics (CPU temperature, WiFi signal, memory) |
| `include_weather` | `True` | Include weather data when available |
| `use_https` | `True` | Enable HTTPS — a self-signed TLS certificate is generated automatically |
| `debug` | `False` | Enable verbose debug logging |

**Enabling the Addon**

Enable genhubitat in the genmon web interface under **Add-Ons**. On first enable, genmon automatically generates a unique API key and writes it to `genhubitat.conf`. The API key is displayed in the Add-Ons settings page — copy it for use when configuring the Hubitat driver.

**API Endpoints**

The addon exposes the following endpoints. All endpoints except `/api/health` require a `Bearer` token in the `Authorization` header matching the configured API key.

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/health` | Health check — returns `{"status": "ok"}` (no auth required) |
| `GET` | `/api/info` | Generator start info (model, serial, controller type, capabilities) |
| `GET` | `/api/status` | Current generator state and all sensor values |
| `GET` | `/api/entities` | Entity definitions for all sensors, binary sensors, buttons, switches, and selects |
| `POST` | `/api/command` | Send a command to genmon (e.g. `{"command": "start"}`) |
| `GET` | `/ws` | WebSocket connection — authenticate via first message, then receive real-time state updates |

**WebSocket Protocol**

Connect to `wss://<host>:<port>/ws` (or `ws://` if HTTPS is disabled). Authenticate by sending a JSON message as the first frame:

```json
{"type": "auth", "token": "<api_key>"}
```

On success the server responds with `{"type": "auth_ok"}` followed immediately by a full state snapshot (`{"type": "full_state", ...}`). Subsequently the server pushes `{"type": "state_update", ...}` messages whenever genmon values change.

**HTTPS / TLS**

When `use_https = True` (the default) the addon generates a self-signed certificate on first run and stores it alongside the addon file. Because the certificate is self-signed, the Hubitat driver must be configured to accept it — see the driver documentation at the link above.

To disable HTTPS set `use_https = False` in `genhubitat.conf` and restart genmon.

**Port Conflicts**

If you run both genhubitat and genhalink simultaneously, ensure they use different ports. The default ports are:

* genhubitat: `9084`
* genhalink: `9083`

**Configuring the Hubitat Driver**

After enabling the addon:

1. Install the Hubitat driver from **https://github.com/bdwilson/hubitat/tree/master/Genmon** following the instructions there.
2. Enter the IP address of your genmon system, the port (default `9084`), and the API key shown in the genmon Add-Ons settings page.
3. The driver will connect, download the entity list, and begin receiving live generator data.

**Notes**

* The addon requires genmon to be reachable on its standard port (`9082`) to retrieve generator data.
* Sensor, binary sensor, button, switch, select, and number entities are automatically created based on the generator controller type detected at startup.
* The `blacklist` setting is useful for suppressing high-volume or unneeded data paths. The default excludes `Tiles` data.

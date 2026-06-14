#!/usr/bin/env python3
"""
genotodata.py - Genmon addon for the Otodata TM6030 BLE propane tank sensor.

Installation:
  cp genotodata.py   /home/pi/genmon/addon/
  cp genotodata.conf /etc/genmon/

Add to /etc/genmon/genloader.conf:

  [genotodata]
  module = genotodata.py
  enable = True
  hardstop = False
  conffile = genotodata.conf
  args =
  priority = 2
  postloaddelay = 0

  Then restart genmon: sudo systemctl restart genmon

Dependency: pip3 install bleak
User running genmon must be in the bluetooth group: sudo usermod -aG bluetooth pi
"""

import asyncio
import json
import os
import re
import signal
import sys
import threading
import time

try:
    from bleak import BleakScanner
except ImportError:
    print("bleak not found. Run: pip3 install bleak", flush=True)
    sys.exit(1)

try:
    from genmonlib.myclient import ClientInterface
    from genmonlib.myconfig import MyConfig
    from genmonlib.mysupport import MySupport
except ImportError:
    print("genmonlib not found. Ensure this script runs inside a genmon installation.", flush=True)
    sys.exit(1)

# ------------------------------------------------------------------
LEVEL_REGEX = re.compile(r"level:\s*([0-9]+(?:\.[0-9]+)?)\s*%", re.IGNORECASE)


class GenOtodata(MySupport):

    def __init__(
        self,
        log=None,
        loglocation=None,
        ConfigFilePath=None,
        host="localhost",
        port=9082,
        console=None,
    ):
        super(GenOtodata, self).__init__()

        self.log = log
        self.console = console
        self.running = True
        self.current_level = None

        conf_path = os.path.join(
            ConfigFilePath if ConfigFilePath else "/etc/genmon/",
            "genotodata.conf",
        )
        self.config = MyConfig(filename=conf_path, section="genotodata", log=self.log)

        self.tank_name      = self.config.ReadValue("tank_name",      return_type=str,   default="Propane Tank")
        self.capacity       = self.config.ReadValue("capacity",       return_type=int,   default=0)
        self.poll_frequency = self.config.ReadValue("poll_frequency", return_type=int,   default=5)
        self.scan_time      = self.config.ReadValue("scan_time",      return_type=float, default=30.0)
        self.mac_address    = self.config.ReadValue("mac_address",    return_type=str,   default="").strip().lower()

        try:
            self.generator = ClientInterface(host=host, port=port, log=self.log)
        except Exception as e:
            self._log_error(f"Cannot connect to genmon at {host}:{port}: {e}")
            self.generator = None

        signal.signal(signal.SIGTERM, self._on_signal)
        signal.signal(signal.SIGINT, self._on_signal)

        self._poll_thread = threading.Thread(
            target=self._poll_loop, daemon=True, name="GenOtodataPoll"
        )
        self._poll_thread.start()
        self._log_info("GenOtodata started.")

    # ------------------------------------------------------------------
    # Logging helpers (MySupport logging requires self.log to be set)
    # ------------------------------------------------------------------

    def _log_info(self, msg):
        if self.log:
            self.log.info(msg)
        if self.console:
            self.console.info(msg)

    def _log_error(self, msg):
        if self.log:
            self.log.error(msg)
        if self.console:
            self.console.error(msg)

    # ------------------------------------------------------------------
    # BLE scanning via bleak
    # ------------------------------------------------------------------

    async def _ble_scan_async(self):
        """Scan for scan_time seconds; return (address, level) or (None, None)."""
        result = {}

        def _callback(device, adv_data):
            name = device.name or (adv_data.local_name if adv_data else "") or ""
            m = LEVEL_REGEX.search(name)
            if not m:
                return
            addr = device.address.lower()
            if self.mac_address and addr != self.mac_address:
                return
            result["addr"] = device.address
            result["level"] = float(m.group(1))

        scanner = BleakScanner(detection_callback=_callback)
        await scanner.start()
        await asyncio.sleep(self.scan_time)
        await scanner.stop()

        return result.get("addr"), result.get("level")

    def _ble_scan(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(self._ble_scan_async())
        except Exception as e:
            self._log_error(f"BLE scan error: {e}")
            return None, None
        finally:
            loop.close()

    # ------------------------------------------------------------------
    # Send to genmon
    # ------------------------------------------------------------------

    def _send_genmon(self, level):
        if self.generator is None:
            return
        data = {"Tank Name": self.tank_name, "Percentage": level}
        if self.capacity > 0:
            data["Capacity"] = self.capacity
        cmd = f"generator: set_tank_data={json.dumps(data)}"
        try:
            result = self.generator.ProcessMonitorCommand(cmd)
            self._log_info(f"genmon updated: {level}% -> {result}")
        except Exception as e:
            self._log_error(f"genmon send failed: {e}")

    # ------------------------------------------------------------------
    # Main poll loop
    # ------------------------------------------------------------------

    def _poll_loop(self):
        while self.running:
            self._log_info(
                f"Scanning for Otodata TM6030 ({self.scan_time:.0f}s)…"
            )
            addr, level = self._ble_scan()

            if level is not None:
                self._log_info(f"Sensor [{addr}]: {level}%")
                if level != self.current_level:
                    self.current_level = level
                    self._send_genmon(level)
                else:
                    self._log_info("Level unchanged, skipping send.")
            else:
                self._log_error(
                    "Otodata sensor not found. Check Bluetooth and sensor proximity."
                )

            # Sleep poll_frequency minutes, waking each second to check running flag.
            for _ in range(self.poll_frequency * 60):
                if not self.running:
                    return
                time.sleep(1)

    # ------------------------------------------------------------------

    def _on_signal(self, signum, frame):
        self.running = False

    def Close(self):
        self.running = False
        if getattr(self, "generator", None):
            try:
                self.generator.Close()
            except Exception:
                pass


# ------------------------------------------------------------------
if __name__ == "__main__":
    (console, ConfigFilePath, address, port, loglocation, log) = (
        MySupport.SetupAddOnProgram("genotodata")
    )

    instance = GenOtodata(
        log=log,
        loglocation=loglocation,
        ConfigFilePath=ConfigFilePath,
        host=address,
        port=port,
        console=console,
    )

    while instance.running:
        time.sleep(0.5)

    instance.Close()
    sys.exit(0)

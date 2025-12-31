#!/usr/bin/env python3

import subprocess
import sys
import re
import urllib.request
import datetime

#
# ---- USER SETTINGS ----
#

DEBUG = False

# do you have genmon running locally?
DO_GENMON = True

# do you want to send data to Hubitat?
DO_HUBITAT = True

# tank capacity
CAPACITY = "320"

# Hubitat Maker API app
# https://github.com/bdwilson/hubitat/tree/master/Otodata-Propane
HUBITAT_URL = "http://192.168.1.xx/apps/api/xxx/update/"
HUBITAT_KEY = "0940aac2-355b-xxxxx-xxxxxx-xxxxx-xxxx"

# Genmon client interface path
GENMON_CLIENT = "/home/pi/genmon/ClientInterface.py"

#
# ---- INTERNALS BELOW HERE ----
#

LEVEL_REGEX = re.compile(
    r"level:\s*([0-9]+(?:\.[0-9]+)?)\s*%",  # e.g. 80 or 80.8
    re.IGNORECASE,
)

old_level = None


def debug(msg):
    if DEBUG:
        print(msg, flush=True)


def send_to_hubitat(level):
    url = f"{HUBITAT_URL}{level}?access_token={HUBITAT_KEY}"
    debug(f"HUBITAT: {url}")

    try:
        with urllib.request.urlopen(url, timeout=10) as resp:
            data = resp.read().decode("utf-8", errors="ignore")
            debug(f"RETURN: {data}")
    except Exception as e:
        debug(f"HUBITAT ERROR: {e}")


def send_to_genmon(level):
    payload = (
        f"generator: set_tank_data={{"
        f"\"Tank Name\": \"External Tank\", "
        f"\"Capacity\": {CAPACITY}, "
        f"\"Percentage\": {level}"
        f"}}"
    )

    debug(f"DATA: {payload}")

    try:
        proc = subprocess.Popen(
            ["python3", GENMON_CLIENT],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )

        out, _ = proc.communicate(payload + "\n", timeout=10)

        for line in out.splitlines():
            debug(f"GENMON: {line}")

    except Exception as e:
        debug(f"GENMON ERROR: {e}")


def main():
    global old_level

    debug("Starting BLE scan…")

    # IMPORTANT: full path avoids PATH issues under systemd/sudo
    proc = subprocess.Popen(
        ["/usr/bin/hcitool", "lescan", "--duplicates"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )

    for line in proc.stdout:
        debug(f"RAW: {repr(line)}")

        line = line.strip()

        m = LEVEL_REGEX.search(line)
        if not m:
            if "error" in line.lower():
                debug(f"Error from hcitool: {line}")
            continue

        level = m.group(1)
        debug(f"OTODATA: Level {level}")

        if old_level == level:
            continue

        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        debug(f"Date: {timestamp} Level: {level}")

        if DO_GENMON:
            send_to_genmon(level)

        if DO_HUBITAT:
            send_to_hubitat(level)

        old_level = level


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nExiting.", flush=True)
        sys.exit(0)
    except Exception as e:
        print(f"CRASHED WITH: {e}", flush=True)
        sys.exit(1)

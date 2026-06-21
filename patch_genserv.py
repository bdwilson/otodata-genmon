#!/usr/bin/env python3
"""
patch_genserv.py - Insert the genotodata addon into genserv.py.

Usage:
    python3 patch_genserv.py /path/to/genmon/genserv.py

The script is idempotent: it will not apply the patch a second time if
genotodata is already present.
"""

import re
import sys

# ---------------------------------------------------------------------------
# The three blocks to insert
# ---------------------------------------------------------------------------

CONST_LINE = 'GENOTODATA_CONFIG = os.path.join(ConfigPath, "genotodata.conf")\n'

CONFIGFILES_LINE = (
    'ConfigFiles[GENOTODATA_CONFIG] = MyConfig(\n'
    '    filename=GENOTODATA_CONFIG, section="genotodata", log=log\n'
    ')\n'
)

ADDON_BLOCK = '''
# GENOTODATA
if sys.version_info >= (3, 7):
    Description = "Support Otodata TM6030 Propane Tank Sensor"
    try:
        import bleak
    except Exception as e1:
        Description = (
            Description
            + "<br/><font color=\\'red\\'>The required libraries for this add on "
            "are not installed, please run the installation script.</font>"
        )

    AddOnCfg["genotodata"] = collections.OrderedDict()
    AddOnCfg["genotodata"]["enable"] = ConfigFiles[GENLOADER_CONFIG].ReadValue(
        "enable", return_type=bool, section="genotodata", default=False
    )
    AddOnCfg["genotodata"]["title"] = "Otodata TM6030 Propane Tank Sensor"
    AddOnCfg["genotodata"]["description"] = Description
    AddOnCfg["genotodata"]["icon"] = "mopeka"
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
        "Optional: restrict readings to a specific sensor MAC address "
        "(e.g. aa:bb:cc:dd:ee:ff). Leave blank to use the first Otodata device found.",
        bounds="",
        display_name="Sensor MAC Address",
    )

'''

# ---------------------------------------------------------------------------

def find_line_ending_with(lines, suffix, start=0):
    """Return index of first line (>= start) whose stripped content ends with suffix."""
    for i in range(start, len(lines)):
        if lines[i].rstrip().endswith(suffix):
            return i
    return -1


def patch(path):
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    if "genotodata" in content:
        print("genotodata already present in genserv.py — nothing to do.")
        return

    lines = content.splitlines(keepends=True)

    # ------------------------------------------------------------------
    # 1. Insert GENOTODATA_CONFIG constant after GENMOPEKA_CONFIG
    # ------------------------------------------------------------------
    idx = find_line_ending_with(lines, '"genmopeka.conf")')
    if idx == -1:
        # Try alternate pattern without trailing )
        for i, l in enumerate(lines):
            if "GENMOPEKA_CONFIG" in l and "genmopeka.conf" in l:
                idx = i
                break
    if idx == -1:
        print("ERROR: Could not find GENMOPEKA_CONFIG constant. Check genserv.py manually.")
        sys.exit(1)
    lines.insert(idx + 1, CONST_LINE)
    print(f"[1/3] Inserted GENOTODATA_CONFIG constant after line {idx + 1}.")

    # ------------------------------------------------------------------
    # 2. Insert ConfigFiles[GENOTODATA_CONFIG] after ConfigFiles[GENMOPEKA_CONFIG]
    # ------------------------------------------------------------------
    # Re-search because we just inserted a line
    for i, l in enumerate(lines):
        if "ConfigFiles[GENMOPEKA_CONFIG]" in l and "MyConfig" in l:
            # Find the end of this (possibly multi-line) statement
            end = i
            while end < len(lines) - 1 and not lines[end].rstrip().endswith(")"):
                end += 1
            lines.insert(end + 1, "\n")
            lines.insert(end + 2, CONFIGFILES_LINE)
            print(f"[2/3] Inserted ConfigFiles[GENOTODATA_CONFIG] after line {end + 1}.")
            break
    else:
        print("ERROR: Could not find ConfigFiles[GENMOPEKA_CONFIG]. Check genserv.py manually.")
        sys.exit(1)

    # ------------------------------------------------------------------
    # 3. Insert AddOnCfg["genotodata"] block after genmopeka block ends
    # ------------------------------------------------------------------
    # The genmopeka block is the last AddOnCfg["genmopeka"] assignment.
    last_mopeka = -1
    for i, l in enumerate(lines):
        if 'AddOnCfg["genmopeka"]' in l:
            last_mopeka = i

    if last_mopeka == -1:
        print('ERROR: Could not find AddOnCfg["genmopeka"]. Check genserv.py manually.')
        sys.exit(1)

    # Walk forward to the end of the genmopeka block (next blank line or
    # next comment block that starts a new addon section).
    end = last_mopeka
    while end < len(lines) - 1:
        end += 1
        stripped = lines[end].strip()
        # A new addon section starts with a comment like "# GENSOMETHING"
        if stripped.startswith("# GEN") and stripped.isupper():
            break
        # Or the end of the if-block dedents back to column 0 with a blank line
        if stripped == "" and end + 1 < len(lines):
            next_stripped = lines[end + 1].strip()
            if next_stripped.startswith("# GEN") or next_stripped == "":
                break

    lines.insert(end, ADDON_BLOCK)
    print(f"[3/3] Inserted AddOnCfg['genotodata'] block after line {end}.")

    # ------------------------------------------------------------------
    # Write patched file
    # ------------------------------------------------------------------
    with open(path, "w", encoding="utf-8") as f:
        f.writelines(lines)

    print(f"\nDone. Patched {path}")
    print("Verify with: grep -n genotodata " + path)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(1)
    patch(sys.argv[1])

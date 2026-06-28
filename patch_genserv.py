#!/usr/bin/env python3
"""
patch_genserv.py - Insert the genotodata addon into genserv.py.

Usage (run from inside your genmon fork directory):
    python3 /path/to/otodata-genmon/patch_genserv.py genserv.py

The script is idempotent: it will not apply the patch a second time if
genotodata is already present.

After running, verify with:
    grep -n genotodata genserv.py
"""

import sys


def leading_spaces(line):
    """Return the leading whitespace of a line as a string."""
    return line[: len(line) - len(line.lstrip())]


def addon_block(indent):
    """Return the full AddOnCfg['genotodata'] block at the given indent level."""
    i = indent  # e.g. "    "
    i2 = i + "    "
    i3 = i2 + "    "
    return (
        f"\n"
        f"{i}# GENOTODATA\n"
        f"{i}if sys.version_info >= (3, 7):\n"
        f'{i2}Description = "Support Otodata TM6030 Propane Tank Sensor"\n'
        f"{i2}try:\n"
        f"{i3}import bleak\n"
        f"{i2}except Exception as e1:\n"
        f"{i3}Description = (\n"
        f'{i3}    Description\n'
        f'{i3}    + "<br/><font color=\'red\'>The required libraries for this add on "\n'
        f'{i3}    "are not installed, please run the installation script.</font>"\n'
        f"{i3})\n"
        f"\n"
        f'{i2}AddOnCfg["genotodata"] = collections.OrderedDict()\n'
        f'{i2}AddOnCfg["genotodata"]["enable"] = ConfigFiles[GENLOADER_CONFIG].ReadValue(\n'
        f'{i3}"enable", return_type=bool, section="genotodata", default=False\n'
        f"{i2})\n"
        f'{i2}AddOnCfg["genotodata"]["title"] = "Otodata TM6030 Propane Tank Sensor"\n'
        f'{i2}AddOnCfg["genotodata"]["description"] = Description\n'
        f'{i2}AddOnCfg["genotodata"]["icon"] = "mopeka"\n'
        f'{i2}AddOnCfg["genotodata"]["url"] = (\n'
        f'{i3}"https://github.com/jgyates/genmon/wiki/"\n'
        f'{i3}"1----Software-Overview#genototadatapy-optional"\n'
        f"{i2})\n"
        f'{i2}AddOnCfg["genotodata"]["parameters"] = collections.OrderedDict()\n'
        f"\n"
        f'{i2}AddOnCfg["genotodata"]["parameters"]["tank_name"] = CreateAddOnParam(\n'
        f"{i3}ConfigFiles[GENOTODATA_CONFIG].ReadValue(\n"
        f'{i3}    "tank_name", return_type=str, default="Propane Tank"\n'
        f"{i3}),\n"
        f'{i3}"string",\n'
        f'{i3}"Display name for this tank in the genmon web interface.",\n'
        f'{i3}bounds="",\n'
        f'{i3}display_name="Tank Name",\n'
        f"{i2})\n"
        f'{i2}AddOnCfg["genotodata"]["parameters"]["capacity"] = CreateAddOnParam(\n'
        f"{i3}ConfigFiles[GENOTODATA_CONFIG].ReadValue(\n"
        f'{i3}    "capacity", return_type=int, default=0\n'
        f"{i3}),\n"
        f'{i3}"int",\n'
        f'{i3}"Tank capacity in gallons. Set to 0 to omit from genmon data.",\n'
        f'{i3}bounds="number",\n'
        f'{i3}display_name="Tank Capacity (gallons)",\n'
        f"{i2})\n"
        f'{i2}AddOnCfg["genotodata"]["parameters"]["poll_frequency"] = CreateAddOnParam(\n'
        f"{i3}ConfigFiles[GENOTODATA_CONFIG].ReadValue(\n"
        f'{i3}    "poll_frequency", return_type=int, default=5\n'
        f"{i3}),\n"
        f'{i3}"int",\n'
        f'{i3}"The time in minutes between BLE scan cycles. Default is 5 minutes.",\n'
        f'{i3}bounds="number",\n'
        f'{i3}display_name="Poll Interval (minutes)",\n'
        f"{i2})\n"
        f'{i2}AddOnCfg["genotodata"]["parameters"]["scan_time"] = CreateAddOnParam(\n'
        f"{i3}ConfigFiles[GENOTODATA_CONFIG].ReadValue(\n"
        f'{i3}    "scan_time", return_type=float, default=30.0\n'
        f"{i3}),\n"
        f'{i3}"float",\n'
        f'{i3}"Seconds to listen for BLE advertisements per scan cycle. "\n'
        f'{i3}"Increase if the sensor is far from the Pi.",\n'
        f'{i3}bounds="number",\n'
        f'{i3}display_name="Scan Duration (seconds)",\n'
        f"{i2})\n"
        f'{i2}AddOnCfg["genotodata"]["parameters"]["mac_address"] = CreateAddOnParam(\n'
        f"{i3}ConfigFiles[GENOTODATA_CONFIG].ReadValue(\n"
        f'{i3}    "mac_address", return_type=str, default=""\n'
        f"{i3}),\n"
        f'{i3}"string",\n'
        f'{i3}"Optional: restrict readings to a specific sensor MAC address "\n'
        f'{i3}"(e.g. aa:bb:cc:dd:ee:ff). Leave blank to use the first Otodata device found.",\n'
        f'{i3}bounds="",\n'
        f'{i3}display_name="Sensor MAC Address",\n'
        f"{i2})\n"
        f"\n"
    )


def patch(path):
    with open(path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    content = "".join(lines)
    if "genotodata" in content:
        print("genotodata already present in genserv.py — nothing to do.")
        return

    # ------------------------------------------------------------------
    # 1. Insert GENOTODATA_CONFIG constant after GENMOPEKA_CONFIG line
    # ------------------------------------------------------------------
    idx = -1
    for i, l in enumerate(lines):
        if "GENMOPEKA_CONFIG" in l and "genmopeka.conf" in l and "os.path.join" in l:
            idx = i
            break
    if idx == -1:
        print("ERROR: Could not find GENMOPEKA_CONFIG constant. Aborting.")
        sys.exit(1)

    # Copy the line's indentation and replace genmopeka with genotodata
    new_const = lines[idx].replace("GENMOPEKA_CONFIG", "GENOTODATA_CONFIG").replace(
        "genmopeka.conf", "genotodata.conf"
    )
    lines.insert(idx + 1, new_const)
    print(f"[1/3] Inserted GENOTODATA_CONFIG constant after line {idx + 1}:")
    print(f"      {new_const.rstrip()}")

    # ------------------------------------------------------------------
    # 2. Insert "genotodata": ConfigFiles[GENOTODATA_CONFIG] entry
    #    after "genmopeka": ConfigFiles[GENMOPEKA_CONFIG]
    # ------------------------------------------------------------------
    target2 = -1
    for i, l in enumerate(lines):
        if '"genmopeka"' in l and "ConfigFiles[GENMOPEKA_CONFIG]" in l:
            target2 = i
            break
    if target2 == -1:
        print('ERROR: Could not find "genmopeka": ConfigFiles[GENMOPEKA_CONFIG]. Aborting.')
        sys.exit(1)

    new_entry = lines[target2].replace("genmopeka", "genotodata").replace(
        "GENMOPEKA_CONFIG", "GENOTODATA_CONFIG"
    )
    lines.insert(target2 + 1, new_entry)
    print(f"[2/3] Inserted ConfigFiles dict entry after line {target2 + 1}:")
    print(f"      {new_entry.rstrip()}")

    # ------------------------------------------------------------------
    # 3. Insert AddOnCfg["genotodata"] block after the genmopeka block
    # ------------------------------------------------------------------
    # Find the LAST occurrence of AddOnCfg["genmopeka"] — that's the end of the block.
    last_mopeka = -1
    for i, l in enumerate(lines):
        if 'AddOnCfg["genmopeka"]' in l:
            last_mopeka = i

    if last_mopeka == -1:
        print('ERROR: Could not find AddOnCfg["genmopeka"]. Aborting.')
        sys.exit(1)

    # Find the "# GENMOPEKA" comment to detect block indentation
    block_indent = ""
    for i, l in enumerate(lines):
        if l.strip() == "# GENMOPEKA":
            block_indent = leading_spaces(l)
            break

    # Walk forward from the last genmopeka line to find where the block ends
    end = last_mopeka
    while end < len(lines) - 1:
        end += 1
        stripped = lines[end].strip()
        # Stop at the next top-level comment that looks like another addon section
        if stripped.startswith("# GEN") and stripped == stripped.upper():
            break
        # Or two consecutive blank lines
        if stripped == "" and end + 1 < len(lines) and lines[end + 1].strip() == "":
            end += 1
            break

    block = addon_block(block_indent)
    lines.insert(end, block)
    print(f"[3/3] Inserted AddOnCfg['genotodata'] block before line {end + 1}.")

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

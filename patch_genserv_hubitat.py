#!/usr/bin/env python3
"""
patch_genserv_hubitat.py - Insert the genhubitat addon into genserv.py.

Usage (run from inside your genmon fork directory):
    python3 /path/to/otodata-genmon/patch_genserv_hubitat.py genserv.py

The script is idempotent: it will not apply the patch a second time if
genhubitat is already present.

After running, verify with:
    grep -n genhubitat genserv.py
"""

import sys


def leading_spaces(line):
    return line[: len(line) - len(line.lstrip())]


def addon_block(indent):
    """Return the full AddOnCfg['genhubitat'] block at the given indent."""
    i = indent        # 8 spaces
    i2 = i + "    "  # 12 spaces
    i3 = i2 + "    " # 16 spaces
    return (
        f"\n"
        f"{i}# GENHUBITAT - Native Hubitat Integration\n"
        f'{i}AddOnCfg["genhubitat"] = collections.OrderedDict()\n'
        f'{i}AddOnCfg["genhubitat"]["enable"] = ConfigFiles[GENLOADER_CONFIG].ReadValue(\n'
        f'{i2}"enable", return_type=bool, section="genhubitat", default=False\n'
        f"{i})\n"
        f'{i}AddOnCfg["genhubitat"]["title"] = "Native Hubitat Integration via REST/WebSocket API"\n'
        f'{i}AddOnCfg["genhubitat"][\n'
        f'{i2}"description"\n'
        f'{i}] = "Native Hubitat integration via REST/WebSocket API. No MQTT broker required."\n'
        f'{i}AddOnCfg["genhubitat"]["icon"] = "hubitat"\n'
        f'{i}AddOnCfg["genhubitat"][\n'
        f'{i2}"url"\n'
        f'{i}] = "https://github.com/bdwilson/hubitat/tree/master/Genmon"\n'
        f'{i}AddOnCfg["genhubitat"]["parameters"] = collections.OrderedDict()\n'
        f"\n"
        f'{i}AddOnCfg["genhubitat"]["parameters"]["port"] = CreateAddOnParam(\n'
        f"{i2}ConfigFiles[GENHUBITAT_CONFIG].ReadValue(\n"
        f'{i3}"port", return_type=int, default=9084\n'
        f"{i2}),\n"
        f'{i2}"int",\n'
        f'{i2}"Port for the REST/WebSocket API server.",\n'
        f'{i2}bounds="required digits range:1024:65535",\n'
        f'{i2}display_name="API Server Port",\n'
        f"{i})\n"
        f"{i}genhubitat_api_key = ConfigFiles[GENHUBITAT_CONFIG].ReadValue(\n"
        f'{i2}"api_key", return_type=str, default=""\n'
        f"{i})\n"
        f"{i}if not genhubitat_api_key:\n"
        f"{i2}genhubitat_api_key = str(uuid.uuid4())\n"
        f'{i2}ConfigFiles[GENHUBITAT_CONFIG].WriteValue("api_key", genhubitat_api_key)\n'
        f'{i2}LogError("Auto-generated API key for genhubitat")\n'
        f'{i}AddOnCfg["genhubitat"]["parameters"]["api_key"] = CreateAddOnParam(\n'
        f"{i2}genhubitat_api_key,\n"
        f'{i2}"readonly",\n'
        f'{i2}"API key for authentication (auto-generated). Copy this value into Hubitat when adding the integration.",\n'
        f'{i2}bounds="",\n'
        f'{i2}display_name="API Key (read-only)",\n'
        f"{i})\n"
        f'{i}AddOnCfg["genhubitat"]["parameters"]["poll_interval"] = CreateAddOnParam(\n'
        f"{i2}ConfigFiles[GENHUBITAT_CONFIG].ReadValue(\n"
        f'{i3}"poll_interval", return_type=float, default=3.0\n'
        f"{i2}),\n"
        f'{i2}"int",\n'
        f'{i2}"Interval in seconds between polling genmon for status updates. Default is 3.",\n'
        f'{i2}bounds="number",\n'
        f'{i2}display_name="Poll Interval",\n'
        f"{i})\n"
        f'{i}AddOnCfg["genhubitat"]["parameters"]["blacklist"] = CreateAddOnParam(\n'
        f"{i2}ConfigFiles[GENHUBITAT_CONFIG].ReadValue(\n"
        f'{i3}"blacklist", return_type=str, default="Tiles"\n'
        f"{i2}),\n"
        f'{i2}"string",\n'
        f'{i2}"Comma-separated keywords to exclude from the API. Matches any data path '
        f'containing the keyword (case-insensitive).",\n'
        f'{i2}bounds="",\n'
        f'{i2}display_name="Excluded Data Paths",\n'
        f"{i})\n"
        f'{i}AddOnCfg["genhubitat"]["parameters"]["include_monitor_stats"] = CreateAddOnParam(\n'
        f"{i2}ConfigFiles[GENHUBITAT_CONFIG].ReadValue(\n"
        f'{i3}"include_monitor_stats", return_type=bool, default=True\n'
        f"{i2}),\n"
        f'{i2}"boolean",\n'
        f'{i2}"Include monitor/platform statistics (CPU temp, WiFi, memory).",\n'
        f'{i2}bounds="",\n'
        f'{i2}display_name="Include Monitor Stats",\n'
        f"{i})\n"
        f'{i}AddOnCfg["genhubitat"]["parameters"]["include_weather"] = CreateAddOnParam(\n'
        f"{i2}ConfigFiles[GENHUBITAT_CONFIG].ReadValue(\n"
        f'{i3}"include_weather", return_type=bool, default=True\n'
        f"{i2}),\n"
        f'{i2}"boolean",\n'
        f'{i2}"Include weather data if available.",\n'
        f'{i2}bounds="",\n'
        f'{i2}display_name="Include Weather",\n'
        f"{i})\n"
        f"\n"
    )


def save_addon_key_block(indent):
    """Return the SaveAddOnSettings enable-time API key block."""
    i = indent        # indentation of the if-statement (e.g. 20 spaces)
    i2 = i + "    "  # body indent
    i3 = i2 + "    " # nested body
    i4 = i3 + "    " # doubly nested
    return (
        f'{i}if module == "genhubitat" and basevalues.lower() == "true":\n'
        f"{i2}# Auto-generate API key if empty when addon is enabled\n"
        f"{i2}current_key = ConfigFiles[GENHUBITAT_CONFIG].ReadValue(\n"
        f'{i3}"api_key", return_type=str, default=""\n'
        f"{i2})\n"
        f"{i2}if not current_key:\n"
        f"{i3}new_key = str(uuid.uuid4())\n"
        f'{i3}ConfigFiles[GENHUBITAT_CONFIG].WriteValue("api_key", new_key)\n'
        f'{i3}LogError("Auto-generated API key for genhubitat")\n'
    )


def patch(path):
    with open(path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    content = "".join(lines)
    if "genhubitat" in content:
        print("genhubitat already present in genserv.py — nothing to do.")
        return

    # ------------------------------------------------------------------
    # 1. Insert GENHUBITAT_CONFIG constant after GENHALINK_CONFIG line
    # ------------------------------------------------------------------
    idx1 = -1
    for i, l in enumerate(lines):
        if "GENHALINK_CONFIG" in l and "genhalink.conf" in l and "os.path.join" in l:
            idx1 = i
            break
    if idx1 == -1:
        print("ERROR: Could not find GENHALINK_CONFIG constant. Aborting.")
        sys.exit(1)

    new_const = lines[idx1].replace("GENHALINK_CONFIG", "GENHUBITAT_CONFIG").replace(
        "genhalink.conf", "genhubitat.conf"
    )
    lines.insert(idx1 + 1, new_const)
    print("[1/5] Inserted GENHUBITAT_CONFIG constant after line %d:" % (idx1 + 1))
    print("      " + new_const.rstrip())

    # ------------------------------------------------------------------
    # 2. Insert GENHUBITAT_CONFIG into ConfigFileList after GENHALINK_CONFIG
    # ------------------------------------------------------------------
    target2 = -1
    for i, l in enumerate(lines):
        if l.strip() == "GENHALINK_CONFIG,":
            target2 = i
            break
    if target2 == -1:
        print("ERROR: Could not find GENHALINK_CONFIG, in ConfigFileList. Aborting.")
        sys.exit(1)

    new_list_entry = lines[target2].replace("GENHALINK_CONFIG", "GENHUBITAT_CONFIG")
    lines.insert(target2 + 1, new_list_entry)
    print("[2/5] Inserted GENHUBITAT_CONFIG into ConfigFileList after line %d." % (target2 + 1))

    # ------------------------------------------------------------------
    # 3. Insert "genhubitat": ConfigFiles[GENHUBITAT_CONFIG] into
    #    SaveAddOnSettings ConfigDict after the genhalink entry
    # ------------------------------------------------------------------
    target3 = -1
    for i, l in enumerate(lines):
        if '"genhalink"' in l and "ConfigFiles[GENHALINK_CONFIG]" in l:
            target3 = i
            break
    if target3 == -1:
        print('ERROR: Could not find "genhalink": ConfigFiles[GENHALINK_CONFIG]. Aborting.')
        sys.exit(1)

    new_dict_entry = lines[target3].replace("genhalink", "genhubitat").replace(
        "GENHALINK_CONFIG", "GENHUBITAT_CONFIG"
    )
    lines.insert(target3 + 1, new_dict_entry)
    print("[3/5] Inserted genhubitat into SaveAddOnSettings ConfigDict after line %d." % (target3 + 1))

    # ------------------------------------------------------------------
    # 4. Insert genhubitat enable-time API key block in SaveAddOnSettings
    #    after the genhalink block (identified by unique if-statement)
    # ------------------------------------------------------------------
    target4 = -1
    for i, l in enumerate(lines):
        if 'module == "genhalink" and basevalues.lower() == "true"' in l:
            target4 = i
            break
    if target4 == -1:
        print('ERROR: Could not find SaveAddOnSettings genhalink enable block. Aborting.')
        sys.exit(1)

    # Detect indentation of the if-statement line
    if_indent = leading_spaces(lines[target4])

    # Walk forward from the if-statement to find end of its block
    end4 = target4
    while end4 < len(lines) - 1:
        end4 += 1
        stripped = lines[end4].strip()
        if not stripped:
            break  # blank line marks end of the if-block
        line_indent = leading_spaces(lines[end4])
        if len(line_indent) <= len(if_indent):
            # Back to same or lower indent — stop before this line
            end4 -= 1
            break

    new_key_block = save_addon_key_block(if_indent)
    lines.insert(end4 + 1, new_key_block)
    print("[4/5] Inserted genhubitat API key enable block after line %d." % (end4 + 1))

    # ------------------------------------------------------------------
    # 5. Insert AddOnCfg["genhubitat"] block in GetAddOns() immediately
    #    before the except/finally that closes the genhalink try-block
    # ------------------------------------------------------------------
    # Find the LAST occurrence of AddOnCfg["genhalink"]
    last_halink = -1
    for i, l in enumerate(lines):
        if 'AddOnCfg["genhalink"]' in l:
            last_halink = i

    if last_halink == -1:
        print('ERROR: Could not find AddOnCfg["genhalink"]. Aborting.')
        sys.exit(1)

    # Detect block indentation from the # GENHALINK comment
    block_indent = "        "  # default 8 spaces
    for i, l in enumerate(lines):
        if "# GENHALINK" in l and l.strip().startswith("# GENHALINK"):
            block_indent = leading_spaces(l)
            break

    # Walk forward from last genhalink line to the first non-blank line
    # that is less indented than the block — that's the except/finally
    end5 = last_halink
    while end5 < len(lines) - 1:
        end5 += 1
        stripped = lines[end5].strip()
        if not stripped:
            continue  # skip blank lines
        line_indent = leading_spaces(lines[end5])
        if len(line_indent) < len(block_indent):
            break  # found the except/finally — insert before it

    block = addon_block(block_indent)
    lines.insert(end5, block)
    print("[5/5] Inserted AddOnCfg['genhubitat'] block before line %d." % (end5 + 1))

    # ------------------------------------------------------------------
    # Write patched file
    # ------------------------------------------------------------------
    with open(path, "w", encoding="utf-8") as f:
        f.writelines(lines)

    print("\nDone. Patched %s" % path)
    print("Verify with: grep -n genhubitat " + path)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(1)
    patch(sys.argv[1])

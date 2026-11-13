#!/usr/bin/env python3
"""
WiFi Watchdog v1.1
Author : Techvyana2.0
License: MIT

Find who is on YOUR WiFi and get alerted about unknown devices.
Works in Termux without root. Uses only the Python standard library.

USE ONLY ON A NETWORK YOU OWN OR HAVE PERMISSION TO TEST.

Usage:
  python wifi_watchdog.py                    # scan once
  python wifi_watchdog.py --trust            # mark every device found as known
  python wifi_watchdog.py --trust-ip IP ...  # mark only the given IP(s) as known
  python wifi_watchdog.py --watch 60         # scan every 60 s, alert once per new device
"""
import argparse
import concurrent.futures as cf
import ipaddress
import json
import os
import re
import shutil
import socket
import subprocess
import time

__version__ = "1.1"
__author__ = "Techvyana2.0"

DB = os.path.expanduser("~/.wifi_watchdog.json")
PORTS = (80, 443, 53, 22, 8080, 62078, 5000, 7000, 8009, 554)


def local_ip():
    """Our own IP on the WiFi (a UDP connect sends no data)."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    except OSError:
        return None
    finally:
        s.close()


def is_alive(ip):
    """Ping first. Many phones block ping, so also try common ports."""
    exe = shutil.which("ping") or "/system/bin/ping"
    try:
        r = subprocess.run([exe, "-c", "1", "-W", "1", ip],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=3)
        if r.returncode == 0:
            return True
    except (OSError, subprocess.TimeoutExpired):
        pass
    for port in PORTS:
        try:
            with socket.create_connection((ip, port), timeout=0.3):
                return True
        except ConnectionRefusedError:
            return True  # the device answered "closed", so it is alive
        except OSError:
            continue
    return False


def mac_table():
    """Read MAC addresses if Android allows it. Newer Android often blocks this."""
    macs = {}
    try:
        out = subprocess.run(["ip", "neigh"], capture_output=True, text=True, timeout=5).stdout
        for m in re.finditer(r"(\d+\.\d+\.\d+\.\d+).*?lladdr\s+([0-9a-f:]{17})", out, re.I):
            macs[m.group(1)] = m.group(2).lower()
    except (OSError, subprocess.TimeoutExpired):
        pass
    try:
        with open("/proc/net/arp") as f:
            for line in f.readlines()[1:]:
                parts = line.split()
                if len(parts) >= 4 and parts[3] != "00:00:00:00:00:00":
                    macs.setdefault(parts[0], parts[3].lower())
    except OSError:
        pass
    return macs


def hostname(ip):
    try:
        return socket.gethostbyaddr(ip)[0]
    except OSError:
        return "-"


def scan():
    me = local_ip()
    if not me:
        raise SystemExit("Not connected to WiFi. Connect and try again.")
    hosts = [str(h) for h in ipaddress.ip_network(me + "/24", strict=False).hosts()]
    with cf.ThreadPoolExecutor(max_workers=64) as pool:
        alive = [ip for ip, ok in zip(hosts, pool.map(is_alive, hosts)) if ok]
    macs = mac_table()
    devices = []
    for ip in alive:
        devices.append({
            "ip": ip,
            "mac": macs.get(ip, "N/A"),
            "name": hostname(ip),
            "me": ip == me,
        })
    return me, devices


def key(dev):
    """MAC is the best ID. If Android hides it, fall back to IP."""
    return dev["mac"] if dev["mac"] != "N/A" else dev["ip"]


def load_known():
    try:
        with open(DB) as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def save_known(known):
    with open(DB, "w") as f:
        json.dump(known, f, indent=2)


def notify(text):
    if shutil.which("termux-notification"):
        subprocess.run(["termux-notification", "--title", "WiFi Watchdog",
                        "--content", text])


def entry(dev):
    return {"name": dev["name"], "seen": time.strftime("%Y-%m-%d %H:%M")}


def run_once(trust=False, trust_ips=None, alerted=None):
    me, devices = scan()
    known = load_known()
    trust_ips = set(trust_ips or [])
    changed = False
    new_devices = []

    print(f"\nYour IP: {me}  |  Devices found: {len(devices)}\n")
    print(f"{'IP':<16}{'MAC':<19}{'NAME':<28}STATUS")
    print("-" * 72)
    for d in devices:
        k = key(d)
        if d["me"]:
            status = "this phone"
        elif k in known:
            status = "known"
        elif trust or d["ip"] in trust_ips:
            known[k] = entry(d)
            changed = True
            status = "trusted now"
        else:
            status = "NEW !!"
            new_devices.append(d)
        print(f"{d['ip']:<16}{d['mac']:<19}{d['name'][:26]:<28}{status}")

    missing = trust_ips - {d["ip"] for d in devices}
    for ip in sorted(missing):
        print(f"\nCould not find {ip} on the network.")
    if changed:
        save_known(known)
        print(f"\nKnown devices saved -> {DB}")

    fresh = [d for d in new_devices if alerted is None or key(d) not in alerted]
    if fresh:
        msg = f"{len(fresh)} unknown device(s): " + ", ".join(d["ip"] for d in fresh)
        print("\n" + msg)
        notify(msg)
        if alerted is not None:
            alerted.update(key(d) for d in fresh)
    elif new_devices:
        print("\nUnknown device(s) still connected (already alerted).")

    if any(d["mac"] == "N/A" for d in devices):
        print("\nNote: Android is hiding MAC addresses, so devices are matched by IP.")
        print("IPs can change, so an old device may show as NEW after a router restart.")
    return new_devices


def main():
    ap = argparse.ArgumentParser(description="Find who is on your WiFi. By Techvyana2.0")
    ap.add_argument("--trust", action="store_true", help="mark all devices found as known")
    ap.add_argument("--trust-ip", nargs="+", metavar="IP", help="mark only these IP(s) as known")
    ap.add_argument("--watch", type=int, metavar="SEC", help="rescan every SEC seconds")
    ap.add_argument("--version", action="version", version=f"WiFi Watchdog {__version__}")
    args = ap.parse_args()

    if args.watch:
        alerted = set()
        while True:
            run_once(args.trust, args.trust_ip, alerted)
            time.sleep(args.watch)
    else:
        run_once(args.trust, args.trust_ip)


if __name__ == "__main__":
    main()

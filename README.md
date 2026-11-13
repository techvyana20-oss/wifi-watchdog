# 🛡️ WiFi Watchdog

**Find out who is connected to your WiFi, and get an alert when an unknown device joins.**

Runs in **Termux on Android, no root needed**. Pure Python, no extra libraries.

> **Author:** Techvyana2.0 · **License:** MIT · **Version:** 1.1

---

## ⚠️ Use only on your own network

This tool is for **defending your own WiFi**. Scan only networks you own or have clear permission to test. The author is not responsible for misuse.

It does **not** hack, block, or disconnect anyone, and it cannot read anyone's messages or browsing. It only shows which devices are present.

---

## ✨ Features

- Scans your WiFi and lists every live device (IP, name, MAC if Android allows)
- Saves a **known devices** list, so strangers show up as `NEW !!`
- **Watch mode** rescans every N seconds
- **Alerts once** per new device (no repeated spam)
- Phone notification through Termux:API
- Trust all devices, or only one device, with a single command

---

## 📋 Requirements

| Requirement | Details |
|---|---|
| Android + Termux | Install Termux from F-Droid or GitHub |
| Python | 3.8 or newer (`pkg install python`) |
| ping | Recommended (`pkg install inetutils`) |
| Termux:API | Optional, for notifications (`pkg install termux-api` + the Termux:API app) |
| pip packages | **None** |

See [`requirements.txt`](requirements.txt).

---

## 🚀 Installation

```bash
pkg update
pkg install python inetutils termux-api git
git clone https://github.com/techvyana20-oss/wifi-watchdog.git
cd wifi-watchdog
```

---

## 🧪 Usage

**1. First run: save your own devices as known.** Do this when only your family's devices are on the WiFi.

```bash
python wifi_watchdog.py --trust
```

**2. Scan any time:**

```bash
python wifi_watchdog.py
```

**3. Keep watching** (scan every 60 seconds and alert on new devices):

```bash
termux-wake-lock
python wifi_watchdog.py --watch 60
```

**4. Trust just one new device** (for example, a friend's phone you approved):

```bash
python wifi_watchdog.py --trust-ip 192.168.1.23
```

### Options

| Option | What it does |
|---|---|
| `--trust` | Mark every device found as known |
| `--trust-ip IP [IP ...]` | Mark only the given IP(s) as known |
| `--watch SEC` | Rescan every SEC seconds |
| `--version` | Show the version |
| `-h`, `--help` | Show help |

Known devices are stored in `~/.wifi_watchdog.json`. Delete this file to start fresh.

---

## 📟 Sample output

```
Your IP: 192.168.1.5  |  Devices found: 4

IP              MAC               NAME                        STATUS
------------------------------------------------------------------------
192.168.1.1     N/A               router.local                known
192.168.1.5     N/A               -                           this phone
192.168.1.8     N/A               Rahul-laptop                known
192.168.1.23    N/A               -                           NEW !!

1 unknown device(s): 192.168.1.23
```

---

## ⚙️ How it works

1. Finds your phone's IP and assumes a `/24` network (for example `192.168.1.1` to `192.168.1.254`).
2. Checks each address with `ping`. If ping is blocked, it tries common ports.
3. Reads MAC addresses from the ARP/neighbour table when Android allows it.
4. Compares devices with the saved known list and flags new ones.

---

## 🚧 Limitations

- **Newer Android versions hide MAC addresses** from apps. The tool then matches devices by IP, and shows a note.
- **IP addresses can change** after a router restart, so a known device may show as `NEW`. Run `--trust-ip` for it, or set fixed IPs in your router.
- **Random (private) MAC addresses:** some phones use a different MAC per WiFi network.
- **Sleeping devices** that block every probe may be missed in a scan.
- Alerts only work **while the tool is running**. Use `termux-wake-lock` and set Termux battery use to unrestricted.
- Only `/24` networks are scanned.

This is an early warning tool, not a complete security system. If you find an unknown device, change your WiFi password.

---

## 🗺️ Roadmap

- Device nicknames (`--name 192.168.1.8 "Rahul laptop"`)
- Vendor lookup from MAC prefix
- Export scan history to CSV
- Telegram alerts

---

## 🤝 Contributing

Issues and pull requests are welcome. Keep the tool defensive and the code dependency-free.

---

## 👤 Author

**Techvyana2.0**

- 🎥 YouTube: [Tech vyana 2.0](https://www.youtube.com/channel/UCtOsvuTLp9qefl1yoQDqmPg)
- 💻 GitHub: [techvyana20-oss](https://github.com/techvyana20-oss)
- 📸 Instagram: [@techvyana2.0](https://www.instagram.com/techvyana2.0/)

If this helped you, give the repo a ⭐ and subscribe to the channel.

---

## 📄 License

Released under the [MIT License](LICENSE). Copyright (c) 2026 Techvyana2.0.

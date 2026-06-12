# HORACO Managed Switch — Home Assistant Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)
[![GitHub Release](https://img.shields.io/github/v/release/gtrancillo/horaco_switch_ha)](https://github.com/gtrancillo/horaco_switch_ha/releases)
[![Validate](https://github.com/gtrancillo/horaco_switch_ha/actions/workflows/validate.yml/badge.svg)](https://github.com/gtrancillo/horaco_switch_ha/actions/workflows/validate.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![HA Version](https://img.shields.io/badge/Home%20Assistant-2024.1%2B-blue)](https://www.home-assistant.io/)

Control and monitor your **HORACO**, **keepLink** and compatible OEM managed switches directly from Home Assistant — **no extra app, no Docker, no intermediate service**. The integration talks straight to the switch's built-in HTTP interface, the same CGI endpoints used by [byte4geek/switch-dashboard](https://github.com/byte4geek/switch-dashboard), implemented natively in HA with full async support.

---

## Supported devices

| Model | Ports | SFP+ | Status |
|-------|-------|------|--------|
| HORACO HC-SWTGW218AS | 8 × GbE | 2 × 10G | ✅ Confirmed |
| HORACO HC-SWTGW215AS | 5 × GbE | — | ✅ Confirmed |
| keepLink KP9000-9XH-X | 8 × GbE | 1 × 10G | ✅ Confirmed |
| OEM Realtek RTL8373-based switches | varies | — | ✅ Likely |

> If your switch has a browser-accessible web UI on port 80 with user/password login, it will very likely work. Open an issue to get it added to the table.

---

## Features

- 🔌 **Per-port child devices** — each port is its own HA device grouping link state, speed, duplex, TX/RX bytes, TX/RX packets and flow control
- 📊 **Traffic counters** — cumulative TX/RX sensors compatible with HA statistics and the Energy dashboard
- 🔄 **Reboot button** — one-tap remote reboot from any HA dashboard or automation
- ⚡ **Direct LAN polling** — fully local, no cloud, no proxy
- 🔧 **Configurable interval** — 10 to 300 seconds (default 30 s)

---

## Installation

### Via HACS (recommended)

1. HACS → Integrations → ⋮ → **Custom repositories**
2. URL: `https://github.com/gtrancillo/horaco_switch_ha` · Type: **Integration**
3. Install **HORACO Managed Switch** and restart HA
4. **Settings → Devices & Services → Add Integration → HORACO Managed Switch**

### Manual

1. Download the latest `horaco_switch.zip` from [Releases](https://github.com/gtrancillo/horaco_switch_ha/releases/latest)
2. Unzip and copy the `horaco_switch/` folder into `<config>/custom_components/`
3. Restart HA and add the integration via the UI

---

## Setup

| Field | Default | Notes |
|-------|---------|-------|
| Switch IP Address | — | e.g. `192.168.1.100` |
| HTTP Port | `80` | Change only if you remapped the web UI |
| Username | `admin` | Default HORACO credential |
| Password | `admin` | Default HORACO credential |

After setup click **Configure** on the integration card to adjust the polling interval (10–300 s).

---

## Entities

### Switch device

| Entity | Type | Description |
|--------|------|-------------|
| Uptime | Sensor | e.g. `3d 14h 22m` |
| Firmware | Sensor | Firmware version string |
| MAC Address | Sensor | Switch hardware MAC |
| Ports Up | Sensor | Count of active ports |
| Ports Total | Sensor | Total physical port count |
| **Reboot** | **Button** | Sends `POST /reboot.cgi` to the switch |

### Port N device *(one per physical port)*

| Entity | Type | Description |
|--------|------|-------------|
| Link | Binary Sensor | `ON` = up · `OFF` = down/disabled. Carries all port attrs. |
| Speed | Sensor | `100M` · `1000M` · `10G` · `Disabled` |
| Duplex | Sensor | `Full` or `Half` |
| TX | Sensor | Total bytes transmitted (cumulative) |
| RX | Sensor | Total bytes received (cumulative) |
| TX Packets | Sensor | Total packets transmitted |
| RX Packets | Sensor | Total packets received |
| Flow Control | Sensor | `Enabled` or `Disabled` |

---

## Example automations

### Alert when a port goes down

```yaml
alias: "Switch port 3 disconnected"
trigger:
  - platform: state
    entity_id: binary_sensor.port_3_link
    to: "off"
    for: "00:00:30"
action:
  - service: notify.mobile_app
    data:
      title: "⚠️ Network alert"
      message: "Switch port 3 went down"
```

### Weekly maintenance reboot

```yaml
alias: "Switch reboot Sunday 3 AM"
trigger:
  - platform: time
    at: "03:00:00"
condition:
  - condition: time
    weekday: [sun]
action:
  - service: button.press
    target:
      entity_id: button.switch_192_168_1_100_reboot
```

---

## How it works

1. **Auth** — `MD5(username + password)` → `POST /login.cgi`, cookie jar
2. **Poll** (every N seconds):
   - `GET /info.cgi` → model, firmware, MAC, uptime, port link/speed
   - `GET /port.cgi` → admin state per port
   - `GET /port.cgi?page=stats` → TX/RX counters
3. **Reboot** — `POST /reboot.cgi {"cmd":"reboot"}`

A 0.4 s delay between sequential requests prevents session thrashing on the switch's uIP micro-controller.

---

## Contributing

See [CONTRIBUTING.md](.github/CONTRIBUTING.md) for the full workflow.

Short version: fork → branch → PR → both CI checks green → merge.

**Found a compatible device?** Open a [New device issue](https://github.com/gtrancillo/horaco_switch_ha/issues/new?template=new_device.yml) and we'll add it to the table.

---

## Protecting the `main` branch (repo setup guide)

After pushing to GitHub, go to **Settings → Branches → Add rule** and configure:

| Setting | Value |
|---------|-------|
| Branch name pattern | `main` |
| Require a pull request before merging | ✅ |
| Require approvals | 1 (or 0 for solo projects) |
| Require status checks to pass | ✅ |
| Status checks required | `HACS validation`, `hassfest` |
| Do not allow bypassing the above settings | ✅ (optional but recommended) |

This ensures no commit lands on `main` without both CI validations passing.

---

## License

MIT — see [LICENSE](LICENSE)

## Credits

CGI endpoint knowledge and scraping approach from [byte4geek/switch-dashboard](https://github.com/byte4geek/switch-dashboard).

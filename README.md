# HORACO Managed Switch — Home Assistant Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)
[![GitHub Release](https://img.shields.io/github/v/release/gtrancillo/horaco_switch_ha)](https://github.com/gtrancillo/horaco_switch_ha/releases)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![HA Version](https://img.shields.io/badge/Home%20Assistant-2024.1%2B-blue)](https://www.home-assistant.io/)

Native Home Assistant integration for **HORACO HC-SWTGW218AS**, **HC-SWTGW215AS**, **keepLink KP9000** and compatible OEM managed switches.

**No intermediate service, no Docker, no switch-dashboard app required.** This integration talks directly to the switch's built-in HTTP CGI interface — the same endpoints used by [byte4geek/switch-dashboard](https://github.com/byte4geek/switch-dashboard), implemented natively in HA.

---

## Supported Devices

| Model | Ports | SFP+ | Confirmed |
|-------|-------|------|-----------|
| HORACO HC-SWTGW218AS | 8 x GbE | 2 x 10G | ✅ |
| HORACO HC-SWTGW215AS | 5 x GbE | — | ✅ |
| keepLink KP9000-9XH-X | 8 x GbE | 1 x 10G | ✅ |
| OEM Realtek RTL8373-based switches | varies | — | ✅ likely |

> **Tip:** If your switch has a web interface accessible via a browser on port 80 with user/password login, it will very likely work.

---

## Features

- 🔌 **Per-port child devices** — each port groups its own entities (link, speed, TX/RX bytes, packets, flow control)
- 📊 **Traffic counters** — cumulative TX/RX bytes and packets, compatible with HA statistics and Energy dashboard
- 🔄 **Reboot button** — remote switch reboot with a single button press
- ⚡ **Direct CGI polling** — no cloud, no proxy, pure LAN
- 🔧 **Configurable polling interval** — 10 to 300 seconds

---

## Installation

### Via HACS (Recommended)

1. Open HACS → Integrations → ⋮ → **Custom repositories**
2. Add `https://github.com/gtrancillo/horaco_switch_ha` → type **Integration**
3. Search **HORACO** and install
4. Restart Home Assistant
5. Go to **Settings → Devices & Services → Add Integration → HORACO Managed Switch**

### Manual

1. Download the [latest release](https://github.com/gtrancillo/horaco_switch_ha/releases/latest)
2. Copy the `horaco_switch/` folder into `<your HA config>/custom_components/`
3. Restart Home Assistant
4. Go to **Settings → Devices & Services → Add Integration → HORACO Managed Switch**

---

## Configuration

During setup you will be asked for:

| Field | Default | Description |
|-------|---------|-------------|
| Switch IP Address | — | LAN IP of the switch (e.g. `192.168.1.100`) |
| HTTP Port | `80` | Switch web interface port |
| Username | `admin` | Switch admin username |
| Password | `admin` | Switch admin password |

After setup, click **Configure** on the integration card to adjust:

| Option | Default | Range |
|--------|---------|-------|
| Polling interval | `30` s | 10 – 300 s |

---

## Entities

### Switch Device

| Entity | Type | Description |
|--------|------|-------------|
| `Uptime` | Sensor | Switch uptime (e.g. `3d 14h 22m`) |
| `Firmware` | Sensor | Firmware version string |
| `MAC Address` | Sensor | Switch hardware MAC |
| `Ports Up` | Sensor | Number of currently active ports |
| `Ports Total` | Sensor | Total physical port count |
| `Reboot` | Button | Sends reboot command to the switch |

### Port N Device  *(one per physical port)*

| Entity | Type | Description |
|--------|------|-------------|
| `Link` | Binary Sensor | `ON` = link up · `OFF` = down / disabled |
| `Speed` | Sensor | Negotiated speed (`100M`, `1000M`, `10G`, …) |
| `Duplex` | Sensor | `Full` or `Half` |
| `TX` | Sensor | Total transmitted bytes (cumulative) |
| `RX` | Sensor | Total received bytes (cumulative) |
| `TX Packets` | Sensor | Total transmitted packets (cumulative) |
| `RX Packets` | Sensor | Total received packets (cumulative) |
| `Flow Control` | Sensor | `Enabled` or `Disabled` |

The `Link` binary sensor also carries all port attributes as extra state:
`status`, `link`, `speed`, `duplex`, `flow_control`, `tx_bytes`, `rx_bytes`, `tx_packets`, `rx_packets`

---

## Example Automations

### Alert when a port goes down

```yaml
alias: "Switch Port 3 Disconnected"
trigger:
  - platform: state
    entity_id: binary_sensor.port_3_link
    to: "off"
    for: "00:00:30"
action:
  - service: notify.mobile_app
    data:
      title: "⚠️ Network alert"
      message: "Switch port 3 link went down"
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

### Dashboard — all port states at a glance

```yaml
type: custom:mushroom-entity-card   # or type: entities
title: Switch Ports
entities:
  - entity: binary_sensor.port_1_link
    secondary_info: attribute
    attribute: speed
  - entity: binary_sensor.port_2_link
    secondary_info: attribute
    attribute: speed
  # repeat for all ports…
```

---

## How It Works

The integration replicates the HTTP scraping logic from [byte4geek/switch-dashboard](https://github.com/byte4geek/switch-dashboard) natively inside HA:

1. **Auth** — `MD5(username + password)` → `POST /login.cgi`, cookie jar
2. **Poll every N seconds:**
   - `GET /info.cgi` → model, firmware, MAC, uptime, port link/speed
   - `GET /port.cgi` → admin-enabled state per port
   - `GET /port.cgi?page=stats` → TX/RX byte and packet counters
3. **Reboot** — `POST /reboot.cgi {"cmd":"reboot"}`

A small delay (0.4 s) is enforced between sequential requests to avoid session thrashing the switch's uIP micro-controller.

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| "Cannot connect" during setup | Verify HA can reach the switch IP on port 80; check credentials |
| Entities show `unavailable` | Check HA logs for `[horaco_switch]` errors |
| Counters not updating | Some OEM firmware versions zero out stats on re-login; increase polling interval |
| Reboot button does nothing | Ensure the switch firmware supports `/reboot.cgi` |

---

## Contributing

Pull requests welcome! If you have a different switch model that works (or doesn't), please open an issue with your model name and HA logs.

---

## License

MIT — see [LICENSE](LICENSE)

---

## Credits

- CGI scraping approach and endpoint knowledge: [byte4geek/switch-dashboard](https://github.com/byte4geek/switch-dashboard)
- Home Assistant custom component structure inspired by the HA developer docs

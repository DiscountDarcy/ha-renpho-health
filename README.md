# Renpho Health — Home Assistant Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)

Home Assistant custom component that fetches body composition data from the **Renpho Health** cloud API and exposes it as sensor entities.

> **Note:** This targets the **new Renpho Health app** (2024+). The old `renpho.qnclouds.com` API integrations no longer work with the Health app — this component uses the new `cloud.renpho.com` encrypted API.

## Features

- 🔐 **AES-encrypted API** — handles the Health app's custom encryption automatically
- 📊 **16 body composition metrics** — weight, BMI, body fat %, water %, muscle %, bone %, BMR, visceral fat, subcutaneous fat, protein %, body age, lean body mass, fat-free weight, heart rate, cardiac index, body shape
- 📱 **Multi-scale support** — discovers all scales on your Renpho account
- ⚙️ **UI config flow** — no YAML editing needed
- 🔄 **Configurable polling** — update interval from 5 minutes to 24 hours
- 🏷️ **Device registry** — each scale appears as a device with all its sensors grouped

## Installation

### HACS (Recommended)

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=DiscountDarcy&repository=ha-renpho-health&category=integration)

Or manually:
1. In HACS, click **⋯** → **Custom repositories**
2. Paste `https://github.com/DiscountDarcy/ha-renpho-health`
3. Category: **Integration**
4. Click **Add** → find "Renpho Health" in HACS → **Download**

### Manual

```bash
cd /config/custom_components
git clone https://github.com/DiscountDarcy/ha-renpho-health.git renpho_health
```

Then restart Home Assistant.

## Setup

1. Go to **Settings** → **Devices & Services** → **+ Add Integration**
2. Search for **"Renpho Health"**
3. Enter your **Renpho Health app email and password**
4. Choose update interval (default: 60 minutes)
5. Click **Submit**

## Sensors Created

| Sensor | Unit | Description |
|--------|------|-------------|
| Weight | kg | Body weight |
| BMI | — | Body Mass Index |
| Body Fat | % | Body fat percentage |
| Body Water | % | Total body water percentage |
| Muscle Mass | % | Skeletal muscle percentage |
| Bone Mass | % | Bone mass percentage |
| BMR | kcal/day | Basal Metabolic Rate |
| Visceral Fat | level | Visceral fat level |
| Subcutaneous Fat | % | Subcutaneous fat percentage |
| Protein | % | Protein percentage |
| Body Age | years | Estimated body age |
| Lean Body Mass | kg | Lean body mass |
| Fat Free Weight | kg | Fat-free body weight |
| Heart Rate | bpm | Heart rate at measurement |
| Cardiac Index | — | Cardiac output index |
| Body Shape | — | Body shape classification |

## Requirements

- Home Assistant 2024.1 or newer
- Renpho Health app account (the **new** app, not the old "Renpho" app)

## Credits

- Based on reverse-engineering by [forkerer/RenphoGarminSync-CLI](https://github.com/forkerer/RenphoGarminSync-CLI)
- Uses [danvaneijck/renpho-api](https://github.com/danvaneijck/renpho-api) Python client

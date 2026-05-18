# Renpho Health — Home Assistant Integration

![icon](https://raw.githubusercontent.com/DiscountDarcy/ha-renpho-health/main/brand/icon.png)

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

## Troubleshooting

> **Important:** This integration polls the **Renpho cloud API** (`cloud.renpho.com`). It does not communicate with your scale directly over Bluetooth or Wi-Fi. Your scale must be syncing to the Renpho Health app for data to appear in Home Assistant.

### No entities appearing

1. Open the Renpho Health app on your phone and confirm your latest weigh-in is visible
2. Check that the scale successfully synced (look for the measurement in the app's history)
3. In Home Assistant, go to **Settings → Devices & Services → Renpho Health** and verify the integration shows "Connected"
4. The integration polls every 60 minutes by default — new measurements won't appear instantly

### "Invalid credentials" error

- Use the same email and password as the **Renpho Health** app (the new blue-icon app, not the old "Renpho" app)
- If you recently changed your Renpho password, re-enter it in the integration's options
- Accounts created before 2024 may need to migrate to the Health app first

### "Failed to connect" error

- Your Home Assistant instance needs internet access to reach `cloud.renpho.com`
- Check your HA host can resolve DNS and make outbound HTTPS connections
- Temporary Renpho cloud outages do happen — the integration will retry on the next poll interval

### Rate limiting

If you set the polling interval very low (e.g., 5 minutes) and have multiple scales or users,
you may hit Renpho's API rate limits. Symptoms include "Rate limited" warnings in the HA logs.
Increase the polling interval to 30+ minutes if this occurs.

### Data looks wrong?

- Verify the **Unit system** in the integration options matches your preference (Imperial/Metric)
- Changing the unit system updates sensor values immediately
- For multi-user households, make sure you're looking at the correct user's sensor entities

### Still stuck?

[Open an issue](https://github.com/DiscountDarcy/ha-renpho-health/issues) on GitHub. Include:
- Your Home Assistant version
- The integration version (visible in HACS or the manifest)
- Any relevant log entries from **Settings → System → Logs** (search for "renpho")

## Removal

1. In Home Assistant, go to **Settings → Devices & Services**
2. Find the **Renpho Health** integration card
3. Click **⋯** → **Delete**
4. If installed via HACS, go to **HACS → Integrations → Renpho Health → ⋯ → Remove**
5. Restart Home Assistant to fully clear the integration

## Credits

- Based on reverse-engineering by [forkerer/RenphoGarminSync-CLI](https://github.com/forkerer/RenphoGarminSync-CLI)
- Uses [danvaneijck/renpho-api](https://github.com/danvaneijck/renpho-api) Python client

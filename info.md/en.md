# Renpho Health

![icon](https://raw.githubusercontent.com/DiscountDarcy/ha-renpho-health/main/brand/icon.png)

Home Assistant custom integration for Renpho Health smart scales. Fetches body composition data from the **Renpho Health cloud API** and exposes it as sensor entities.

## Why this integration?

The official Renpho integration was removed from Home Assistant. This integration fills that gap by connecting to the **new Renpho Health app** (2024+) cloud API (`cloud.renpho.com`) with proper encryption support.

## Features

- 🔐 **AES-encrypted API** — handles the Health app's custom encryption
- 📊 **16 body composition metrics** — weight, BMI, body fat %, water %, muscle %, bone %, BMR, visceral fat, and more
- 📱 **Multi-scale support** — all scales on your Renpho account
- 👥 **Multi-user support** — separate entities per family member
- ⚖️ **Imperial & Metric** — toggle between lbs and kg in options
- ⚙️ **UI config flow** — no YAML editing needed
- 🔄 **Configurable polling** — 5 minutes to 24 hours

## Quick Links

- [Documentation](https://github.com/DiscountDarcy/ha-renpho-health)
- [Issue Tracker](https://github.com/DiscountDarcy/ha-renpho-health/issues)
- [Source Code](https://github.com/DiscountDarcy/ha-renpho-health)

## Requirements

- Home Assistant 2024.1 or newer
- Renpho Health app account (the **new** app, not the old "Renpho" app)

## Credits

Built with ❤️ by [Barnaby](https://github.com/barnaby-the-bot-scrivener), based on reverse engineering by [forkerer/RenphoGarminSync-CLI](https://github.com/forkerer/RenphoGarminSync-CLI).

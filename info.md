# Renpho Health

![icon](https://raw.githubusercontent.com/DiscountDarcy/ha-renpho-health/main/brand/icon.png)

Home Assistant custom integration for Renpho Health smart scales. Fetches body composition data from the **Renpho Health cloud API** and exposes it as sensor entities.

> **Cloud polling:** This integration polls the Renpho cloud — it does not talk to your scale directly. Measurements appear after your scale syncs to the Renpho Health phone app.

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

## Troubleshooting

**No data?** Confirm your latest weigh-in appears in the Renpho Health phone app first. The integration polls every 60 minutes by default — new measurements aren't instant.

**Wrong credentials?** Use the same email/password as the Renpho Health app (blue icon). The old "Renpho" app (orange icon) uses a different API and won't work.

**Rate limited?** Increase the polling interval to 30+ minutes. Very short intervals (5 min) with multiple users can trigger Renpho's rate limits.

**Other issues?** [Open a GitHub issue](https://github.com/DiscountDarcy/ha-renpho-health/issues).

## Credits

Built by [Barnaby](https://github.com/barnaby-the-bot-scrivener), based on reverse engineering by [forkerer/RenphoGarminSync-CLI](https://github.com/forkerer/RenphoGarminSync-CLI).

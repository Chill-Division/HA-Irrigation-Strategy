# Crop Steering for Home Assistant

![Release](https://img.shields.io/badge/Release-2.35.2-blue)
![Home Assistant](https://img.shields.io/badge/Home%20Assistant-2026.5+-41BDF5)
![HACS](https://img.shields.io/badge/HACS-Custom-orange)
![License](https://img.shields.io/badge/License-MIT-green)

Crop Steering waters a grow room automatically. Every minute it reads each zone's moisture and EC probes, decides whether the zone needs a shot and how big, and runs your pump and valves to deliver it, through the four-phase day that crop-steering growers use. It runs inside [Home Assistant](https://www.home-assistant.io/) with the probes, pumps and valves you already have, on your own hardware: no cloud account, no subscription.

**Deterministic, sensor-driven crop steering.** No AI makes any decision. Every shot comes from a published rule and your setpoints: the same readings, settings and day so far always give the same decision, and the dashboard shows the numbers behind each one. Nothing guesses, nothing makes up a reading, and nothing apologises after the fact.

![The Overview: today's grow day for every zone, the zones and the tank](https://raw.githubusercontent.com/ChillingSilence/HA-Irrigation-Strategy/main/img/operator-dashboard.png)

> **Safety first.** This switches real pumps and valves, unattended, on living plants. Set each room up with watering switched off, check every probe and switch it uses, and do a catch test (measure what the drippers actually deliver) before you let it water. It does not replace physical safety devices: use valves that close when power is lost, and a float switch or timer that can stop a pump on its own.

## Features

- **The four-phase day, for every zone.** P0: the morning dryback. P1: small shots, a few minutes apart, up to your peak target. P2: a top-up whenever moisture falls to your trigger. P3: the overnight dryback, held at your dryback target, with a rescue shot if a zone still gets too dry. The day's counters start again at lights-on.
- **Shots sized from your hardware.** Each zone's pot size, plant count, drippers and dripper flow turn a shot's percentage into litres and seconds, within a daily water limit and a maximum shot length.
- **A plan for the whole grow.** Steer each zone week by week, or day by day, between vegetative and generative; the targets change at lights-on. Keep the plans that worked in a recipe library.
- **The grow day on one chart.** Each zone's phases, shots, holds and setting changes since lights-on, against its targets, yesterday and the projected rest of the day. Every setting change says who made it and what it replaced.
- **Nutrient batches.** Refills the reservoir before the next shots would take it under its minimum, recirculates and runs each doser in turn from the feed recipe for the growth stage; with automatic refills off, watering waits at the minimum, so the pump never runs it dry. Stock tanks count down with every batch and warn before they run out.
- **Water use and runs compared.** Litres per zone by day, week and grow, today's water per plant, and this run lined up against an earlier one at the same age.
- **It fails safe.** Every switch it turns off is read back, and one that stays on holds the room and alerts you. A zone whose probe dies follows a working zone, or a cautious timer. An empty room switches off: no watering, no alerts.
- **Alerts you can act on.** Each alert, as a Repairs card or a notification, carries a code (such as CS-601) that the built-in Help explains: what it means, what happens to watering meanwhile, and what to do.
- **Auto setpoints (off by default).** Learns each zone's real peak and drying rates from its own shots, and keeps its targets reachable in small, bounded steps, by fixed rules.
- **Set up without YAML.** Map the valves, pumps and probes you already have from the dashboard. Every save is checked before it applies, and the controller confirms it has picked the change up.
- **A log you can read.** The controller app's log says, every minute and in plain words, what each zone is doing and what it is waiting for.

| Today's targets on the zone's own readings | Nutrient batches | Water use per zone |
| --- | --- | --- |
| ![Today's targets on the zone's recorded moisture and EC, with the projected day](https://raw.githubusercontent.com/ChillingSilence/HA-Irrigation-Strategy/main/img/plan-graph.png) | ![The Reservoir page: a batch's steps, the doses going in while it fills, and the reservoir's level](https://raw.githubusercontent.com/ChillingSilence/HA-Irrigation-Strategy/main/img/reservoir.png) | ![Today, this week, this grow and an estimate for the whole grow, with litres per grow week](https://raw.githubusercontent.com/ChillingSilence/HA-Irrigation-Strategy/main/img/water-use.png) |

| On a phone: the Overview | The Reservoir | Today's targets |
| --- | --- | --- |
| ![The Overview on a phone](https://raw.githubusercontent.com/ChillingSilence/HA-Irrigation-Strategy/main/img/mobile-overview.png) | ![The Reservoir on a phone: a batch's steps, the doses inside Fill and mix](https://raw.githubusercontent.com/ChillingSilence/HA-Irrigation-Strategy/main/img/mobile-reservoir.png) | ![Today's targets on a phone](https://raw.githubusercontent.com/ChillingSilence/HA-Irrigation-Strategy/main/img/mobile-plan.png) |

More in the [screenshots](https://github.com/ChillingSilence/HA-Irrigation-Strategy/blob/main/docs/SCREENSHOTS.md).

## What you need

| | |
| --- | --- |
| **Home Assistant** | **2026.5.0 or newer.** Every change is tested on 2026.5.0 and on 2026.9.3. |
| **The controller app** | Home Assistant OS or Supervised, where it installs from the app store (amd64, aarch64 or armv7) and brings its own Python 3.12. On Home Assistant Container or Core, run the controller yourself (see the [install guide](https://github.com/Chill-Division/HA-Irrigation-Strategy/blob/main/docs/INSTALL.md)). |
| **HACS** | 1.6.0 or newer for the guided download, or copy `custom_components/crop_steering` into Home Assistant by hand. |
| **Hardware** | A switch Home Assistant can control for each zone's valve (and for your pump and main line, if you have them), and a moisture probe per zone. EC probes and tank sensors are optional but recommended. |

## Install

Crop Steering comes in two parts, and watering needs both: the **integration** keeps your rooms, settings and plans and adds the Crop Steering page to the sidebar, but never switches anything; the **controller app** reads the probes and runs the pump and valves.

1. **Download the integration with HACS**, then restart Home Assistant.
   [![Open your Home Assistant instance and open this repository in HACS.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=Chill-Division&repository=HA-Irrigation-Strategy&category=integration)
2. **Add Crop Steering** and name your first room.
   [![Open your Home Assistant instance and start setting up Crop Steering.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=crop_steering)
3. **Add the controller app's repository**, then install and start **Crop Steering Controller**.
   [![Open your Home Assistant instance and add this app repository.](https://my.home-assistant.io/badges/supervisor_add_addon_repository.svg)](https://my.home-assistant.io/redirect/supervisor_add_addon_repository/?repository_url=https%3A%2F%2Fgithub.com%2FChill-Division%2FHA-Irrigation-Strategy)
4. **Open Crop Steering in the sidebar.** Map your valves, pump and probes in **Settings, Rooms & hardware**, check the readings on the **Overview**, and keep watering switched off until everything reads correctly.

**Updating:** both parts carry one version number; update them together. Update the integration in HACS and restart Home Assistant, then press **Update** on the controller app (restarting it alone keeps the old version). Updates keep your rooms, settings, plans and history. The [install guide](https://github.com/Chill-Division/HA-Irrigation-Strategy/blob/main/docs/INSTALL.md) covers manual installs, upgrades and rolling back.

## Documentation

- [User guide](https://github.com/Chill-Division/HA-Irrigation-Strategy/blob/main/docs/USER_GUIDE.md) and [planning a grow](https://github.com/Chill-Division/HA-Irrigation-Strategy/blob/main/docs/GROW_PLANS.md)
- [Error codes](https://github.com/Chill-Division/HA-Irrigation-Strategy/blob/main/docs/ERROR_CODES.md) and [troubleshooting](https://github.com/Chill-Division/HA-Irrigation-Strategy/blob/main/docs/troubleshooting.md)
- [Entity reference](https://github.com/Chill-Division/HA-Irrigation-Strategy/blob/main/docs/ENTITIES.md)
- For developers: [how it fits together](https://github.com/Chill-Division/HA-Irrigation-Strategy/blob/main/docs/SYSTEM_OVERVIEW.md), [testing](https://github.com/Chill-Division/HA-Irrigation-Strategy/blob/main/docs/TESTING.md), [releasing](https://github.com/Chill-Division/HA-Irrigation-Strategy/blob/main/docs/RELEASING.md) and [contributing](https://github.com/Chill-Division/HA-Irrigation-Strategy/blob/main/CONTRIBUTING.md)

## Support

Report a problem or ask a question in [GitHub issues](https://github.com/Chill-Division/HA-Irrigation-Strategy/issues). Include the error code if there is one, both version numbers (shown in the Crop Steering sidebar), and what the controller app's log says.

## License

[MIT](https://github.com/Chill-Division/HA-Irrigation-Strategy/blob/main/LICENSE)

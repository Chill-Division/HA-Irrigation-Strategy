# Crop Steering Controller

This companion app runs the P0–P3 irrigation decision loop and sequences mapped pump/valve entities. Install the Crop Steering integration first; it owns room configuration, sensor mapping and grow-plan storage.

## Install and configure

Follow the [installation guide](https://github.com/Chill-Division/HA-Irrigation-Strategy/blob/main/docs/INSTALL.md). After installing this app, review Configuration, start it, and open the integration's **Crop Steering** sidebar page. The ingress dashboard is also available. Both serve the same native workspace.

Use **Settings → Rooms & hardware** for mapping and per-zone sizing. Keep engines off while commissioning. Fresh installations create engine controls; existing mapped enable flags are preserved. The legacy default-room helper may still be input_boolean.f2_control_enabled. The room descriptor/heartbeat identifies the actual flag; do not create a second one blindly.

## Plans and operation

**Irrigation plan → Schedule** supports per-zone day/week schedules and explicit vegetative/generative profiles. Saving is draft-only; arming makes a plan eligible at the next local lights-on boundary. It does not enable the engine. Active plans supply atomic versioned targets. Missing or expired required plans hold the plan's steering, including after restart; rescue and watchdog shots still water.

The controller retains interlock holds, duration/daily-volume caps and hardware state readback. Shared-hardware faults latch until implicated engines and hardware are off. State readback is not proof of physical delivery; verify sensors and actual flow on site.

## Visible targets and water

**Irrigation plan → Today** shows saved and draft targets beside the selected phase, on a graph that also draws the zone's recorded VWC and pore EC and the projected day. Compare runs overlays retained readings with daily target illustrations or earlier runs aligned by grow age. Stored references are timestamped; Recorder retention determines the available historical data.

Water cards distinguish total substrate capacity from all-plant zone litres and average mL per plant. The runtime calculator includes whole-second timing, the minimum shot and duration cap. Phase estimates also disclose engine parameter limits. Water delivered is counted from the flow configured when each shot ran and its elapsed runtime, partial aborts included.

## Its log

The app's **Log** tab has a line a minute for every zone, each dated and named as you named the room and zone: its phase, moisture, EC and water today, and what it waits for next. A phase change says why; a shot says what kind it is, how long it runs, about how much water it gives and why; a setting change says who made it, a person as Home Assistant knows them, Auto setpoints, or an automation by its name.

```
2026-10-01 06:59:02 GR2 · Bench 1 (Z1) · P3 · VWC 61.2% · EC 2.9 · 0.0 L today · holding · next: rescue shot if VWC < 35% (now 61%) · P0 at 07:00
2026-10-01 07:00:03 GR2 · Bench 1 (Z1) · P3 → P0: lights on
2026-10-01 07:01:04 GR2 · Bench 1 (Z1) · P0 → P1: VWC 61% is at or under the maintenance trigger (63%), no morning dryback needed
2026-10-01 07:01:04 GR2 · Bench 1 (Z1) · P1 ramp shot 2.5% for 72 s (~0.9 L): VWC 61% under the 88% peak target
2026-10-01 07:04:12 GR2 · Bench 1 (Z1) · Sam raised Most P1 shots to 10 (was 6)
```

## Updating

Update the integration and this app together. Use **Update** or **Rebuild** to include new Python code; restarting an old image does not rebuild it. Preserve persistent data and export plans before upgrades. See the installation guide for rollback instructions.

The display name is Crop Steering Controller. The existing f2_control slug remains stable for upgrade compatibility. The app and the integration carry one version number: run the same release of both. The dashboard sidebar shows both, as reported by the running parts. Local browser/unit checks do not constitute a live HA installation test.

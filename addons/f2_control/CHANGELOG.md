# Unreleased

- **Wording:** Auto setpoints, frozen, says an armed irrigation strategy owns the room's targets. **The dashboard the app serves:** Irrigation plan is now Irrigation strategy, its saved copies are kept in the Strategy library, and a recipe is always a feed recipe.
- **Feed EC:** a flush or diluting shot now waters with the feed recipe in use's Feed EC, from the integration's feed plan: a root zone saltier than that feed gets one. Without one it counts the feed as 3.0 mS/cm, as before. The root-zone EC hold (CS-206) says so. **The dashboard the app serves** has the Feed EC on each recipe.
- **Notifications:** the root-zone EC hold (CS-206) says what can lift it, and the setting-range warning (CS-401) no longer mentions the minimum daily volume. **Configuration:** the kill-switch option says that a room made by the setup wizard has its own watering switch, and the zone-count option that the zones come from the room's setup. **The dashboard the app serves:** the same corrections in its help and error codes. No change to how the controller waters.

# 1.0.0

Pair with integration 1.0.0.

- **Version 1.0.** The numbers start again at 1.0.0, after 2.37.1, for the first release published for everyone. No change to the controller.
- **The app's image carries the MIT licence**, and **the dashboard the app serves** ships the licences of its open-source libraries beside it (`THIRD_PARTY_LICENSES.txt`). No change to the controller.
- **The dashboard the app serves:** no What's new with the first-run tour. No change to the controller.
- **A new icon and logo in Settings → Apps:** a tank of water with a seedling in front of it, white on a blue tile. **The dashboard the app serves** has the same mark in its menu. No change to the controller.

import { afterEach, describe, expect, it, vi } from "vitest";
import { HaClient, type HassSession } from "./client";
import { buildRoom, discoverRooms, validateChange } from "./model";
import { createDemo } from "./demo";
import type { States } from "./types";
import type { OperatorAction } from "./operator-types";
import { errorText } from "./utils";

afterEach(() => vi.restoreAllMocks());
const REFUSAL =
  "switch.crop_steering_engine_enabled must read OFF before changing setup (it is ON: turn it off, then submit again)";
/** Inside Home Assistant: its frontend's session, with the websocket it is connected over. */
function insideHomeAssistant(sendMessagePromise: ReturnType<typeof vi.fn>) {
  const callApi = vi.fn(),
    callService = vi.fn();
  const session = {
    callApi,
    callService,
    connection: { subscribeMessage: vi.fn(), sendMessagePromise },
  } as HassSession;
  return { client: new HaClient("http://ha.test", "", session), callApi, callService };
}
describe("workspace response transport", () => {
  it("inside Home Assistant calls the integration over its websocket, with the response", async () => {
    const send = vi.fn().mockResolvedValue({ context: { id: "c" }, response: { revision: 2 } });
    const { client, callApi, callService } = insideHomeAssistant(send);
    const payload = { entry_id: "e", expected_revision: 1, room_name: "Growroom 2" };
    expect(await client.operator("setup_save", payload)).toEqual({ revision: 2 });
    expect(send).toHaveBeenCalledWith({
      type: "call_service",
      domain: "crop_steering",
      service: "setup_save",
      service_data: payload,
      return_response: true,
    });
    expect(callApi).not.toHaveBeenCalled();
    expect(callService).not.toHaveBeenCalled();
  });
  it("shows why Home Assistant refused a change, not a bare 500", async () => {
    // What Home Assistant's websocket sends back when the integration refuses: over REST the same
    // refusal was "500 Internal Server Error", and the page said "Response error: 500".
    const send = vi.fn().mockRejectedValue({ code: "home_assistant_error", message: REFUSAL });
    const { client } = insideHomeAssistant(send);
    const refused = await client.operator("setup_save", {}).catch((error: unknown) => error);
    expect(errorText(refused)).toBe(REFUSAL);
  });
  it("says an integration without the action needs updating", async () => {
    const send = vi
      .fn()
      .mockRejectedValue({
        code: "not_found",
        message: "Service crop_steering.feed_get not found.",
      });
    const { client } = insideHomeAssistant(send);
    await expect(client.operator("feed_get", { room_id: "room:" })).rejects.toThrow(
      /updated PHASE Steering/,
    );
  });
  it("outside Home Assistant, a refusal points at Home Assistant's log", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response("500 Internal Server Error\n\nServer got itself in trouble", { status: 500 }),
    );
    const client = new HaClient("http://ha.test", "token");
    await expect(client.operator("setup_save", {})).rejects.toThrow(
      /\(500\)\. Its log, under Settings → System → Logs, says why/,
    );
  });
  it("uses response-bearing REST in a session without Home Assistant's websocket", async () => {
    const callApi = vi
      .fn()
      .mockResolvedValue({ changed_states: [], service_response: { revision: 3 } });
    const callService = vi.fn();
    const client = new HaClient("http://ha.test", "", { callApi, callService } as HassSession);
    expect(await client.operator("strategy_get", { room_id: "room:f1_" })).toEqual({ revision: 3 });
    expect(callApi).toHaveBeenCalledWith(
      "POST",
      "services/crop_steering/strategy_get?return_response",
      { room_id: "room:f1_" },
    );
    expect(callService).not.toHaveBeenCalled();
  });
  it("sends the nutrient batch actions to the integration", async () => {
    const callApi = vi
      .fn()
      .mockResolvedValue({ changed_states: [], service_response: { revision: 1 } });
    const client = new HaClient("http://ha.test", "", { callApi, callService: vi.fn() } as never);
    for (const action of ["feed_get", "feed_save", "feed_mix"] as OperatorAction[])
      expect(await client.operator(action, { room_id: "room:f1_" })).toEqual({ revision: 1 });
    expect(callApi).toHaveBeenLastCalledWith(
      "POST",
      "services/crop_steering/feed_mix?return_response",
      { room_id: "room:f1_" },
    );
    // A zone's test shot, from Settings → Rooms & hardware → Tests.
    await client.operator("test_shot", { room_id: "room:f1_", zone: 2 });
    expect(callApi).toHaveBeenLastCalledWith(
      "POST",
      "services/crop_steering/test_shot?return_response",
      { room_id: "room:f1_", zone: 2 },
    );
  });
  it("rejects ordinary acknowledgements and unrecognized operations", async () => {
    const callApi = vi.fn().mockResolvedValue([]),
      callService = vi.fn();
    const client = new HaClient("http://ha.test", "", { callApi, callService } as HassSession);
    await expect(client.operator("strategy_save", {})).rejects.toThrow(/updated PHASE Steering/);
    await expect(client.operator("execute_irrigation_shot" as OperatorAction, {})).rejects.toThrow(
      /Unsupported/,
    );
    expect(callApi).toHaveBeenCalledTimes(1);
  });
});
function activePlan(states: States) {
  const id = "sensor.crop_steering_strategy_plan";
  states[id] = {
    entity_id: id,
    state: "active",
    attributes: {
      snapshot_version: 1,
      room_id: "room:",
      enabled: true,
      updated_at: new Date().toISOString(),
      valid_until: new Date(Date.now() + 180000).toISOString(),
      zones: [
        {
          zone_id: 1,
          status: "active",
          parameters: {
            p1_target_vwc: 71,
            p2_vwc_threshold: 49,
            ec_target_p1: 4.2,
            ec_target_p2: 5.2,
          },
        },
      ],
    },
  };
  states["sensor.crop_steering_zone_1_phase"] = {
    entity_id: "sensor.crop_steering_zone_1_phase",
    state: "P2",
    attributes: {},
  };
  return states[id];
}
describe("active plan presentation and lifecycle", () => {
  it("shows atomic plan targets and refuses conflicting manual writes", () => {
    const states = createDemo();
    activePlan(states);
    const room = buildRoom(
      states,
      discoverRooms(states).find((r) => r.id === "room:")!,
    );
    expect(room.strategy.valid).toBe(true);
    expect(room.zones[0].target.value).toBe(49);
    expect(room.zones[0].ecTarget.value).toBe(5.2);
    expect(
      validateChange(room, states, {
        entityId: "number.crop_steering_zone_1_p1_target_vwc",
        value: 60,
      }),
    ).toMatch(/active irrigation strategy/);
  });
  it("never presents old manual targets as active after expiry or wrong room identity", () => {
    for (const bad of ["expired", "wrong-room"]) {
      const states = createDemo(),
        snapshot = activePlan(states);
      if (bad === "expired")
        snapshot.attributes.valid_until = new Date(Date.now() - 1).toISOString();
      else snapshot.attributes.room_id = "room:f1_";
      const room = buildRoom(
        states,
        discoverRooms(states).find((r) => r.id === "room:")!,
      );
      expect(room.strategy.valid).toBe(false);
      expect(room.zones[0].target.value).toBeNull();
      expect(room.zones[0].ecTarget.value).toBeNull();
      expect(
        room.alerts.some((a) => a.severity === "critical" && a.title.includes("snapshot")),
      ).toBe(true);
    }
  });
  it("preserves zone identities after archival and hides archived rooms", () => {
    const states = createDemo(),
      descriptor = states["sensor.crop_steering_engine_config"];
    descriptor.attributes.active_zone_ids = [1, 3];
    descriptor.attributes.zone_names = { "3": "East bench" };
    const room = buildRoom(
      states,
      discoverRooms(states).find((r) => r.id === "room:")!,
    );
    expect(room.zones.map((z) => z.id)).toEqual([1, 3]);
    expect(room.zones[1].name).toBe("East bench");
    descriptor.attributes.active = false;
    expect(discoverRooms(states).some((r) => r.id === "room:")).toBe(false);
  });
});

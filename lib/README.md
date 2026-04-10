# `lib/` — shared Minescript utilities

This package holds reusable helpers for Hypixel Skyblock (and similar) automation scripts: camera and movement, timing, raycasting, optional world overlays, a vendored **Minescript Plus** API, and background **services** for safety and monitoring.

Scripts typically import with the `lib` prefix, for example `import lib.movement as movement`, assuming the Minescript working directory includes the parent folder on `PYTHONPATH` (as in this repo layout).

## Dependencies

Most modules expect:

- **`minescript`** — core mod API (`player_position`, `entities`, key presses, etc.).
- **`core`** — project package (`core.constants`, `core.state`, `core.api_lock`).

**`minescript_plus.py`** additionally requires Minecraft mappings under `minescript/system/mappings/<version>/` (install via `\install_mappings` in-game if missing). Optional **`lib_nbt`** extends inventory helpers that parse SNBT.

**`worldrender.py`** targets **Minecraft 1.21.11+** and uses client gizmos via embedded Pyjinn; it is separate from vanilla Minescript block APIs.

---

## Top-level modules

| Module | Purpose |
|--------|---------|
| **`lib.py`** | Small helpers; currently `play_alert_sound()` using Minescript Plus sounds. |
| **`minescript_plus.py`** | Vendored **Minescript Plus** (RazrCraft): Java bridge, `Inventory`, `Screen`, `Gui`, `Key`, `Client`, `Player`, `Server`, `World`, `Trading`, `Util`, `Hud` (Fabric), events, keybinds, etc. See the module docstring for version and requirements. |
| **`humanization.py`** | Human-like delays and noise: `human_delay()`, `generate_smooth_noise()`, `generate_look_offset()`. |
| **`orientation.py`** | Camera math and smoothing: aim deltas, Bezier-smoothed looks, entity tracking, frustum-style `is_in_front_of_player()`, line sampling `raycast()`, distance helper, and humanized `look()` / `look_at()` (community-derived look model; see in-file credit). Uses `core.constants.PLAYER_EYE_HEIGHT`. |
| **`movement.py`** | Key-based movement state: `moving` dict, `stop_all_movement()`, `start_movement()`, sprint/fly helpers, `fly_to_height()`, `move_to_waypoint()` (uses `lib.orientation` and `core.state` events). |
| **`session.py`** | `SessionScheduler` — session length, scheduled breaks, optional disconnect at end (`minescript_plus.Client.disconnect`), integrates with `core.state` pause/run events and `lib.movement`. |
| **`raycast.py`** | DDA ray against the world: `Ray` class and `raycast_block_subregions()` (samples sub-voxels, returns best-facing yaw/pitch). Uses `core.api_lock.java_lock` around `minescript.getblock`. |
| **`worldrender.py`** | Static `WorldRender` API: world-space boxes, block highlights, billboard text, points, lines, arrows, circles, quads; toggle visibility and optional F12-style toggle key. Implemented with `eval_pyjinn_script` + render listener. |

---

## `lib/services/`

Infrastructure for long-running background threads that cooperate with bot lifecycle (`start` / `stop` / `pause` / `resume`).

| File | Role |
|------|------|
| **`base_service.py`** | `BaseService` — daemon thread loop calling `run_step()` on an interval; swallows exceptions in the loop to stay alive. |
| **`service_registry.py`** | `ServiceRegistry` — register, start/stop/pause/resume individual services or all. |
| **`service_context.py`** | Global `SERVICE_REGISTRY`, `register_service()`, context managers `pause_services()` and `pause_temporarily()`, `update_state_driven_pause()` to tie pause state to `bot_active` / `pause_event` / `run_event`. |
| **`__init__.py`** | Re-exports registry helpers and `BaseService`. |
| **`proximity_monitor_service.py`** | `ProximityMonitorService` — tracks nearby players without “farming” tools; after repeated suspicion, pauses and runs a scripted evade (`/hub`). |
| **`teleport_failsafe_service.py`** | `TeleportFailsafeService` — compares position/rotation each tick to a baseline; large jumps trigger failsafe (disconnect / exit). Optional `alarm_event` callback. |
| **`chat_monitor_service.py`** | `ChatMonitorService` — chat + action bar mention handling. **Note:** this file still imports `constants`, `state`, and `services.base_service` as top-level names; if you use it from this tree, align imports with `core.*` and `lib.services.*` like the other services. |

---

## Typical usage patterns

- **Smooth camera toward a block:** `lib.orientation.smooth_look_at_block(pos, duration_min, duration_max)`.
- **Humanized turn to yaw/pitch or block:** `lib.orientation.look()` / `lib.orientation.look_at(x, y, z)`.
- **Movement cleanup:** `lib.movement.stop_all_movement()` before disconnect or pause.
- **Register a service:** `from lib.services import register_service` then `register_service(MyService(...))` and `SERVICE_REGISTRY.start("my_id")` (or start via your script bootstrap).
- **World debug overlay:** `from lib.worldrender import WorldRender` then `WorldRender.add_line(...)` etc.

For full API detail, prefer reading docstrings in **`minescript_plus.py`** and **`worldrender.py`**; those files are the largest and most feature-rich.

## Maintenance notes

- **`orientation.py`:** The humanized `look` / `look_at` / `get_axes` path and `raycast()` call into Minescript using the name `m` (e.g. `m.player_set_orientation`). The file only imports `minescript`; add `m = minescript` or replace `m.` with `minescript.` if you see `NameError`. The `@dataclass` block also needs `from dataclasses import dataclass` if you use that section.
- **`session.py`:** `human_delay()` does not return a duration; code that assigns its result for logging may need a separate `time.sleep` + measured elapsed time for breaks.

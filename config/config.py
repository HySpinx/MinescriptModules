from __future__ import annotations

from pathlib import Path
from typing import Any

from config.config_lib import Config

DEFAULT_CONFIG = {
    "player": {
        "eye_height": 1.62,
    },
    "timing": {
        "min_slot_switch_delay": 0.05,
        "max_slot_switch_delay": 0.1,
        "min_delay": 0.07,
        "max_delay": 0.15,
        "min_hold_delay": 0.02,
        "max_hold_delay": 0.09,
        "min_click_delay": 0.02,
        "max_click_delay": 0.09,
        "min_swing_cooldown": 0.5,
        "max_swing_cooldown": 0.9,
    },
    "lib": {
        "direction_opposites": {
            "left": "right",
            "right": "left",
            "forward": "backward",
            "backward": "forward",
            "diagonal-left-forward": "diagonal-right-backward",
            "diagonal-right-forward": "diagonal-left-backward",
            "diagonal-left-backward": "diagonal-right-forward",
            "diagonal-right-backward": "diagonal-left-forward",
        }
    },
    "farming": {
        "pause_key": 80,
        "enable_mob_killer": True,
        "hub_detection_enabled": True,
        "check_interval_seconds": 0.25,
        "distance_moved_threshold": 0.03,
        "required_stuck_ticks": 5,
        "hub_chat_message": "Sending to server",
        "auto_pause_messages": [
            "wth?",
            "whyy",
            "bruh",
            "brah",
            "Let me farm brah",
            "why.",
            "wth",
            "bruhhhh",
            "brahhh",
            "...bruhh",
            "Huh?",
            "Cmon man.",
            "Seriously?",
            "Brooo",
            "Ughhh",
            "Still here.",
            "Hello?",
        ],
        "valid_pest_names": ["beetle", "locust", "mite", "mosquito", "rat", "slug", "fly", "moth", "worm"],
        "pest_detection_radius": 13.0,
        "pest_kill_radius": 15.0,
        "tool_slot": 0,
        "snap_look_slot": 1,
        "vacuum_slot": 3,
        "presets": {
            "crops": {
                "name": "Crops Farm",
                "description": "Left/Right alternating",
                "rows": 1,
                "warp_command": "/warp garden",
                "reverse_pattern": False,
                "has_drops": False,
                "pattern": [
                    [("forward" if (i % 4 == 0) or (i % 4 == 2) else "left" if i % 4 == 1 else "right"), i + 1]
                    for i in range(32)
                ],
                "speed": 93,
                "pitch": 0,
                "yaw": -90,
            },
            "cane": {
                "name": "Sugar Cane/Sunflower Farm",
                "description": "Hold Left, switch to Backward at wall",
                "rows": 1,
                "warp_command": "/warp garden",
                "reverse_pattern": False,
                "has_drops": False,
                "pattern": [[("left" if i % 2 == 0 else "backward"), i + 1] for i in range(31)],
                "speed": 328,
                "pitch": 0,
                "yaw": -135,
            },
            "mushroom": {
                "name": "Mushroom Farm",
                "description": "Hold Left+Forward -> Hold Backward -> Hold Right",
                "rows": 8,
                "warp_command": "/warp garden",
                "reverse_pattern": False,
                "has_drops": False,
                "pattern": [["left", 1], ["diagonal-right-backward", 2]],
                "speed": 232,
                "pitch": 5.5,
                "yaw": -106,
            },
        },
    },
    "mining": {
        "target_blocks": [
        "minecraft:prismarine",
        "minecraft:dark_prismarine",
        "minecraft:light_gray_conrete",
        "minecraft:grey_wool",
        "minecraft:gold_block",
        "minecraft:polished_diorite",
        "minecraft:light_blue_wool"
        ],
        "ignore_block_state": False,
        "search_distance": 4,
        "rotation_duration": [0.5, 1.2],
        "rotation_steps": 90,
        "block_cooldown": 0.05,
        "auto_rescan": True,
        "rescan_key": 89,
        "use_cluster_mode": True,
        "break_blocks": True,
        "break_delay": 0.0,
        "use_smart_targeting": True,
        "max_wait": 7.0,
        "wait_time": 0.0,
        "check_interval": 0.05,
        "ability_on": True,
        "min_ability_cooldown": 61.0,
        "max_ability_cooldown": 65.0,
        "transparent_blocks": {
            "minecraft:air", 
            "minecraft:cave_air", 
            "minecraft:void_air", 
            "minecraft:water"
        },
    },
    "fishing": {
        "attack_clicks": 3,
        "attack_slot": 0,
        "hold_use_duration": 0.05,
        "name_marker": "!!!",
        "panic_key": 80,
        "per_cycle": 10,
        "pitch_tolerance": 1.0,
        "pos_tolerance": 0.05,
        "rod_slot": 0,
        "target_block_distance": 15.0,
        "timeout": 10.0,
        "toggle_key": 80,
        "use_hold_attack_mode": True,
        "yaw_tolerance": 1.0,
    },
    "render": {
        "enable_debug_rendering": True,
    },
}

def _merge_missing(current: dict[str, Any], defaults: dict[str, Any]) -> bool:
    changed = False
    for key, default_val in defaults.items():
        if key not in current:
            current[key] = default_val
            changed = True
            continue
        if isinstance(current[key], dict) and isinstance(default_val, dict):
            changed = _merge_missing(current[key], default_val) or changed
    return changed


CONFIG_PATH = Path(__file__).resolve().parent / "config.json"
cfg = Config(str(CONFIG_PATH), autosave=False)
if _merge_missing(cfg._data, DEFAULT_CONFIG):
    cfg.save()

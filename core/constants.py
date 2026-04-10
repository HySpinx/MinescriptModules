from config.config import cfg


def _tuple_list(values):
    return [tuple(v) for v in values]


player = cfg._data["player"]
timing = cfg._data["timing"]
farming = cfg._data["farming"]
mining = cfg._data["mining"]
fishing = cfg._data["fishing"]
lib_cfg = cfg._data["lib"]

# Player constants
PLAYER_EYE_HEIGHT = player["eye_height"]

# Timing Constants
TIME_MIN_SLOT_SWITCH_DELAY = timing["min_slot_switch_delay"]
TIME_MAX_SLOT_SWITCH_DELAY = timing["max_slot_switch_delay"]
TIME_MIN_DELAY = timing["min_delay"]
TIME_MAX_DELAY = timing["max_delay"]
TIME_MIN_HOLD = timing["min_hold"]
TIME_MAX_HOLD = timing["max_hold"]
TIME_MIN_CLICK_DELAY = timing["min_click_delay"]
TIME_MAX_CLICK_DELAY = timing["max_click_delay"]
TIME_MIN_SWING_COOLDOWN = timing["min_swing_cooldown"]
TIME_MAX_SWING_COOLDOWN = timing["max_swing_cooldown"]

# Farming constants
FARM_PAUSE_KEY = farming["pause_key"]
FARM_ENABLE_MOB_KILLER = farming["enable_mob_killer"]
FARM_HUB_DETECTION_ENABLED = farming["hub_detection_enabled"]
FARM_HUB_CHAT_MESSAGE = farming["hub_chat_message"]
FARM_AUTO_PAUSE_MESSAGES = list(farming["auto_pause_messages"])
FARM_VALID_PEST_NAMES = list(farming["valid_pest_names"])
FARM_PEST_DETECTION_RADIUS = farming["pest_detection_radius"]
FARM_PEST_KILL_RADIUS = farming["pest_kill_radius"]
FARM_TOOL_SLOT = farming["tool_slot"]
FARM_SNAP_LOOK_SLOT = farming["snap_look_slot"]
FARM_VACUUM_SLOT = farming["vacuum_slot"]
FARM_CHECK_INTERVAL_SECONDS = farming["check_interval_seconds"]
FARM_DISTANCE_MOVED_THRESHOLD = farming["distance_moved_threshold"]
FARM_REQUIRED_STUCK_TICKS = farming["required_stuck_ticks"]
FARM_PRESETS = {
    preset_name: {
        key: _tuple_list(value) if key == "pattern" else value
        for key, value in preset_data.items()
    }
    for preset_name, preset_data in farming["presets"].items()
}

# Lib movement constants
LIB_DIRECTION_OPPOSITES = dict(lib_cfg["direction_opposites"])

# Mining constants
MINING_TARGET_BLOCKS = list(mining["target_blocks"])
MINING_IGNORE_BLOCK_STATE = mining["ignore_block_state"]
MINING_SEARCH_DISTANCE = mining["search_distance"]
MINING_ROTATION_DURATION_MIN = mining["rotation_duration"][0]
MINING_ROTATION_DURATION_MAX = mining["rotation_duration"][1]
MINING_ROTATION_STEPS = mining["rotation_steps"]
MINING_BLOCK_COOLDOWN = mining["block_cooldown"]
MINING_AUTO_RESCAN = mining["auto_rescan"]
MINING_RESCAN_KEY = mining["rescan_key"]
MINING_USE_CLUSTER_MODE = mining["use_cluster_mode"]
MINING_BREAK_BLOCKS = mining["break_blocks"]
MINING_BREAK_DELAY = mining["break_delay"]
MINING_USE_SMART_TARGETING = mining["use_smart_targeting"]
MINING_MAX_WAIT = mining["max_wait"]
MINING_WAIT_TIME = mining["wait_time"]
MINING_CHECK_INTERVAL = mining["check_interval"]
MINING_ABILITY_ON = mining["ability_on"]
MINING_MIN_ABILITY_COOLDOWN = mining["min_ability_cooldown"]
MINING_MAX_ABILITY_COOLDOWN = mining["max_ability_cooldown"]
MINING_TRANSPARENT_BLOCKS = set(mining["transparent_blocks"])

# Fishing constants
FISH_ATTACK_CLICKS = fishing["attack_clicks"]
FISH_ATTACK_SLOT = fishing["attack_slot"]
FISH_HOLD_USE_DURATION = fishing["hold_use_duration"]
FISH_NAME_MARKER = fishing["name_marker"]
FISH_PANIC_KEY = fishing["panic_key"]
FISH_PER_CYCLE = fishing["per_cycle"]
FISH_PITCH_TOLERANCE = fishing["pitch_tolerance"]
FISH_POS_TOLERANCE = fishing["pos_tolerance"]
FISH_ROD_SLOT = fishing["rod_slot"]
FISH_TARGET_BLOCK_DISTANCE = fishing["target_block_distance"]
FISH_TIMEOUT = fishing["timeout"]
FISH_TOGGLE_KEY = fishing["toggle_key"]
FISH_USE_HOLD_ATTACK_MODE = fishing["use_hold_attack_mode"]
FISH_YAW_TOLERANCE = fishing["yaw_tolerance"]

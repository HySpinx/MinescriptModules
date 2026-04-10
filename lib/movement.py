
import minescript
import time
import random
import lib.humanization as human
import lib.orientation as orientation

from core.constants import LIB_DIRECTION_OPPOSITES
from core.state import bot_active, run_event

# ==========================================
# 1. GLOBAL STATE VARIABLES
# ==========================================

DIRECTION_OPPOSITES = LIB_DIRECTION_OPPOSITES

moving = {
    "left": False,
    "right": False,
    "forward": False,
    "backward": False,
    "sneak": False,
    "jump": False,
    "sprint": False,
    "fly": False
}

# Standard mappings for minescript keys
_MOVEMENT_KEY_RELEASE = {
    "left": minescript.player_press_left,
    "right": minescript.player_press_right,
    "forward": minescript.player_press_forward,
    "backward": minescript.player_press_backward,
    "sneak": minescript.player_press_sneak,
    "jump": minescript.player_press_jump,
    # Sprint logic depends on Minescript version, defaulting to standard sneak/jump format
    "sprint": getattr(minescript, 'player_press_sprint', lambda x: None) ,
    "fly": minescript.player_press_sneak,
}

# ==========================================
# 2. PLAYER BASIC MOVEMENT FUNCTIONS
# ==========================================
def stop_all_movement(): # Stop moving and clicking
    for direction_key, is_active in moving.items():
        if is_active:
            _MOVEMENT_KEY_RELEASE[direction_key](False)
            moving[direction_key] = False
    stop_attack()
    stop_use()

def stop_directional_movement(): # Stop moving along the x,y,z
    for direction_key, is_active in moving.items():
        if is_active:
            _MOVEMENT_KEY_RELEASE[direction_key](False)
            moving[direction_key] = False

def reverse_direction(direction): # Inverts the direction provided
    return DIRECTION_OPPOSITES.get(direction, direction)

def start_movement(direction): # Initiates movement in the direction provided
    needs_pressing = []
    # Parse the requested string for any supported actions
    for key in _MOVEMENT_KEY_RELEASE.keys():
        if key in direction.lower():
            needs_pressing.append(key)

    overlap_keys = random.random() < 0.5 # Add in key overlap to look more human
    if overlap_keys:
        for key in needs_pressing:
            if not moving[key]:
                _MOVEMENT_KEY_RELEASE[key](True)
                moving[key] = True
        time.sleep(random.uniform(0.05, 0.1)) 

    for current_key, is_active in moving.items():
        if is_active and current_key not in needs_pressing:
            _MOVEMENT_KEY_RELEASE[current_key](False)
            moving[current_key] = False

    if not overlap_keys:
        time.sleep(random.uniform(0.05, 0.1)) 
        for key in needs_pressing:
            if not moving[key]:
                _MOVEMENT_KEY_RELEASE[key](True)
                moving[key] = True

def toggle_fly(): #Double jump
    minescript.player_press_jump(True); human.human_delay(0.07, 0.1)
    minescript.player_press_jump(False); human.human_delay(0.07, 0.1)
    minescript.player_press_jump(True); human.human_delay(0.07, 0.1)
    minescript.player_press_jump(False); human.human_delay(0.07, 0.1)

def start_sprint():
    minescript.player_press_sprint(True)

def stop_sprint():
    minescript.player_press_sprint(False)

def start_attack():
    minescript.player_press_attack(True)

def stop_attack():
    minescript.player_press_attack(False)

def start_use():
    minescript.player_press_use(True)

def stop_use():
    minescript.player_press_use(False)

# ==========================================
# 3. ADVANCED MOVEMENT FUNCTIONS
# ==========================================

def fly_to_height(target_height, tolerance=0.5, check_interval=0.05):
    """Ascend smoothly to target height without spamming fly()."""

    # get current Y
    y = minescript.player_position().y

    # only tap fly once if we’re below target
    if y < target_height - tolerance:
        toggle_fly()  # enter flying mode once
        minescript.player_press_jump(True)
    else:
        minescript.player_press_jump(False)
        return

    # keep ascending until we reach height
    while bot_active.is_set() and run_event.is_set():
        y = minescript.player_position().y
        if y >= target_height - tolerance:
            minescript.player_press_jump(False)
            break
        time.sleep(check_interval)

    minescript.player_press_jump(False)

def move_to_waypoint(waypoint):
    w_x, w_y, w_z = waypoint
    w_x += random.uniform(-7, 7)
    w_y += random.uniform(-.5, 2)
    w_z += random.uniform(-7, 7)
    while bot_active.is_set() and run_event.is_set():
        player_x, player_y, player_z = minescript.player_position()
        orientation.smooth_look_at_block((w_x, w_y, w_z), 0.5, 0.9)
        if abs(player_x - w_x) < 0.01 and abs(player_z - w_z) < 0.01:
            minescript.player_press_forward(False); minescript.player_press_left(False); minescript.player_press_right(False)
            return True
        dx = dz = 0
        if player_x: dx = w_x - player_x; dz = w_z - player_z
        minescript.player_press_forward(abs(dx) > abs(dz)); minescript.player_press_left(dz > 0); minescript.player_press_right(dz < 0)
        human.human_delay(0.05, 0.1)
    minescript.player_press_forward(False); minescript.player_press_left(False); minescript.player_press_right(False)
    return False
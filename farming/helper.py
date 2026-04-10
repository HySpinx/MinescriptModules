import minescript
import lib.minescript_plus as minescript_plus
import time
import lib.humanization as human
import lib.movement as move
import lib.orientation as orient

from core.constants import (
    PLAYER_EYE_HEIGHT,
)

# Player configs
EYE_HEIGHT = PLAYER_EYE_HEIGHT

# Timing configs

def get_inventory_hash():
    inventory = minescript.player_inventory()
    return "".join(f"{item.item}:{item.count}:{item.slot}|" for item in inventory)

def squeeker_snap(squeeker_slot, config):
    # Ensure the squeeker isn't accidently activated
    move.stop_attack()
    move.stop_use()

    # Select the squeeker
    human.do_normal_delay()
    minescript.player_inventory_select_slot(squeeker_slot)
    human.do_slot_switch_delay()

    move.start_attack()
    human.do_click_delay()

    move.stop_attack()
    human.do_normal_delay()
    
    # Confirm that the squeeker worked
    minescript_plus.Screen.close_screen() # Ensure the screen isn't in the sign GUI

    time.sleep(.075)
    expected_pitch = config["pitch"]
    expected_yaw = config["yaw"]
    current_pitch = minescript.player().pitch
    current_yaw = minescript.player().yaw
    squeeker_worked = (expected_pitch == current_pitch and expected_yaw == current_yaw) # Returns True if the squeeker worked, False if it didn't

    
    if squeeker_worked:
        return True
    else:
        squeeker_snap(squeeker_slot, config)

def return_to_farming(original_x, original_y, original_z, config):
    # Cleanup step
    # Return to x, y, z of player's original position
    orient.smooth_look_at_block((original_x, original_y + EYE_HEIGHT, original_z), 0.5, 0.9)
    move.move_to_waypoint(original_x, original_y, original_z)
    move.stop_all_movement()

    # Squeeker snap
    squeeker_snap(config["snap_look_slot"], config)
    move.start_movement("forward")
    human.do_normal_delay()
    move.stop_all_movement()
    # Back in original position

    human.do_normal_delay()
    minescript.player_inventory_select_slot(config["tool_slot"])
    human.do_slot_switch_delay()

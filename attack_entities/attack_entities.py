import minescript
import lib
import lib.orientation as orient
import random
import time
import math
import lib.humanization as human

# Import your existing global states and pause handler
from core.state import bot_active, check_pause
from core.constants import TIME_MIN_CLICK_DELAY, TIME_MAX_CLICK_DELAY, TIME_MIN_SWING_COOLDOWN, TIME_MAX_SWING_COOLDOWN

# ==========================================
# CONFIGURATION
# ==========================================
CLICK_HOLD_MIN = TIME_MIN_CLICK_DELAY
CLICK_HOLD_MAX = TIME_MAX_CLICK_DELAY
SWING_COOLDOWN_MIN = TIME_MIN_SWING_COOLDOWN
SWING_COOLDOWN_MAX = TIME_MAX_SWING_COOLDOWN

# ==========================================
# COMBAT LOGIC
# ==========================================
def get_entity(distance=4.0):
    return minescript.player_get_targeted_entity(distance)

def attack_entity():
    entities = minescript.entities(max_distance=8.0)
    target = get_entity()
    entity_in_front = False

    player_orientation = minescript.player_orientation()
    player_pos = minescript.player_position()

    for entity in entities:
        if orient.is_in_front_of_player(player_orientation, player_pos, entity.position):
            entity_in_front = True

            entity_pos = (entity.position[0], entity.position[1], entity.position[2])
            player_pos = (player_pos[0], player_pos[1], player_pos[2])

            if math.dist(entity_pos, player_pos) < 4.0:
                # "Bad attack" / Intentional missed swing logic (10% chance)
                if random.random() < 0.1: # 10% chance to miss
                    minescript.player_press_attack(True)
                    human.human_delay(CLICK_HOLD_MIN, CLICK_HOLD_MAX)
                    minescript.player_press_attack(False)
                    human.human_delay(SWING_COOLDOWN_MIN, SWING_COOLDOWN_MAX)
                    continue
    if target:
        minescript.player_press_attack(True)
        human.human_delay(CLICK_HOLD_MIN, CLICK_HOLD_MAX)
        minescript.player_press_attack(False)
        
        human.human_delay(SWING_COOLDOWN_MIN, SWING_COOLDOWN_MAX)
        return True
    return False

# ==========================================
# MAIN LOOP
# ==========================================
def main():
    minescript.echo("Auto-Attack loaded and waiting for global run state.")
    
    # Run as long as the global bot_active event is set
    while bot_active.is_set():
        
        # 1. Yield to the global pause state
        # If your master controller sets pause_event, this function will
        # block execution here until run_event is set again.
        check_pause()
            
        # 2. Check and attack if target exists
        attack_entity()
        
        # 3. General loop buffer to prevent CPU maxing
        human.human_delay(0.05, 0.15)

if __name__ == "__main__":
    main()
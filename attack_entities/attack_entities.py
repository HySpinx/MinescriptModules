import minescript
import lib.orientation as orient
import random
import math
import lib.humanization as human
import lib.movement as move

# Import your existing global states and pause handler
from core.state import bot_active, check_pause

# ==========================================
# CONFIGURATION
# ==========================================

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
                    move.start_attack()
                    human.do_click_delay()
                    move.stop_attack()
                    human.do_click_cooldown()
                    continue
    if target:
        move.start_attack()
        human.do_click_delay()
        move.stop_attack()
        
        human.do_click_cooldown()
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
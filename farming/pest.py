import minescript
import time
import math
import random
import helper
import lib.humanization as human
import lib.movement as move
import lib.orientation as orient

from core.constants import (
    PLAYER_EYE_HEIGHT,

    FARM_VALID_PEST_NAMES,
    FARM_ENABLE_MOB_KILLER,
    FARM_PEST_DETECTION_RADIUS,
    FARM_PEST_KILL_RADIUS,
    FARM_TOOL_SLOT,
    FARM_SNAP_LOOK_SLOT,
    FARM_VACUUM_SLOT,

)
from core.state import restart_event, check_pause

# ==========================================
# 1. CONFIG VARIABLES
# ==========================================

# Player configs
EYE_HEIGHT = PLAYER_EYE_HEIGHT

# Pest configs
VALID_PEST_NAMES = FARM_VALID_PEST_NAMES
ENABLE_MOB_KILLER = FARM_ENABLE_MOB_KILLER
PEST_DETECTION_RADIUS = FARM_PEST_DETECTION_RADIUS  
PEST_KILL_RADIUS = FARM_PEST_KILL_RADIUS

# Farming Configs
TOOL_SLOT = FARM_TOOL_SLOT
SNAP_LOOK_SLOT = FARM_SNAP_LOOK_SLOT
VACUUM_SLOT = FARM_VACUUM_SLOT

#Timing configs

# ==========================================
# 2. GLOBAL STATE VARIABLES
# ==========================================

# ==========================================
# 3. FUNCTIONS
# ==========================================

def scan_for_pests():
    # Scan for pests within the detection radius

    if restart_event.is_set() or not ENABLE_MOB_KILLER:
        return False

    all_entities = minescript.entities(max_distance=PEST_DETECTION_RADIUS) # Detection radius
    all_mobs = []

    for entity in all_entities:
        if not hasattr(entity, 'id'): # Skip entities that don't have an ID
            continue
    
        entity_type = entity.type.lower()
        entity_name = getattr(entity, 'name', str(entity)).lower()

        is_valid_type = "armor_stand" in entity_type
        is_pest_name = any(pest in entity_name for pest in VALID_PEST_NAMES)

        if is_valid_type and is_pest_name:
            all_mobs.append(entity)

    if not all_mobs:
        return False

    else:
        return all_mobs

def attack_nearby_pests(config):
    # Attack a pest within the kill radius
    player_data = minescript.player()
    all_mobs = scan_for_pests()

    pest = min(all_mobs, key=lambda entity: math.dist(player_data.position, entity.position))
    minescript.echo(f"Targeting pest: {getattr(pest, 'name', pest.type)} (ID: {pest.id})")

    move.stop_all_movement()
    original_x, original_y, original_z = minescript.player_position() # Record player position
    human.do_normal_delay()

    # Select the vacuum
    minescript.player_inventory_select_slot(FARM_VACUUM_SLOT)
    human.do_slot_switch_delay()

    while all_mobs:
        all_mobs = scan_for_pests()
        if all_mobs:
            pest = min(all_mobs, key=lambda entity: math.dist(player_data.position, entity.position))

            # Determine coordinates to aim at with offset so we don't snap to the same position every time
            body_offset_x, body_offset_y, body_offset_z = human.generate_look_offset(-0.2, 0.2, 0.2, 0.6, -0.2, 0.2)
            pest_x, pest_y, pest_z = pest.position

            # Start Vacuum
            move.start_use()

            # Move the camera to the pest's position
            orient.smooth_look_at_block((pest_x + body_offset_x, pest_y + body_offset_y, pest_z + body_offset_z), 0.5, 0.9)

            # Dynamic polling function for the tracker
            target_id = pest.id
            def get_pest_pos():
                global last_inventory_change_time, stuck_counter

                for entity in minescript.entities(max_distance=PEST_KILL_RADIUS): # We extend the kill radius to account for movement
                    pause_duration = check_pause()
                    if pause_duration > 0:
                        last_inventory_change_time += pause_duration
                        stuck_counter = 0
                        continue
                    if entity.id == target_id:
                        player_pos = minescript.player_position()
                        player_coords = (player_pos[0], player_pos[1], player_pos[2])
                        entity_coords = (entity.position[0], entity.position[1], entity.position[2])

                        distance = math.dist(player_coords, entity_coords)
                        if distance > 5.0: # If the pest is too far away, move forward
                            move.start_movement("forward")
                        else: # If the pest is too close, stop moving
                            move.stop_directional_movement()
                        
                        # Coordinates for entity tracking
                        return (
                            entity.position[0] + body_offset_x, 
                            entity.position[1] + body_offset_y, 
                            entity.position[2] + body_offset_z
                        )
                move.stop_directional_movement()
                return None # Return None if the entity dies or vanishes

            # Engage the LERP tracker
            # Script will pause up to 4 seconds while the tracker is engaged
            # It will automatically exit this line if the pest dies or exits range
            scale = random.betavariate(2.0, 5.0)
            max_duration = 3.5 + (scale * (4.0 - 3.5))
            pest_pos = get_pest_pos()
            player_pos = minescript.player_position()
            distance = math.dist(pest_pos, player_pos)
            if distance < 5:
                move.stop_directional_movement()
            else:
                move.start_movement("forward")
            orient.track_entity_smoothly(get_target_pos_func=get_pest_pos, duration=max_duration, smoothing=0.1)

    # Pest either dead or out of range, stop vacuum
    move.stop_use()
    human.do_normal_delay()

    helper.return_to_farming(original_x, original_y, original_z, config)

    return True
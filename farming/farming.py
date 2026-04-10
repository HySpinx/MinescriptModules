import math
import random
import sys
import time

import helper
import minescript
import lib.lib as lib
import lib.humanization as human
import lib.movement as move
import lib.orientation as orient
import pest
from lib.session import SessionScheduler

from core.constants import (
    FARM_AUTO_PAUSE_MESSAGES,
    FARM_CHECK_INTERVAL_SECONDS,
    FARM_DISTANCE_MOVED_THRESHOLD,
    FARM_HUB_CHAT_MESSAGE,
    FARM_HUB_DETECTION_ENABLED,
    FARM_PAUSE_KEY,
    FARM_PRESETS,
    FARM_REQUIRED_STUCK_TICKS,
    FARM_SNAP_LOOK_SLOT,
    TIME_MAX_DELAY,
    TIME_MIN_DELAY,
)
from core.state import check_pause, pause_event, restart_event, run_event
from lib.services import BaseService
from lib.services.service_context import register_service

# Timing configs
MIN_DELAY = TIME_MIN_DELAY
MAX_DELAY = TIME_MAX_DELAY

# Change Direction Configs
CHECK_INTERVAL_SECONDS = FARM_CHECK_INTERVAL_SECONDS
DISTANCE_MOVED_THRESHOLD = FARM_DISTANCE_MOVED_THRESHOLD
REQUIRED_STUCK_TICKS = FARM_REQUIRED_STUCK_TICKS

# Farm Configs
PAUSE_KEY = FARM_PAUSE_KEY
HUB_DETECTION_ENABLED = FARM_HUB_DETECTION_ENABLED
HUB_CHAT_MESSAGE = FARM_HUB_CHAT_MESSAGE
FARM_SNAP_LOOK_SLOT = FARM_SNAP_LOOK_SLOT

# ==========================================
# 2. FARMING FUNCTIONS
# ========================================== 

def harvest_row(direction, row_num, config, scheduler=None):
    if config.get("reverse_pattern", False):
        direction = move.reverse_direction(direction)

    minescript.echo(f"Row {row_num}: Moving {direction}")

    last_inventory = helper.get_inventory_hash()
    last_inventory_change_time = time.time()
    last_hash_check_time = time.time()
    required_stuck_ticks = random.randint(5,10) #Number of ticks before changing direction to next in config

    # Start harvesting the row
    move.start_attack()
    move.start_sprint()
    move.start_movement(direction)

    # Data to ensure that we haven't stopped moving for a macro check or bug
    player_data = minescript.player()
    last_x, last_z = player_data.position[0], player_data.position[2]
    last_pos_check_time = time.time()
    stuck_counter = 0

    # Ensure that we have not paused the macro
    while True:
        pause_duration = check_pause()

        # Stops or starts the macro based on the input schedule in the params
        if scheduler:
            scheduler_pause = scheduler.check_schedule(pause_event, run_event)
            if scheduler_pause > 0:
                pause_duration += scheduler_pause

        if pause_duration > 0:
            last_inventory_change_time += pause_duration # Check to make sure that even if we are moving our inventory is updating
            move.start_attack()
            human.do_normal_delay()
            if (direction == "forward"):
                move.start_sprint()
            move.start_movement(direction)
            human.do_hold_delay()
            stuck_counter = 0
            continue

        if restart_event.is_set():
            move.stop_all_movement()
            return

        time.sleep(max(0.02, random.gauss(0.05,0.01)))

        if random.random() < 0.005: # Randomly release and then depress attack to look more natural
            move.stop_attack()
            human.do_click_delay() 
            move.start_attack()

        # Check if there are pests in the area and remove them
        if pest.scan_for_pests():
            pest.attack_nearby_pests(config)
            # Return to farming
            human.do_normal_delay()
            move.start_attack()
            human.do_normal_delay()
            move.start_movement(direction)
            human.do_normal_delay()

            stuck_counter = 0
            last_inventory_change_time = time.time()
            continue

        pause_duration = check_pause()
        if pause_duration > 0:
            last_inventory_change_time += pause_duration
            move.start_movement(direction)
            human.do_normal_delay()
            move.start_attack()
            human.do_hold_delay()
            stuck_counter = 0
            continue

        # Determine if we not updated our inventory and are getting macro checked
        current_time = time.time()
        if current_time - last_hash_check_time >= CHECK_INTERVAL_SECONDS: # Number of seconds between checks
            current_inventory = helper.get_inventory_hash()
            last_hash_check_time = current_time 
            if current_inventory != last_inventory:
                last_inventory = current_inventory
                last_inventory_change_time = current_time

        time_since_change = time.time() - last_inventory_change_time
        base_stall = 4 if config.get("name") == "Mushroom Farm" else 2 # Mushroom Farm has a longer travel time between rows so gave it more time
        inventory_stall_sec = random.uniform(base_stall, base_stall + 1.8)

        if time_since_change > inventory_stall_sec:
            if stuck_counter > 0: # We're good
                pass
            else: # Spazz out, this is the macro check so these erratic movements are intended to buy time to tab into the game
                lib.play_alert_sound() # Alert there's a problem
                human.human_delay(MIN_DELAY*2, MAX_DELAY*2)
                lib.play_alert_sound()
                minescript.echo(f"Inventory hasn't updated for {inventory_stall_sec} seconds")
                # minescript.chat(random.choice(FARM_AUTO_PAUSE_MESSAGES))
                
                # Make the player do some random movement in 'confusion'
                move.stop_all_movement()
                human.do_normal_delay()
                def pick_direction(): return random.choice(["left", "right", "forward", "backward"]) # Pick a random direction to move in
                move.start_movement(pick_direction())
                human.do_normal_delay()
                move.start_movement(pick_direction())

                # Player looks around
                yaw, pitch = minescript.player_orientation()
                target_orientation = (yaw + random.uniform(-10,10), pitch + random.uniform(-10,10))
                orient.smooth_look_at_cursor(target_orientation, 0.5, 0.9)
                move.stop_all_movement()

                # Player jumps and moves in a random direction
                human.do_normal_delay()
                minescript.player_press_jump(True)
                human.do_normal_delay()
                move.start_movement(pick_direction())
                human.do_normal_delay()
                
                # Player looks around
                yaw, pitch = minescript.player_orientation()
                target_orientation = (yaw + random.uniform(-10,10), pitch + random.uniform(-10,10))
                orient.smooth_look_at_cursor(target_orientation, 0.5, 0.9)
                yaw, pitch = minescript.player_orientation()
                target_orientation = (yaw + random.uniform(-10,10), pitch + random.uniform(-10,10))
                orient.smooth_look_at_cursor(target_orientation, 0.5, 0.9)
                
                # Player stops moving
                minescript.player_press_jump(False)
                move.stop_all_movement()
                
                # Additional alert to get you to tab into the game
                lib.play_alert_sound()
                move.stop_all_movement() # Stop movement so you can take control
                pause_event.set()
                run_event.clear()
                run_event.wait()
                pause_event.clear()

                last_inventory_change_time = time.time()
                last_inventory = helper.get_inventory_hash()
                last_hash_check_time = time.time()

                # Start harvesting the row again when you unpause the macro
                move.start_attack()
                human.do_normal_delay()
                if (direction == "forward"):
                    move.start_sprint()
                move.start_movement(direction)
                human.do_normal_delay()
                stuck_counter = 0
                continue
#Only necessary if you don't have sundial
        # Determine if we have hit a wall and need to change direction
        current_time = time.time()
        if current_time - last_pos_check_time >= CHECK_INTERVAL_SECONDS: # Number of seconds between checks
            player_data = minescript.player()
            current_x, current_z = player_data.position[0], player_data.position[2]
            distance_moved = math.hypot(current_x - last_x, current_z - last_z) # Calculate the distance moved

            if distance_moved < DISTANCE_MOVED_THRESHOLD: # If the distance moved is less than 0.03, we have hit a wall
                stuck_counter += 1
                if stuck_counter >= REQUIRED_STUCK_TICKS: # If we have hit a wall for the required number of ticks, we need to change direction
                    #minescript.echo(f"Hit wall on row {row_num}")
                    human.do_normal_delay()
                    break
            else:
                stuck_counter = 0

            last_x, last_z = current_x, current_z
            last_pos_check_time = current_time

    move.stop_directional_movement()
    human.do_normal_delay()
    minescript.echo(f"Row {row_num} complete")

def drop_to_next_row(row_num):
    minescript.echo(f"Dropping to row {row_num + 1}")
    check_pause()
    human.do_normal_delay()

def run_farm(config, scheduler=None, set_home_and_squeeker=True):
    minescript.echo(f"=== {config['name']} Started ===")
    event_queue = minescript.EventQueue()
    event_queue.register_key_listener()

    if HUB_DETECTION_ENABLED:
        event_queue.register_chat_listener()

    run_count = 0

    class FarmEventService(BaseService):
        def __init__(self):
            super().__init__("farm_event_listener", tick_interval=0.05)

        def run_step(self):
            try:
                event = event_queue.get(block=False)
                if event.type == "key":
                    if event.key == PAUSE_KEY and event.action == 1:
                        if pause_event.is_set():
                            pause_event.clear()
                            run_event.set()
                        else:
                            pause_event.set()
                            run_event.clear()
                elif event.type == "chat":
                    if HUB_CHAT_MESSAGE in event.message:
                        restart_event.set()
                        lib.play_alert_sound()
                        minescript.echo("=== SERVER RESTART DETECTED! ===")
            except:
                pass
    register_service(FarmEventService()).start()

    while True:
        if restart_event.is_set():
            move.stop_all_movement()
            return

        farm_setup(config, run_count, set_home_and_squeeker)
        run_count += 1
        check_pause()

        for run in range(config["rows"]):
            if restart_event.is_set():
                move.stop_all_movement()
                return

            for i, (direction, row_num) in enumerate(config["pattern"]):
                if restart_event.is_set():
                    move.stop_all_movement()
                    return
                check_pause()
                if scheduler:
                    scheduler.check_schedule(pause_event, run_event)
                harvest_row(direction, row_num, config, scheduler)
                if config.get("has_drops", False) and i < len(config["pattern"]) - 1:
                    drop_to_next_row(row_num)

        check_pause()

def farm_setup(config, run_count, set_home_and_squeeker):
    human.human_delay(0.5, 0.1)
    minescript.player_inventory_select_slot(FARM_SNAP_LOOK_SLOT)

    # Set the default settings for the farm based on the configs
    if (run_count == 0 and set_home_and_squeeker):
        human.human_delay(1, 1.2)
        minescript.execute(f"/sethome") 
        #human.human_delay(0.5, 0.15)
        #minescript.execute(f"/setmaxspeed {config['speed']}") #Only necessary if you don't have sundial
        human.human_delay(1, 1.5)
        minescript.execute(f"/setpitch {config['pitch']}")
        human.human_delay(1, 1.5)
        minescript.execute(f"/setyaw {config['yaw']}")

    # Activate the squeeker
    human.do_slot_switch_delay()
    move.start_attack()
    human.do_hold_delay()
    move.stop_attack()

def main():
    usage = (
        "Usage: farming <farmPreset> [set home and squeeker boolean] [duration_hrs] [num_breaks] "
        "[min_break_mins] [max_break_mins]"
    )

    # At minimum, we need to pass one param, the farm preset name
    if len(sys.argv) < 2:
        minescript.echo(usage)
        return

    # This is the farm preset param
    farm_type = sys.argv[1].lower()
    if farm_type not in FARM_PRESETS:
        minescript.echo(f"Error: Unknown farm preset '{farm_type}'.")
        minescript.echo(f"Available presets: {', '.join(sorted(FARM_PRESETS.keys()))}")
        return
    config = FARM_PRESETS[farm_type]

    # Default values for the optional params
    set_home_and_squeeker = True # Do the farm setup
    duration_hrs = 1 # Session duration in hours
    num_breaks = 0 # Number of breaks to take during the session
    min_break_mins = 0 # Minimum break duration in minutes
    max_break_mins = 0 # Maximum break duration in minutes

    # Validate that the number of args passed is not greater than the number of optional params
    optional_args = sys.argv[2:]
    if len(optional_args) > 5:
        minescript.echo("Error: Too many arguments.")
        minescript.echo(usage)
        return

    parse_spec = [
        ("set_home_and_squeeker", lambda v: str(v).lower() == 'true'),
        ("duration_hrs", float),
        ("num_breaks", int),
        ("min_break_mins", float),
        ("max_break_mins", float),
    ]
    parsed_values = [set_home_and_squeeker, duration_hrs, num_breaks, min_break_mins, max_break_mins]

    for i, raw_value in enumerate(optional_args):
        arg_name, parser = parse_spec[i]
        try:
            parsed_values[i] = parser(raw_value)
        except ValueError:
            minescript.echo(
                f"Error: Invalid value for {arg_name}: '{raw_value}'."
            )
            minescript.echo(usage)
            return

    # Parse the optional args
    set_home_and_squeeker, duration_hrs, num_breaks, min_break_mins, max_break_mins = parsed_values

    # Create the scheduler
    scheduler = SessionScheduler(
        duration_hrs=duration_hrs,
        num_breaks=num_breaks,
        min_break_mins=min_break_mins,
        max_break_mins=max_break_mins
    )

    # Run the farm
    run_farm(config, scheduler, set_home_and_squeeker)

if __name__ == "__main__":
    main()
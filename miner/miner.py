import minescript
import math
import time
import random
import lib.minescript_plus as minescript_plus
import lib.orientation as orient
import lib.worldrender as worldrender
import lib.humanization as human
import lib.movement as move
from lib.session import scheduler
import sys
from core.state import check_pause, run_event, pause_event

from core.constants import (
    MINING_ABILITY_ON,
    MINING_AUTO_RESCAN,
    MINING_BLOCK_COOLDOWN,
    MINING_BREAK_BLOCKS,
    MINING_BREAK_DELAY,
    MINING_CHECK_INTERVAL,
    MINING_IGNORE_BLOCK_STATE,
    MINING_MAX_ABILITY_COOLDOWN,
    MINING_MAX_WAIT,
    MINING_MIN_ABILITY_COOLDOWN,
    MINING_RESCAN_KEY,
    MINING_ROTATION_DURATION_MAX,
    MINING_ROTATION_DURATION_MIN,
    MINING_SEARCH_DISTANCE,
    MINING_TARGET_BLOCKS,
    MINING_TRANSPARENT_BLOCKS,
    MINING_USE_CLUSTER_MODE,
    MINING_USE_SMART_TARGETING,
    MINING_WAIT_TIME,
    PLAYER_EYE_HEIGHT,

    TIME_MIN_DELAY,
    TIME_MAX_DELAY,
    TIME_MIN_CLICK_DELAY,
    TIME_MAX_CLICK_DELAY,
)

# Mining configs (short names for this module; values from core.constants)
ABILITY_ON = MINING_ABILITY_ON
AUTO_RESCAN = MINING_AUTO_RESCAN
BLOCK_COOLDOWN = MINING_BLOCK_COOLDOWN
BREAK_BLOCKS = MINING_BREAK_BLOCKS
BREAK_DELAY = MINING_BREAK_DELAY
CHECK_INTERVAL = MINING_CHECK_INTERVAL
IGNORE_BLOCK_STATE = MINING_IGNORE_BLOCK_STATE
MAX_ABILITY_COOLDOWN = MINING_MAX_ABILITY_COOLDOWN
MAX_WAIT = MINING_MAX_WAIT
MIN_ABILITY_COOLDOWN = MINING_MIN_ABILITY_COOLDOWN
RESCAN_KEY = MINING_RESCAN_KEY
ROTATION_DURATION_MAX = MINING_ROTATION_DURATION_MAX
ROTATION_DURATION_MIN = MINING_ROTATION_DURATION_MIN
SEARCH_DISTANCE = MINING_SEARCH_DISTANCE
TARGET_BLOCKS = MINING_TARGET_BLOCKS
TRANSPARENT_BLOCKS = MINING_TRANSPARENT_BLOCKS
USE_CLUSTER_MODE = MINING_USE_CLUSTER_MODE
USE_SMART_TARGETING = MINING_USE_SMART_TARGETING
WAIT_TIME = MINING_WAIT_TIME
EYE_HEIGHT = PLAYER_EYE_HEIGHT
MIN_DELAY = TIME_MIN_DELAY
MAX_DELAY = TIME_MAX_DELAY
MIN_CLICK_DELAY = TIME_MIN_CLICK_DELAY
MAX_CLICK_DELAY = TIME_MAX_CLICK_DELAY

unreachable_blocks_blacklist = set()
last_mined_block = None


def _safe_remove_worldrender_box(box_id):
    if box_id is None:
        return
    try:
        worldrender.WorldRender.remove_box(id=box_id)
    except Exception:
        pass


def find_all_blocks(max_distance=None, block_types=None, ignore_state=None):
    """Find all blocks of specified types within max_distance (player hit range)."""
    if max_distance is None:
        max_distance = SEARCH_DISTANCE
    if block_types is None:
        block_types = TARGET_BLOCKS  # List of target blocks
    if ignore_state is None:
        ignore_state = IGNORE_BLOCK_STATE
        
    player_pos = minescript.player_position()
    px, py, pz = player_pos
    
    # 1. OPTIMIZATION: Pre-process targets into a set for O(1) lightning-fast lookups
    if ignore_state:
        target_bases = {bt.split('[')[0] for bt in block_types}
    else:
        target_bases = set(block_types)

    search_mode = "with state ignored" if ignore_state else "exact match"
    #minescript.echo(f"Searching for {len(block_types)} block types within {max_distance} blocks ({search_mode})...")
    
    # Generate list of positions to check
    positions_to_check = []
    search_range = max_distance
    
    for x in range(int(px - search_range), int(px + search_range + 1)):
        for y in range(int(py - search_range), int(py + search_range + 1)):
            for z in range(int(pz - search_range), int(pz + search_range + 1)):
                distance = math.sqrt((x - px)**2 + (y - py)**2 + (z - pz)**2)
                if distance <= max_distance:
                    positions_to_check.append([x, y, z])
    all_found_blocks = []
    # 2. Use getblocklist for batch checking (much faster than fetching individually)
    if positions_to_check:
        world_block_types = minescript.getblocklist(positions_to_check)
        
        for x in range(int(px-search_range), int(px+search_range+1)):
            for y in range(int(py-search_range), int(py+search_range+1)):
                for z in range(int(pz-search_range), int(pz+search_range+1)):
                    distance = math.sqrt((x - px)**2 + (y - py)**2 + (z - pz)**2)
                    if distance <= max_distance:
                        positions_to_check.append([x, y, z])

    if positions_to_check:
        world_block_types = minescript.getblocklist(positions_to_check)
        
        for i, found_block_type in enumerate(world_block_types):
            x,y,z = positions_to_check[i]
            if (x, y, z) in unreachable_blocks_blacklist:
                continue
            if ignore_state:
                found_base = found_block_type.split('[')[0]
                is_match = (found_base in target_bases)
            else:
                is_match = (found_block_type in target_bases)

            if is_match:
                distance = math.sqrt((x - px)**2 + (y - py)**2 + (z - pz)**2)
                all_found_blocks.append({
                    'position': (x, y, z),
                    'distance': distance,
                    'full_type': found_block_type,
                    'cluster_score': 0 # Defaults to 0, customize if you add cluster math later
                })

    #minescript.echo(f"Search complete. Found {len(all_found_blocks)} valid block(s)")

    if USE_CLUSTER_MODE and all_found_blocks:
        current_yaw, current_pitch = minescript.player_orientation()
        best_angular_dist = float('inf')
        crosshair_anchor_pos = all_found_blocks[0]['position']

        for b in all_found_blocks:
            bx, by, bz = b['position']
            req_yaw, req_pitch = calculate_look_angles(player_pos, (bx + 0.5, by + 0.5, bz + 0.5))
            angular_dist = calculate_angular_distance(current_yaw, current_pitch, req_yaw, req_pitch)
            if angular_dist < best_angular_dist:
                best_angular_dist = angular_dist
                crosshair_anchor_pos = b['position']

        cx, cy, cz = crosshair_anchor_pos
        for b in all_found_blocks:
            bx, by, bz = b['position']
            dist_to_anchor = math.sqrt((bx - cx)**2 + (by - cy)**2 + (bz - cz)**2)
            score = 100.0 / (dist_to_anchor + 1.0)
            if dist_to_anchor <= 1.5:
                score += 500.0
            
            if dist_to_anchor == 0:
                score -= 100.0

            b['cluster_score'] = score

    # 4. Sort the aggregated list
    if USE_CLUSTER_MODE:
        # Sort by cluster weight (requires cluster logic to be added to cluster_score above)
        all_found_blocks.sort(key=lambda b: b.get('cluster_score', 0), reverse=True)
    else:
        # Sort by distance so the bot mines the absolute closest ore first
        all_found_blocks.sort(key=lambda b: b['distance'])
        
    return all_found_blocks


def calculate_look_angles(player_pos, target_pos):
    """
    Calculate yaw and pitch to look at target position from player position.
    
    Args:
        player_pos: (x, y, z) tuple of player position
        target_pos: (x, y, z) tuple of target position
    
    Returns:
        (yaw, pitch) tuple in degrees
    """
    px, py, pz = player_pos
    tx, ty, tz = target_pos
    
    # Calculate differences (adjust for player eye height at 1.62 blocks)
    dx = tx - px
    dy = ty - (py + EYE_HEIGHT)
    dz = tz - pz
    
    # Calculate distance in horizontal plane
    horizontal_distance = math.sqrt(dx**2 + dz**2)
    
    # Calculate pitch (vertical angle, negative because of Minecraft's coordinate system)
    pitch = -math.degrees(math.atan2(dy, horizontal_distance))
    
    # Calculate yaw (horizontal angle)
    yaw = math.degrees(math.atan2(-dx, dz))
    
    return yaw, pitch


def calculate_angular_distance(yaw1, pitch1, yaw2, pitch2):
    """
    Calculate angular distance between two orientations.
    Returns a value representing how far apart two look directions are.
    """
    # Convert to radians
    yaw1_rad = math.radians(yaw1)
    pitch1_rad = math.radians(pitch1)
    yaw2_rad = math.radians(yaw2)
    pitch2_rad = math.radians(pitch2)
    
    # Convert to 3D unit vectors
    x1 = math.cos(pitch1_rad) * math.sin(yaw1_rad)
    y1 = math.sin(pitch1_rad)
    z1 = math.cos(pitch1_rad) * math.cos(yaw1_rad)
    
    x2 = math.cos(pitch2_rad) * math.sin(yaw2_rad)
    y2 = math.sin(pitch2_rad)
    z2 = math.cos(pitch2_rad) * math.cos(yaw2_rad)
    
    # Dot product gives cosine of angle between vectors
    dot_product = x1*x2 + y1*y2 + z1*z2
    # Clamp to avoid floating point errors
    dot_product = max(-1.0, min(1.0, dot_product))
    
    # Return angle in degrees
    return math.degrees(math.acos(dot_product))

def sort_blocks_by_viewing_order(blocks, player_pos):
    """
    Sort blocks by natural viewing order (cluster-aware).
    Looks at nearest block first, then blocks close to current view direction.
    """
    if not blocks:
        return []

    sorted_blocks = []
    remaining = blocks.copy()

    remaining.sort(key=lambda b: b['distance'])

    current_block = remaining.pop(0)
    sorted_blocks.append(current_block)

    current_yaw, current_pitch = minescript.player_orientation()

    while remaining:
        current_pos = current_block['position']

        # USE CENTER ONLY FOR SORTING (Massive performance save)
        target_point = (
            current_pos[0] + 0.5,
            current_pos[1] + 0.5,
            current_pos[2] + 0.5,
        )
        current_yaw, current_pitch = calculate_look_angles(player_pos, target_point)

        best_block = None
        best_score = float('inf')

        for block in remaining:
            block_pos = block['position']
            block_target = (
                block_pos[0] + 0.5,
                block_pos[1] + 0.5,
                block_pos[2] + 0.5,
            )

            physical_dist = math.sqrt(
                (block_target[0] - target_point[0])**2 + 
                (block_target[1] - target_point[1])**2 + 
                (block_target[2] - target_point[2])**2
            )

            target_yaw, target_pitch = calculate_look_angles(player_pos, target_point)
            angular_dist = calculate_angular_distance(
                current_yaw, current_pitch, target_yaw, target_pitch
            )  

            score = physical_dist + (angular_dist / 45.0)          

            if score < best_score:
                best_score = score
                best_block = block

        remaining.remove(best_block)
        sorted_blocks.append(best_block)
        current_block = best_block

    return sorted_blocks


def break_block_at(block_pos):
    """Hold attack until the block at integer world coords changes or timeout."""
    if not BREAK_BLOCKS:
        return
    if (minescript.player_get_targeted_block().position is not block_pos):
        return
    if BREAK_DELAY > 0:
        human.human_delay(BREAK_DELAY, BREAK_DELAY+0.05)
    if WAIT_TIME > 0:
        human.human_delay(WAIT_TIME, WAIT_TIME+0.05)
    block_x, block_y, block_z = block_pos
    original_block = minescript.getblock(block_x, block_y, block_z)
    move.start_attack()
    max_wait = MAX_WAIT
    wait_time = WAIT_TIME
    check_interval = CHECK_INTERVAL
    while wait_time < max_wait:
        time.sleep(check_interval)
        wait_time += check_interval
        if minescript.getblock(block_x, block_y, block_z) != original_block:
            break
    # move.stop_attack()
    last_mined_block = block_pos


def find_best_exposed_target(player_pos, block_pos):
    """
    Finds the most direct, physically exposed face of a block pointing towards the player.
    """
    px, py, pz = player_pos
    bx, by, bz = block_pos
    
    eye_y = py + EYE_HEIGHT
    
    # Calculate delta from eye to block center
    dx = (bx + 0.5) - px
    dy = (by + 0.5) - eye_y
    dz = (bz + 0.5) - pz
    
    # Structure: (Delta magnitude, Adjacent block coordinate, Target point on face)
    # We use 0.05 / 0.95 to place the target point just *inside* the block's face 
    # so the raycast successfully hits the ore and not the air block next to it.
    faces_to_check = []
    
    # X faces (West/East)
    if dx > 0: # Player is -X, looking +X. Target the West face
        faces_to_check.append((abs(dx), (bx - 1, by, bz), (bx + 0.05, by + 0.5, bz + 0.5)))
    else:      # Player is +X, looking -X. Target the East face
        faces_to_check.append((abs(dx), (bx + 1, by, bz), (bx + 0.95, by + 0.5, bz + 0.5)))
        
    # Y faces (Bottom/Top)
    if dy > 0: # Player is below, looking up. Target Bottom face
        faces_to_check.append((abs(dy), (bx, by - 1, bz), (bx + 0.5, by + 0.05, bz + 0.5)))
    else:      # Player is above, looking down. Target Top face
        faces_to_check.append((abs(dy), (bx, by + 1, bz), (bx + 0.5, by + 0.95, bz + 0.5)))
        
    # Z faces (North/South)
    if dz > 0: # Player is -Z, looking +Z. Target North face
        faces_to_check.append((abs(dz), (bx, by, bz - 1), (bx + 0.5, by + 0.5, bz + 0.05)))
    else:      # Player is +Z, looking -Z. Target South face
        faces_to_check.append((abs(dz), (bx, by, bz + 1), (bx + 0.5, by + 0.5, bz + 0.95)))
        
    # Sort faces by magnitude so we check the one most directly facing the player first
    faces_to_check.sort(key=lambda f: f[0], reverse=True)
    
    # Check if the faces are actually exposed
    for _, adj_pos, target_point in faces_to_check:
        adj_block = minescript.getblock(*adj_pos)
        adj_base = adj_block.split('[')[0] # Strip states like [waterlogged=true]
        
        if adj_base in TRANSPARENT_BLOCKS:
            return target_point # We found a direct, exposed face!
            
    # Fallback: If no direct faces are exposed (e.g., looking at a corner block diagonally), 
    # default to the center of the block.
    return (bx + 0.5, by + 0.5, bz + 0.5)

def sort_blocks_by_crosshair_proximity(blocks, player_pos):
    """
    Sorts blocks so that those closest to the player's current crosshair
    (requiring the least camera rotation) are targeted first.
    """
    if not blocks:
        return []
        
    current_yaw, current_pitch = minescript.player_orientation()
    
    def crosshair_distance_key(block):
        block_pos = block['position']
        # Use block center for fast calculation
        target_point = (block_pos[0] + 0.5, block_pos[1] + 0.5, block_pos[2] + 0.5)
        
        # Calculate the angle required to look at this specific block
        req_yaw, req_pitch = calculate_look_angles(player_pos, target_point)
        
        # Calculate how many degrees of rotation it takes to get there
        angular_dist = calculate_angular_distance(current_yaw, current_pitch, req_yaw, req_pitch)
        
        # Return tuple: (Primary sort = Angle, Secondary sort = Physical Distance)
        return (angular_dist, block['distance'])
        
    # Return a new list sorted by the key
    return sorted(blocks, key=crosshair_distance_key)

def main(scheduler=None):
    """Main function to find and look at all target blocks sequentially."""

    try:
        duration_hrs = float(sys.argv[1])
        num_breaks = int(sys.argv[2])
        min_break_mins = float(sys.argv[3])
        max_break_mins = float(sys.argv[4])
    except:
        minescript.echo("Error: Please provide valid numbers for the schedulerule variables")
        return

    scheduler = scheduler.SessionScheduler(
        duration_hrs=duration_hrs,
        num_breaks=num_breaks,
        min_break_mins=min_break_mins,
        max_break_mins=max_break_mins
    )

    minescript.echo("=== Smooth Auto Mining Script ===")
    minescript.echo(f"Target: {TARGET_BLOCKS}")
    minescript.echo(
        f"Config: distance={SEARCH_DISTANCE}m, "
        f"rotation={ROTATION_DURATION_MIN}-{ROTATION_DURATION_MAX}s, "
        f"cooldown={BLOCK_COOLDOWN}s"
    )
    minescript.echo(
        f"Features: cluster_mode={USE_CLUSTER_MODE}, "
        f"break_blocks={BREAK_BLOCKS}, "
        f"smart_targeting={USE_SMART_TARGETING}, "
        f"auto_rescan={AUTO_RESCAN}, "
        f"ignore_state={IGNORE_BLOCK_STATE}"
    )

    key_names = {89: 'Y', 82: 'R', 71: 'G', 84: 'T'}
    rescan_key_name = key_names.get(RESCAN_KEY, f"key {RESCAN_KEY}")
    minescript.echo(f"\nPress '{rescan_key_name}' to start mining | Open any GUI to exit")
    
    total_blocks_processed = 0
    session_blocks = 0  # Blocks in current session
    is_active = False  # Whether we're actively processing blocks
    
    # Setup event queue for key and screen events
    event_queue = minescript.EventQueue()
    event_queue.register_key_listener()

    ability_cooldown = human.human_delay(MIN_ABILITY_COOLDOWN, MAX_ABILITY_COOLDOWN)
    last_ability_time = time.time() - ability_cooldown
    
    try:
        while run_event.is_set():
            # Check for exit condition (GUI opened)
            current_screen = minescript.screen_name()
            if current_screen is not None:
                minescript.echo(f"GUI opened ({current_screen}) - Exiting script...")
                break

            # Check for scan key press to start/restart
            try:
                while True:
                    event = event_queue.get(block=False)
                    if event.type == "key":
                        # Key down event (action == 1) and matches rescan key
                        if event.action == 1 and event.key == RESCAN_KEY:
                            if is_active:
                                minescript.echo(f"\n'{rescan_key_name}' pressed - Pausing mining!")
                                minescript.echo(f"Session stats: {session_blocks} blocks mined")
                                is_active = False
                                session_blocks = 0
                            else:
                                minescript.echo(f"\n'{rescan_key_name}' pressed - Starting mining!")
                                is_active = True
            except Exception:
                pass  # No events in queue

            # Only process if active
            if not is_active:
                time.sleep(0.1)
                continue

            check_pause()

            if scheduler:
                scheduler.check_schedule(pause_event, run_event)

            if ABILITY_ON and (time.time() - last_ability_time) > ability_cooldown:
                move.stop_attack()
                human.do_click_delay()
                move.start_use()
                human.do_click_delay()
                move.stop_use()
                human.do_normal_delay()
                move.start_attack()

                last_ability_time = time.time()
                human.human_delay(0.2, 0.4)

            player_pos = minescript.player_position()
            
            # Scan for all target blocks (fresh scan every time)
            blocks = find_all_blocks(
                max_distance=SEARCH_DISTANCE,
                block_types=TARGET_BLOCKS,
                ignore_state=IGNORE_BLOCK_STATE,
            )

            if not blocks:
                if AUTO_RESCAN:
                    # In auto-rescan mode, keep checking silently
                    time.sleep(0.5)  # Wait a bit before rescanning
                    continue
                else:
                    minescript.echo(f"✓ No blocks found in range!")
                    minescript.echo(f"Total blocks mined this session: {session_blocks}")
                    minescript.echo(f"Press '{rescan_key_name}' to stop/start or open GUI to exit")
                    is_active = False
                    session_blocks = 0
                    time.sleep(0.1)
                    continue
            
            # Sort blocks based on configuration
            if USE_CLUSTER_MODE:
                sorted_blocks = blocks
            else:
                sorted_blocks = sort_blocks_by_crosshair_proximity(blocks, player_pos)
            
            # Process only the first block in the sorted list
            block_info = sorted_blocks[0]
            
            # Check for exit condition before processing
            current_screen = minescript.screen_name()
            if current_screen is not None:
                minescript.echo(f"GUI opened ({current_screen}) - Exiting script...")
                break
            
            x, y, z = block_info['position']
            distance = block_info['distance']
            full_type = block_info.get("full_type", TARGET_BLOCKS)

            if USE_SMART_TARGETING:
                target_point = find_best_exposed_target(player_pos, (x, y, z))
                targeting_mode = "visible face"
            else:
                target_point = (x + 0.5, y + 0.5, z + 0.5)
                targeting_mode = "center"
            
            total_available = len(blocks)
            #minescript.echo(f"[{total_available} available] Mining {full_type} at ({x}, {y}, {z}) [{targeting_mode}] - {distance:.1f}m")

            # WorldRender assigns ids internally; remove in finally to avoid gizmo leaks.
            highlight_id = worldrender.WorldRender.add_box(
                x, y, z, x + 1, y + 1, z + 1, 0, 255, 255, 150
            )
            try:
                orient.smooth_look_at_block(
                    target_point,
                    ROTATION_DURATION_MIN,
                    ROTATION_DURATION_MAX,
                )
                expected_base = full_type.split('[')[0]  # Strip state data safely
                block_validated = False
                max_fuzz_attempts = 2
                
                for attempt in range(max_fuzz_attempts + 1):
                    # Pause briefly to allow the server raycast to update
                    human.human_delay(0.01, 0.15)
                    
                    targeted_block = minescript.player_get_targeted_block()
                    
                    if targeted_block:
                        targeted_base = targeted_block.type.split('[')[0]
                        if targeted_base == expected_base:
                            block_validated = True
                            break  # Successfully confirmed!
                            
                    # If we haven't validated it and have attempts left, fuzz the target
                    if attempt < max_fuzz_attempts:
                        minescript.echo(f"Missed target. Fuzzing aim (Attempt {attempt + 1}/{max_fuzz_attempts})...")
                        
                        # Apply a micro-deviation (+/- 0.3 blocks) to the target 3D point
                        fx = target_point[0] + random.uniform(-0.3, 0.3)
                        fy = target_point[1] + random.uniform(-0.3, 0.3)
                        fz = target_point[2] + random.uniform(-0.3, 0.3)
                        
                        # Execute a very fast, localized humanized correction
                        orient.smooth_look_at_block((fx, fy, fz), 0.3, 0.4)
                
                # 3. Final Check before breaking
                if not block_validated:
                    minescript.echo(f"Skipping {expected_base} at ({x}, {y}, {z}) - Could not validate line of sight.")
                    unreachable_blocks_blacklist.add((x, y, z))
                    continue  # Skip breaking and move to the next block
                break_block_at((x, y, z))
            finally:
                _safe_remove_worldrender_box(highlight_id)

            # Increment counters
            total_blocks_processed += 1
            session_blocks += 1

            if BLOCK_COOLDOWN > 0:
                human.human_delay(BLOCK_COOLDOWN, BLOCK_COOLDOWN + 0.05)
            
            # With auto_rescan enabled, loop continues and rescans immediately
            # This allows continuous mining as the player moves or new blocks appear
    
    finally:
        move.stop_attack()
        minescript.echo(f"✓ Script ended. Total blocks mined: {total_blocks_processed}")


# Run the script
if __name__ == "__main__":
    scheduler = None

    if len(sys.argv) >= 5:
        try: 
            duration_hrs = float(sys.argv[1])
            num_breaks = int(sys.argv[2])
            min_break_mins = float(sys.argv[3])
            max_break_mins = float(sys.argv[4])

            scheduler = scheduler.SessionScheduler(
                duration_hrs=duration_hrs,
                num_breaks=num_breaks,
                min_break_mins=min_break_mins,
                max_break_mins=max_break_mins
            )
        except ValueError:
            minescript.echo("Error: Please provide valid numbers for the schedulerule variables")
            sys.exit(1)

    main(scheduler)
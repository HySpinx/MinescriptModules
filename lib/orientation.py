import minescript
import math
import time
import random
import lib.humanization as human
from core.constants import PLAYER_EYE_HEIGHT

# ==========================================
# 1. GLOBAL STATE VARIABLES
# ==========================================

EYE_HEIGHT = PLAYER_EYE_HEIGHT

# ==========================================
# 2. MATH FUNCTIONS
# ==========================================

def get_aim_deltas(player_pos, target_pos, current_yaw, current_pitch):
    """Calculates the target yaw/pitch and shortest angular differences."""
    px, py, pz = player_pos
    tx, ty, tz = target_pos

    target_pitch = -math.degrees(math.atan2(ty - (py + EYE_HEIGHT), math.hypot(tx - px, tz - pz)))
    target_yaw = math.degrees(math.atan2(-(tx - px), tz - pz))

    yaw_diff = ((target_yaw - current_yaw + 180) % 360) - 180
    pitch_diff = ((target_pitch - current_pitch + 180) % 360) - 180

    return target_yaw, target_pitch, yaw_diff, pitch_diff


def eased_bezier(t, p0, p1, p2, p3):
    """Applies sine easing to t and evaluates a cubic bezier point."""
    t = -(math.cos(math.pi * t) - 1) / 2
    u = 1 - t
    return (u**3 * p0) + (3 * u**2 * t * p1) + (3 * u * t**2 * p2) + (t**3 * p3)

# ==========================================
# 3. ORIENTATION FUNCTIONS
# ==========================================

def track_entity_smoothly(get_target_pos_func, duration, smoothing=0.15):
    """Continuously tracks a moving target with smoothing and humanized noise."""
    fps = 120
    loop_delay = 1.0 / fps
    phases = [random.uniform(0, math.pi * 2) for _ in range(4)]

    start_time = time.time()
    end_time = start_time + duration
    frame = 0

    # 1. Switch to a time-based while loop
    while time.time() < end_time:
        loop_start = time.time()

        target_pos = get_target_pos_func()
        if not target_pos:
            break

        yaw, pitch = minescript.player_orientation()
        _, _, yaw_diff, pitch_diff = get_aim_deltas(minescript.player_position(), target_pos, yaw, pitch)

        yaw += yaw_diff * smoothing
        pitch += pitch_diff * smoothing

        current_time_noise = frame * loop_delay
        yaw += human.generate_smooth_noise(current_time_noise, 2.5, 0.8, phases[0], phases[1])
        pitch += human.generate_smooth_noise(current_time_noise, 3.0, 0.5, phases[2], phases[3])

        minescript.player_set_orientation(float(yaw), float(pitch))

        # 2. Dynamic sleep: Calculate how long the API calls took and subtract it
        work_time = time.time() - loop_start
        sleep_time = max(0, loop_delay - work_time) 
        time.sleep(sleep_time)
        
        frame += 1

def smooth_look_at_block(target_pos, duration_min, duration_max):
    """Snaps the camera to a static position using a humanized cubic bezier curve."""
    yaw, pitch = minescript.player_orientation()
    target_yaw, target_pitch, yaw_diff, pitch_diff = get_aim_deltas(
        minescript.player_position(), target_pos, yaw, pitch
    )

    p1_yaw = yaw + (yaw_diff * 0.3) + random.uniform(-6.0, 6.0)
    p1_pitch = pitch + (pitch_diff * 0.3) + random.uniform(-6.0, 6.0)

    p2_yaw = yaw + (yaw_diff * 0.7) + random.uniform(-6.0, 6.0)
    p2_pitch = pitch + (pitch_diff * 0.7) + random.uniform(-6.0, 6.0)

    scale = random.betavariate(2.0, 5.0)
    if duration_max < duration_min: # Catch edge case of user inputting bad values
        minescript.echo("Invalid values.")
        duration = 2 # Default to 2 seconds if user inputs bad values
    else:
        duration = duration_min + (scale * (duration_max - duration_min))
    steps = max(15, int(duration * 120))
    sleep_per_step = duration / steps

    for i in range(1, steps + 1):
        t_linear = i / steps

        step_yaw = eased_bezier(t_linear, yaw, p1_yaw, p2_yaw, yaw + yaw_diff)
        step_pitch = eased_bezier(t_linear, pitch, p1_pitch, p2_pitch, target_pitch)

        minescript.player_set_orientation(float(step_yaw), float(step_pitch))
        time.sleep(sleep_per_step)

    human.human_delay(0.05, 0.1)

def smooth_look_at_cursor(target_orientation, duration_min, duration_max):
    target_yaw, target_pitch = target_orientation
    current_yaw, current_pitch = minescript.player_orientation()
    
    p1_yaw = current_yaw + (target_yaw - current_yaw * 0.3) + random.uniform(-6.0, 6.0)
    p1_pitch = current_pitch + (target_pitch - current_pitch * 0.3) + random.uniform(-6.0, 6.0)

    p2_yaw = current_yaw + (target_yaw - current_yaw * 0.7) + random.uniform(-6.0, 6.0)
    p2_pitch = current_pitch + (target_pitch - current_pitch * 0.7) + random.uniform(-6.0, 6.0)

    scale = random.betavariate(2.0, 5.0)
    if duration_max < duration_min: # Catch edge case of user inputting bad values
        minescript.echo("Invalid human_delay values.")
        duration = 2 # Default to 2 seconds if user inputs bad values
    else:
        duration = duration_min + (scale * (duration_max - duration_min))
    steps = max(15, int(duration * 120))
    sleep_per_step = duration / steps

    for i in range(1, steps + 1):
        t_linear = i / steps

        step_yaw = eased_bezier(t_linear, current_yaw, p1_yaw, p2_yaw, target_yaw)
        step_pitch = eased_bezier(t_linear, current_pitch, p1_pitch, p2_pitch, target_pitch)

        minescript.player_set_orientation(float(step_yaw), float(step_pitch))
        time.sleep(sleep_per_step)

    human.human_delay(0.05, 0.1)

def is_in_front_of_player(player_orientation, player_position,target_position):
    yaw, pitch = player_orientation

    # Convert minecraft yaw and pitch to radians
    yaw_rad = math.radians(yaw)
    pitch_rad = math.radians(pitch)

    # Calculate the look vector
    look_x = -math.sin(yaw_rad) * math.cos(pitch_rad)
    look_y = -math.sin(pitch_rad)
    look_z = math.cos(yaw_rad) * math.cos(pitch_rad)

    # Get standard tuple coordinates of player and target
    player_x, player_y, player_z = player_position
    target_x, target_y, target_z = target_position

    # Calculate the distance between player and target
    dx = target_x - player_x
    dy = target_y - player_y
    dz = target_z - player_z

    # Calculate the dot product of the look vector and the distance vector
    dist = look_x * dx + look_y * dy + look_z * dz

    if dist < 0.1:
        return False

    # Normalize the target vector
    nx, ny, nz = dx / dist, dy / dist, dz / dist

    # Dot Product
    dot_product = look_x * nx + look_y * ny + look_z * nz

    # If the dot product is positive, the target is in front of the player
    return dot_product > 0.5
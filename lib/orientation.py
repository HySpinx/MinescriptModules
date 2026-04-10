import minescript
import math
import time
import random
import lib.humanization as human
from core.constants import PLAYER_EYE_HEIGHT
from dataclasses import dataclass

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
# 3. BASIC ORIENTATION FUNCTIONS
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

# ==========================================
# 4. COMPLEX ORIENTATION FUNCTIONS
# ==========================================

def raycast(start, end):
    """
    Returns a list of block coordinates along the line from start to end,
    sorted by distance from start. Returns None if the path is entirely air.
    """
    x1, y1, z1 = start
    x2, y2, z2 = end
    
    dx, dy, dz = x2 - x1, y2 - y1, z2 - z1
    distance = math.sqrt(dx**2 + dy**2 + dz**2)
    
    steps = int(distance * 2)
    
    path_blocks = []
    
    for i in range(1, steps + 1):
        t = i / steps
        cx = x1 + dx * t
        cy = y1 + dy * t
        cz = z1 + dz * t
        
        bx, by, bz = math.floor(cx), math.floor(cy), math.floor(cz)
        block_pos = (bx, by, bz)
        
        if not path_blocks or path_blocks[-1] != block_pos:
            path_blocks.append(block_pos)
            
    all_air = True
    for block_pos in path_blocks:
        block_type = minescript.get_block(block_pos[0], block_pos[1], block_pos[2])
        if "air" not in block_type:
            all_air = False
            break
            
    if all_air:
        return None
        
    return path_blocks

def distance(a, b):
    return math.sqrt(sum((a[i] - b[i])**2 for i in range(3)))

"""
CODE BELOW HERE IS SKIDDED!

All credit goes to @Jones in the minescript discord for this library.

I couldn't find an official repo for it, so I forked it and added look_at(x, y, z).

"""


@dataclass
class HumanLookConfig:
    min_speed: float = 35.0
    max_speed: float = 260.0
    min_angle: float = 5.0
    max_angle: float = 140.0
    min_duration: float = 0.045
    max_duration: float = 0.75
    max_curve_intensity: float = 0.14
    base_overshoot: float = 0.012
    max_overshoot: float = 0.040
    overshoot_bias: float = 0.55
    jitter_deg: float = 0.04
    jitter_smooth: float = 0.85
    jitter_scale_small_moves: float = 0.35
    target_hz: float = 120.0
    step_jitter: float = 0.22
    micro_settle_deg: float = 0.06
    micro_settle_steps: int = 3
    deadzone_deg: float = 0.05
    pitch_min: float = -89.9
    pitch_max: float = 89.9
    no_overshoot_deg: float = 8.0
    no_curve_deg: float = 10.0
    lock_cone_deg: float = 0.85
    lock_time: float = 0.08
    lock_servo_speed: float = 110.0
    urgent_speed_mult_max: float = 1.8
    urgent_duration_mult_min: float = 0.55
    urgent_curve_scale: float = 0.25
    urgent_no_curve_deg: float = 22.0
    urgent_no_overshoot_deg: float = 18.0
    urgent_lock_cone_deg: float = 0.60
    urgent_lock_time: float = 0.05
    urgent_lock_servo_speed: float = 220.0

CFG = HumanLookConfig()

def _wrap_deg(a):
    return (a + 180.0) % 360.0 - 180.0

def _clamp(x, lo, hi):
    return lo if x < lo else hi if x > hi else x

def _hypot2(a, b):
    return math.sqrt(a * a + b * b)

def _min_jerk(t):
    t3 = t * t * t
    t4 = t3 * t
    t5 = t4 * t
    return 10.0 * t3 - 15.0 * t4 + 6.0 * t5

def _map_speed(ang, cfg):
    if ang <= cfg.min_angle:
        return cfg.min_speed * (0.6 + 0.8 * (ang / max(1e-6, cfg.min_angle)))
    if ang >= cfg.max_angle:
        return cfg.max_speed
    r = (ang - cfg.min_angle) / (cfg.max_angle - cfg.min_angle)
    r = r ** 0.7
    return cfg.min_speed + (cfg.max_speed - cfg.min_speed) * r

def _lateral_curve(ang, cfg):
    r = _clamp((ang - cfg.min_angle) / (cfg.max_angle - cfg.min_angle), 0.0, 1.0)
    return cfg.max_curve_intensity * (r ** 1.2)

def _overshoot_frac_raw(ang, cfg):
    r = _clamp((ang - cfg.min_angle) / (cfg.max_angle - cfg.min_angle), 0.0, 1.0)
    base = cfg.base_overshoot + (cfg.max_overshoot - cfg.base_overshoot) * (r ** 0.9)
    return base * (0.75 + 0.5 * random.random())

def _sleep_step(dt, cfg):
    jitter = 1.0 + cfg.step_jitter * (random.random() - 0.5) * 2.0
    time.sleep(max(0.001, dt * jitter))

def _move_segment(a0, b0, dy, dp, duration, lateral_frac, cfg, target_yaw, target_pitch, tolerance, jitter_state=None, jitter_scale_override=None):
    hz = cfg.target_hz
    dt = 1.0 / hz
    steps = max(1, int(duration * hz))
    ang = max(_hypot2(dy, dp), 1e-6)
    ux, uy = dy / ang, dp / ang
    px, py = -uy, ux
    if jitter_state is None:
        jitter_state = {"jy": 0.0, "jp": 0.0}
    jy, jp = jitter_state["jy"], jitter_state["jp"]
    base_scale = cfg.jitter_scale_small_moves if ang < 12.0 else 1.0
    if jitter_scale_override is not None:
        base_scale = _clamp(jitter_scale_override, 0.0, 1.0)
    for i in range(1, steps + 1):
        t = i / steps
        s = _min_jerk(t)
        byaw = dy * s
        bpitch = dp * s
        bell = math.sin(math.pi * s)
        lat = lateral_frac * ang * bell
        lyaw = px * lat
        lpitch = py * lat
        jy = cfg.jitter_smooth * jy + (1.0 - cfg.jitter_smooth) * (random.random() - 0.5)
        jp = cfg.jitter_smooth * jp + (1.0 - cfg.jitter_smooth) * (random.random() - 0.5)
        jitter_yaw = cfg.jitter_deg * jy * base_scale
        jitter_pitch = cfg.jitter_deg * jp * base_scale
        yaw = _wrap_deg(a0 + byaw + lyaw + jitter_yaw)
        pitch = _clamp(b0 + bpitch + lpitch + jitter_pitch, cfg.pitch_min, cfg.pitch_max)

        
        if _hypot2(_wrap_deg(target_yaw - yaw), target_pitch - pitch) <= tolerance:
            
            minescript.player_set_orientation(target_yaw, target_pitch)
            break
        
        minescript.player_set_orientation(yaw, pitch)
        _sleep_step(dt, cfg)
    jitter_state["jy"] = jy
    jitter_state["jp"] = jp
    return jitter_state

def _urgency_value(urgent):
    if isinstance(urgent, bool):
        return 1.0 if urgent else 0.0
    try:
        return _clamp(float(urgent), 0.0, 1.0)
    except Exception:
        return 0.0

def look(target_yaw, target_pitch, cfg=CFG, urgent=0.0, tolerance=None):
    u = _urgency_value(urgent)
    a, b = minescript.player_orientation()
    dy = _wrap_deg(target_yaw - a)
    tp = _clamp(target_pitch, cfg.pitch_min, cfg.pitch_max)
    dp = tp - b
    ang = _hypot2(dy, dp)
    tol = tolerance if tolerance is not None else cfg.deadzone_deg
    if ang < tol:
        return
    no_curve_thresh = (1.0 - u) * cfg.no_curve_deg + u * cfg.urgent_no_curve_deg
    no_overshoot_thresh = (1.0 - u) * cfg.no_overshoot_deg + u * cfg.urgent_no_overshoot_deg
    no_curve = ang <= no_curve_thresh
    no_overshoot = ang <= no_overshoot_thresh
    wrap_band = (1.0 - u) * 18.0 + u * 24.0
    near_wrap = abs(abs(dy) - 180.0) <= wrap_band
    speed = _map_speed(ang, cfg) * (1.0 + u * (cfg.urgent_speed_mult_max - 1.0))
    base_T = _clamp(ang / max(1e-6, speed), cfg.min_duration, cfg.max_duration)
    duration = base_T * (1.0 - u * (1.0 - cfg.urgent_duration_mult_min)) * (0.9 + 0.2 * random.random())
    if no_curve:
        lateral_frac = 0.0
    else:
        lateral_frac = _lateral_curve(ang, cfg) * (0.85 + 0.3 * random.random())
        lateral_frac *= (1.0 - u * (1.0 - cfg.urgent_curve_scale))
    if no_overshoot or near_wrap:
        overshoot_y = 0.0
        overshoot_p = 0.0
    else:
        over_frac = _overshoot_frac_raw(ang, cfg) * (1.0 - 0.85 * u)
        axis_mix = cfg.overshoot_bias if abs(dy) >= abs(dp) else (cfg.overshoot_bias * 0.8)
        overshoot_y = dy * over_frac * (axis_mix + 0.22 * (random.random() - 0.5))
        overshoot_p = dp * over_frac * ((1.0 - axis_mix) + 0.22 * (random.random() - 0.5))
    main_jitter_scale = 1.0 - 0.85 * u
    jitter_state = _move_segment(a, b, dy + overshoot_y, dp + overshoot_p, duration, lateral_frac, cfg, target_yaw, target_pitch, tol, jitter_state=None, jitter_scale_override=main_jitter_scale)
    corr_dy = -overshoot_y
    corr_dp = -overshoot_p
    corr_ang = _hypot2(corr_dy, corr_dp)
    if corr_ang >= tol * 0.5:
        corr_speed = max(cfg.min_speed * 0.7, _map_speed(corr_ang, cfg) * (0.6 + 0.25 * u))
        corr_T = _clamp(corr_ang / corr_speed, cfg.min_duration * (0.55 - 0.10 * u), cfg.min_duration * (1.45 - 0.25 * u))
        _move_segment(_wrap_deg(a + dy + overshoot_y), _clamp(b + dp + overshoot_p, cfg.pitch_min, cfg.pitch_max), corr_dy, corr_dp, corr_T, lateral_frac * 0.35, cfg, target_yaw, target_pitch, tol, jitter_state=jitter_state, jitter_scale_override=0.25 * (1.0 - u))
    sy, sp = minescript.player_orientation()
    rem_dy = _wrap_deg(target_yaw - sy)
    rem_dp = _clamp(target_pitch, cfg.pitch_min, cfg.pitch_max) - sp
    rem_ang = _hypot2(rem_dy, rem_dp)
    if rem_ang > tol * 0.6:
        lock_speed = (1.0 - u) * cfg.lock_servo_speed + u * cfg.urgent_lock_servo_speed
        snap_T = _clamp(rem_ang / lock_speed, cfg.min_duration * (0.45 - 0.10 * u), cfg.min_duration * (0.9 - 0.15 * u))
        _move_segment(sy, sp, rem_dy, rem_dp, snap_T, 0.0, cfg, target_yaw, target_pitch, tol, jitter_state=jitter_state, jitter_scale_override=0.0)
    lock_deadline = time.time() + ((1.0 - u) * cfg.lock_time + u * cfg.urgent_lock_time)
    lock_cone = (1.0 - u) * cfg.lock_cone_deg + u * cfg.urgent_lock_cone_deg
    lock_speed = (1.0 - u) * cfg.lock_servo_speed + u * cfg.urgent_lock_servo_speed
    while time.time() < lock_deadline:
        cy, cp = minescript.player_orientation()
        edy = _wrap_deg(target_yaw - cy)
        edp = _clamp(target_pitch, cfg.pitch_min, cfg.pitch_max) - cp
        eang = _hypot2(edy, edp)
        if eang <= max(lock_cone, tol):
            break
        nib_T = _clamp(eang / lock_speed, cfg.min_duration * 0.30, cfg.min_duration * 0.55)
        _move_segment(cy, cp, edy, edp, nib_T, 0.0, cfg, target_yaw, target_pitch, tol, jitter_state=jitter_state, jitter_scale_override=0.0)
    for k in range(max(1, int(cfg.micro_settle_steps - round(1.0 * u)))):
        sy, sp = minescript.player_orientation()
        jitter = cfg.micro_settle_deg * (0.6 ** k)
        nudge_y = (random.random() - 0.5) * 2.0 * jitter
        nudge_p = (random.random() - 0.5) * 2.0 * jitter * 0.7
        _move_segment(sy, sp, nudge_y, nudge_p, cfg.min_duration * (0.32 - 0.06 * u), 0.0, cfg, target_yaw, target_pitch, tol, jitter_scale_override=0.25 * (1.0 - u))
        
# Down here is contributions from @No, to be able to look at a BlockPos

def grounddist(x,z,x2,z2):
     return ((x-x2) ** 2 + (z-z2) ** 2) ** .5

def get_axes(x, y, z):
     ax = x   #actual x, actual y, actual z
     ay = y - 1.7
     az = z 
     px, py, pz = minescript.get_player().position

     pitch = math.atan2(py-ay,grounddist(px,pz,ax,az))

     yaw = math.atan2(pz-az,px-ax)
     
     
     return (math.degrees(yaw) + 90, math.degrees(pitch))

def look_at(x,y,z, **kwargs):
    """
    Passes through:
    cfg=CFG, urgent=0.0, tolerance=None

    urgent: makes it faster
    
    """
    look(*get_axes(x,y,z), **kwargs)

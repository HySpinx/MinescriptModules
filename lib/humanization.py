import minescript
import math
import time
import random

from core.constants import (
    TIME_MIN_SLOT_SWITCH_DELAY,
    TIME_MAX_SLOT_SWITCH_DELAY,
    TIME_MIN_DELAY,
    TIME_MAX_DELAY,
    TIME_MIN_CLICK_DELAY,
    TIME_MAX_CLICK_DELAY,
    TIME_MIN_SWING_COOLDOWN,    
    TIME_MAX_SWING_COOLDOWN,
    TIME_MIN_HOLD_DELAY,
    TIME_MAX_HOLD_DELAY,
)

# Timing constants
MIN_SLOT_SWITCH_DELAY = TIME_MIN_SLOT_SWITCH_DELAY
MAX_SLOT_SWITCH_DELAY = TIME_MAX_SLOT_SWITCH_DELAY
MIN_DELAY = TIME_MIN_DELAY
MAX_DELAY = TIME_MAX_DELAY
MIN_CLICK_DELAY = TIME_MIN_CLICK_DELAY
MAX_CLICK_DELAY = TIME_MAX_CLICK_DELAY
MIN_SWING_COOLDOWN = TIME_MIN_SWING_COOLDOWN
MAX_SWING_COOLDOWN = TIME_MAX_SWING_COOLDOWN
MIN_HOLD_DELAY = TIME_MIN_HOLD_DELAY
MAX_HOLD_DELAY = TIME_MAX_HOLD_DELAY

# ==========================================
# 1. GENERAL USE FUNCTIONS
# ==========================================

def human_delay(min_delay, max_delay):
    '''
    This function will return a random delay between min_delay and max_delay.
    '''
        
    # betavariate(alpha=2.0, beta=5.0) creates a right-skewed distribution.
    # This more closely resembles human reaction times.
    scale = random.betavariate(2.0, 5.0)
    if max_delay < min_delay: # Catch edge case of user inputting bad values
        minescript.echo("Invalid human_delay values.")
        delay = 5 # Default to 5 seconds if user inputs bad values
    else:
        delay = min_delay + (scale * (max_delay - min_delay))
    time.sleep(delay)
    return

def generate_smooth_noise(time, frequency,amplitude, phase1, phase2):
    # Create noise to avoid hitting the same target unnaturally
    return (math.sin(time * frequency + phase1) * amplitude) + \
           (math.cos(time * frequency * 1.5 + phase2) * (amplitude * 0.5))

def generate_look_offset(min_x, max_x, min_y, max_y, min_z, max_z):
    # Generate a random offset for the look at function
    return (
        random.uniform(min_x, max_x),
        random.uniform(min_y, max_y),
        random.uniform(min_z, max_z)
    )

def do_slot_switch_delay():
    human_delay(MIN_SLOT_SWITCH_DELAY, MAX_SLOT_SWITCH_DELAY)

def do_normal_delay():
    human_delay(MIN_DELAY, MAX_DELAY)

def do_click_delay():
    human_delay(MIN_CLICK_DELAY, MAX_CLICK_DELAY)

def do_click_cooldown():
    human_delay(MIN_SWING_COOLDOWN, MAX_SWING_COOLDOWN)

def do_hold_delay():
    human_delay(MIN_HOLD_DELAY, MAX_HOLD_DELAY) 
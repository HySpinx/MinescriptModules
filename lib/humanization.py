import minescript
import math
import time
import random

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
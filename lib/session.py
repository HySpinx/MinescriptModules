import minescript
import lib.minescript_plus as minescript_plus
import time
import random
import lib.humanization as human
import lib.movement as movement

from core.state import pause_event, run_event

class SessionScheduler:
    def __init__(self, duration_hrs=1, num_breaks=0, min_break_mins=0, max_break_mins=0):
        self.total_duration = float(duration_hrs) * 3600.0
        self.num_breaks = int(num_breaks)
        self.min_break = float(min_break_mins) * 60.0
        self.max_break = float(max_break_mins) * 60.0

        self.session_start = time.time()
        self.session_end = self.session_start + self.total_duration

        # Schedule breaks dynamically within the session limit
        self.upcoming_breaks = []
        if self.num_breaks > 0:
            # Divide session into segments to distribute breaks relatively evenly
            chunk_size = self.total_duration / (self.num_breaks + 1)
            for i in range(self.num_breaks):
                # Add random offsets so intervals don't look robotic
                base_time = self.session_start + (chunk_size * (i + 1))
                random_offset = random.uniform(-chunk_size * 0.2, chunk_size * 0.2)
                self.upcoming_breaks.append(base_time + random_offset)
        
        self.upcoming_breaks.sort()
        minescript.echo(f"§a[Session] duration: {self.total_duration/3600:.2f} hours, breaks: {self.num_breaks}, min break: {self.min_break/60:.2f} minutes, max break: {self.max_break/60:.2f} minutes")

    def check_schedule(self, pause_event, run_event):
        """
        Checks the timeline and blocks if a break is needed.
        Returns the duration paused so farming scripts can offset their failsafe timers.
        """
        current_time = time.time()

        # 1. Total Duration Limit Reached
        if current_time >= self.session_end:
            minescript.echo("§c[Session] Total duration reached. Disconnecting.")
            movement.stop_all_movement()
            human.human_delay(3.5, 10.0)
            minescript_plus.Client.disconnect()

        # 2. Scheduled Break Reached
        if self.upcoming_breaks and current_time >= self.upcoming_breaks[0]:
            start_pause_time = time.time()
            break_duration = human.human_delay(self.min_break, self.max_break)
            self.upcoming_breaks.pop(0) # Remove the consumed break
            
            minescript.echo(f"§e[Session] Taking a scheduled break for {break_duration/60:.2f} minutes.")
            
            # Sync with global state events to halt farming
            pause_event.set()
            run_event.clear()
            movement.stop_all_movement()
            
            # Block the thread while breaking
            time.sleep(break_duration) 
            
            minescript.echo("§a[Session] Break over. Resuming...")
            
            # Sync to resume global state
            pause_event.clear()
            run_event.set()
            
            end_pause_time = time.time()
            return end_pause_time - start_pause_time

        return 0.0 # No break was taken
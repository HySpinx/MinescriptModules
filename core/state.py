from shutil import move
import threading
import time

import lib.lib as lib
import lib.movement as move
import minescript

from lib.services.service_context import update_state_driven_pause

bot_active = threading.Event()
pause_event = threading.Event()
run_event = threading.Event()
pest_hunt_event = threading.Event()
restart_event = threading.Event()

# Preserve existing behavior where scripts expect active state at startup.
bot_active.set()
run_event.set()


class ScriptState:
    """Per-module event container to avoid cross-script collisions."""

    def __init__(self, active_by_default=True):
        self.bot_active = threading.Event()
        self.pause_event = threading.Event()
        self.run_event = threading.Event()
        if active_by_default:
            self.bot_active.set()
            self.run_event.set()


def create_script_state(active_by_default=True):
    """Create isolated event state for a single module/script."""
    return ScriptState(active_by_default=active_by_default)


def check_pause():
    """Block until resumed if global pause is active; stop movement and alert."""
    if pause_event.is_set():
        minescript.echo("=== PAUSED - Press configured key to resume ===")
        move.stop_all_movement()
        lib.play_alert_sound()
        pause_start = time.time()
        run_event.wait()
        pause_duration = time.time() - pause_start
        pause_event.clear()
        minescript.echo("=== RESUMED ===")
        return pause_duration
    return 0


def apply_service_lifecycle(service):
    """Apply global run/pause state to a service."""
    update_state_driven_pause(service, bot_active, pause_event, run_event)

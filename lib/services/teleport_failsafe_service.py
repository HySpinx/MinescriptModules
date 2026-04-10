import math
import os
import time

import minescript

from lib.services.base_service import BaseService


class TeleportFailsafeService(BaseService):
    def __init__(
        self,
        pos_tolerance=4.0,
        yaw_tolerance=30.0,
        pitch_tolerance=30.0,
        alarm_event=None,
    ):
        super().__init__("teleport_failsafe", tick_interval=0.05)
        self.pos_tolerance = pos_tolerance
        self.yaw_tolerance = yaw_tolerance
        self.pitch_tolerance = pitch_tolerance
        self.alarm_event = alarm_event
        self.last_pos = None
        self.last_rot = None
        self.reset_baseline()

    def reset_baseline(self):
        self.last_pos = minescript.player_position()
        self.last_rot = minescript.player_orientation()

    def on_resume(self):
        # Re-baseline after legitimate teleports/warps.
        self.reset_baseline()

    def run_step(self):
        if self.last_pos is None or self.last_rot is None:
            self.reset_baseline()
            return

        curr_pos = minescript.player_position()
        curr_rot = minescript.player_orientation()
        dist = math.dist(self.last_pos, curr_pos)
        yaw_diff = abs((curr_rot[0] - self.last_rot[0] + 180) % 360 - 180)
        pitch_diff = abs(curr_rot[1] - self.last_rot[1])

        if (
            dist > self.pos_tolerance
            or yaw_diff > self.yaw_tolerance
            or pitch_diff > self.pitch_tolerance
        ):
            self.trigger_failsafe(
                f"Teleport/Rot Check! Dist: {dist:.2f}, Yaw: {yaw_diff:.2f}, Pitch: {pitch_diff:.2f}"
            )
            return

        self.last_pos = curr_pos
        self.last_rot = curr_rot

    def trigger_failsafe(self, reason):
        self.stop()
        minescript.player_press_attack(False)
        minescript.player_press_use(False)
        minescript.player_press_forward(False)
        minescript.player_press_backward(False)
        minescript.player_press_left(False)
        minescript.player_press_right(False)

        if self.alarm_event is not None:
            self.alarm_event.set()
            import lib.lib as lib

            lib.play_restart_alarm(self.alarm_event)

        minescript.echo(f"§4[FAILSAFE TRIGGERED] {reason}")
        time.sleep(0.2)
        minescript.execute("/disconnect Admin Check Detected!")
        os._exit(1)

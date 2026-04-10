import random
import time

import minescript
import lib.movement as move

from lib.services.base_service import BaseService
from core.state import bot_active, run_event


class ProximityMonitorService(BaseService):
    def __init__(self, pause_event, safe_radius=5.0, suspicion_limit=15):
        super().__init__("proximity_monitor", tick_interval=2.0)
        self.pause_event = pause_event
        self.safe_radius = safe_radius
        self.suspicion_limit = suspicion_limit
        self.suspicion_ledger = {}
        self.valid_held_items = ["fishing_rod", "hoe", "axe", "pickaxe"]

    def run_step(self):
        if (not bot_active.is_set()) or self.pause_event.is_set() or (not run_event.is_set()):
            return
        nearby_entities = minescript.entities(max_distance=self.safe_radius)
        current_players_in_radius = set()
        for ent in nearby_entities:
            if getattr(ent, "type", "") != "player":
                continue
            name = getattr(ent, "name", "Unknown")
            if name == minescript.player_name() or "NPC" in name:
                continue
            current_players_in_radius.add(name)
            held_item = str(getattr(ent, "held_item", "")).lower()
            is_participating = any(valid_item in held_item for valid_item in self.valid_held_items)
            if not is_participating:
                self.suspicion_ledger[name] = self.suspicion_ledger.get(name, 0) + 1
                if self.suspicion_ledger[name] >= self.suspicion_limit:
                    self._evade_player(name)
                    return
            elif name in self.suspicion_ledger and self.suspicion_ledger[name] > 0:
                self.suspicion_ledger[name] -= 1

        stale_players = list(set(self.suspicion_ledger.keys()) - current_players_in_radius)
        for player_name in stale_players:
            del self.suspicion_ledger[player_name]

    def _evade_player(self, player_name):
        minescript.echo(f"§c[ProximityMonitor] Player '{player_name}' is loitering! Evading...")
        self.pause_event.set()
        self.stop()
        move.stop_attack()
        move.stop_use()
        minescript.player_press_forward(False)
        time.sleep(random.uniform(0.5, 1.2))
        minescript.execute("so laggy brb")
        time.sleep(random.uniform(1.0, 2.0))
        minescript.execute("/hub")
        time.sleep(5.0)

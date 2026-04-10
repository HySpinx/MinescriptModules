import queue
import random
import time

import minescript
from minescript_plus import Gui

from constants import SUSPICION_USERNAME
from services.base_service import BaseService
from state import bot_active, pause_event, run_event


class ChatMonitorService(BaseService):
    def __init__(self):
        super().__init__("chat_monitor", tick_interval=0.1)
        self.username = SUSPICION_USERNAME.lower()
        self.last_response_time = 0
        self.cooldown = 300
        self.generic_responses = ["im busy bro", "leave me alone man"]
        self._event_queue = minescript.EventQueue()
        self._event_queue.register_chat_listener()
        self._last_actionbar_message = None

    def _process_text(self, text):
        lower_text = text.lower()
        if self.username in lower_text and f"<{self.username}>" not in lower_text:
            self._handle_mention(text)

    def stop(self, timeout=2.0):
        super().stop(timeout=timeout)
        self._event_queue.unregister_all()

    def run_step(self):
        if (not bot_active.is_set()) or pause_event.is_set() or (not run_event.is_set()):
            return

        while True:
            try:
                event = self._event_queue.get(block=False)
            except queue.Empty:
                break
            if event.type == minescript.EventType.CHAT:
                self._process_text(event.message)

        actionbar_message = Gui.get_actionbar()
        if actionbar_message and actionbar_message != self._last_actionbar_message:
            self._last_actionbar_message = actionbar_message
            self._process_text(actionbar_message)
        elif not actionbar_message:
            self._last_actionbar_message = None

    def _handle_mention(self, line):
        current_time = time.time()
        if current_time - self.last_response_time < self.cooldown:
            return

        self.last_response_time = current_time
        response = random.choice(self.generic_responses)
        reading_time = random.uniform(1.5, 3.5)
        time.sleep(reading_time)
        typing_time = len(response) / random.uniform(4.0, 6.0)
        minescript.player_press_forward(False)
        minescript.player_press_attack(False)
        time.sleep(typing_time)
        minescript.execute(response)
        minescript.echo(f"§e[ChatMonitor] Responded to mention with: '{response}'")

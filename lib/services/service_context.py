import time
from contextlib import contextmanager

from lib.services.service_registry import ServiceRegistry


SERVICE_REGISTRY = ServiceRegistry()


def register_service(service):
    return SERVICE_REGISTRY.register(service)


@contextmanager
def pause_services(*service_ids):
    for service_id in service_ids:
        SERVICE_REGISTRY.pause(service_id)
    try:
        yield
    finally:
        for service_id in service_ids:
            SERVICE_REGISTRY.resume(service_id)


@contextmanager
def pause_temporarily(service_id, duration_seconds):
    SERVICE_REGISTRY.pause(service_id)
    try:
        yield
        time.sleep(max(0.0, duration_seconds))
    finally:
        SERVICE_REGISTRY.resume(service_id)


def update_state_driven_pause(service, bot_active, pause_event, run_event=None):
    should_pause = (not bot_active.is_set()) or pause_event.is_set()
    if run_event is not None and not run_event.is_set():
        should_pause = True

    if should_pause:
        service.pause()
    else:
        service.resume()

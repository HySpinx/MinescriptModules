import threading


class ServiceRegistry:
    def __init__(self):
        self._services = {}
        self._lock = threading.Lock()

    def register(self, service):
        with self._lock:
            self._services[service.service_id] = service
        return service

    def get(self, service_id):
        return self._services.get(service_id)

    def unregister(self, service_id):
        with self._lock:
            return self._services.pop(service_id, None)

    def start(self, service_id):
        svc = self.get(service_id)
        if svc is not None:
            svc.start()
        return svc

    def stop(self, service_id):
        svc = self.get(service_id)
        if svc is not None:
            svc.stop()
        return svc

    def pause(self, service_id):
        svc = self.get(service_id)
        if svc is not None:
            svc.pause()
        return svc

    def resume(self, service_id):
        svc = self.get(service_id)
        if svc is not None:
            svc.resume()
        return svc

    def start_all(self):
        for svc in list(self._services.values()):
            svc.start()

    def stop_all(self):
        for svc in list(self._services.values()):
            svc.stop()

    def pause_all(self):
        for svc in list(self._services.values()):
            svc.pause()

    def resume_all(self):
        for svc in list(self._services.values()):
            svc.resume()

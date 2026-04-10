import threading

# The single global lock for all Java-interaction calls
java_lock = threading.Lock()
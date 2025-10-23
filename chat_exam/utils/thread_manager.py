from threading import Thread, Lock
import logging

logger = logging.getLogger(__name__)

# === Locks ===
_thread_lock = Lock()

def run_in_thread(target, *args, **kwargs):
    """Simple helper to run background task."""
    thread = Thread(target=target, args=args, kwargs=kwargs, daemon=True)
    thread.start()
    logger.info(f"[THREAD] Started {target.__name__}")
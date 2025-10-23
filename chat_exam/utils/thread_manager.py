# chat_exam/utils/thread_manager.py
from concurrent.futures import ThreadPoolExecutor
import logging

logger = logging.getLogger(__name__)

_executor = ThreadPoolExecutor(max_workers=30)

def run_in_thread(func, *args, **kwargs):
    """Submit a function to the shared thread executor."""
    future = _executor.submit(func, *args, **kwargs)
    logger.info(f"[THREAD] Started task {func.__name__}")
    return future



"""
# --- Ensure functions ---
def ensure_questions_ready(...): ...
def ensure_verdict_ready(...): ...

# --- Background workers ---
def _generate_questions_background(...): ...
def _generate_verdict_background(...): ...

# --- Async spawners ---
def _generate_questions_async(...): ...
def _generate_verdict_async(...): ...

# --- Utility ---
def _generate_content_string(...): ..."""
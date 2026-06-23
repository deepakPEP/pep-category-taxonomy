import os
from common.config import STATE_DIR
from common.logger import get_logger

logger = get_logger("checkpoint")

os.makedirs(STATE_DIR, exist_ok=True)

def _state_file(phase: str) -> str:
    return os.path.join(STATE_DIR, f"{phase}.done")

def is_completed(phase: str) -> bool:
    completed = os.path.exists(_state_file(phase))
    if completed:
        logger.info(f"Phase {phase} already completed — skipping.")
    return completed

def mark_completed(phase: str) -> None:
    path = _state_file(phase)
    with open(path, "w") as f:
        f.write("done")
    logger.info(f"Phase {phase} marked as completed.")

def reset_checkpoint(phase: str) -> None:
    path = _state_file(phase)
    if os.path.exists(path):
        os.remove(path)
        logger.info(f"Checkpoint for phase {phase} reset.")

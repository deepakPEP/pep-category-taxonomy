import json
import os
import time
from common.config import METRICS_DIR
from common.logger import get_logger

logger = get_logger("metrics")

os.makedirs(METRICS_DIR, exist_ok=True)

_metrics: dict = {}
_start_time: float = time.time()

def set_metric(key: str, value) -> None:
    _metrics[key] = value
    logger.info(f"Metric set: {key} = {value}")

def increment_metric(key: str, amount: int = 1) -> None:
    _metrics[key] = _metrics.get(key, 0) + amount

def save_metrics() -> None:
    elapsed_minutes = round((time.time() - _start_time) / 60, 2)
    _metrics["processing_time_minutes"] = elapsed_minutes

    output_path = os.path.join(METRICS_DIR, "metrics.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(_metrics, f, indent=2)

    logger.info(f"Metrics saved to {output_path}")
    logger.info(json.dumps(_metrics, indent=2))

def get_metrics() -> dict:
    return dict(_metrics)

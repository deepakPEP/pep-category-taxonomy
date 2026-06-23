import os
import glob
import json
import pandas as pd
from tqdm import tqdm
from common.config import INPUT_DIR, PHASE1_BATCH_SIZE, PHASE1_OUTPUT_DIR
from common.logger import get_logger
from common.checkpoint import is_completed, mark_completed
from common.metrics import set_metric

logger = get_logger("phase1")

os.makedirs(PHASE1_OUTPUT_DIR, exist_ok=True)

def detect_input_file() -> str:
    """
    Auto-detect the single CSV file in the input directory.
    Raises clear errors if zero or multiple CSVs are found.
    """
    csv_files = glob.glob(os.path.join(INPUT_DIR, "*.csv"))

    if not csv_files:
        raise FileNotFoundError(
            f"No CSV file found in '{INPUT_DIR}/'. "
            f"Place your taxonomy CSV there and re-run."
        )

    if len(csv_files) > 1:
        names = [os.path.basename(f) for f in csv_files]
        raise ValueError(
            f"Multiple CSV files found in '{INPUT_DIR}/': {names}. "
            f"Keep only one taxonomy CSV and re-run."
        )

    detected = csv_files[0]
    logger.info(f"Input file detected: {detected}")
    return detected

def load_csv(filepath: str) -> pd.DataFrame:
    """
    Load CSV with auto-detection of delimiter (tab or comma).
    Normalize column names to: category, subcategory, product_category.
    """
    # Try tab-separated first, then comma-separated
    for sep in ["\t", ","]:
        try:
            df = pd.read_csv(filepath, sep=sep, engine="python")
            if len(df.columns) >= 3:
                logger.info(f"Loaded with separator: {'TAB' if sep == chr(9) else 'COMMA'}")
                break
        except Exception:
            continue
    else:
        raise ValueError(f"Could not parse CSV file: {filepath}")

    df.columns = [c.strip() for c in df.columns]
    logger.info(f"Columns detected: {list(df.columns)}")

    # Normalize column names regardless of original naming
    col_map = {}
    for col in df.columns:
        lower = col.lower().replace(" ", "_").replace("-", "_")
        if "product" in lower:
            col_map[col] = "product_category"
        elif "sub" in lower:
            col_map[col] = "subcategory"
        elif "category" in lower or "cat" in lower:
            col_map[col] = "category"

    if len(col_map) < 3:
        raise ValueError(
            f"Could not map columns to category/subcategory/product_category. "
            f"Found columns: {list(df.columns)}. "
            f"Expected columns containing: 'category', 'sub', 'product'."
        )

    df = df.rename(columns=col_map)
    df = df[["category", "subcategory", "product_category"]]
    df = df.dropna(subset=["category", "subcategory", "product_category"])
    df = df[df["product_category"].str.strip() != ""]

    return df

def run():
    if is_completed("phase1"):
        return

    logger.info("Starting Phase 1 — Batch Generator")

    input_file = detect_input_file()
    df = load_csv(input_file)

    total = len(df)
    logger.info(f"Total valid rows loaded: {total}")
    set_metric("input_rows", total)
    set_metric("input_file", os.path.basename(input_file))

    rows = df.to_dict(orient="records")
    batches = [
        rows[i:i + PHASE1_BATCH_SIZE]
        for i in range(0, total, PHASE1_BATCH_SIZE)
    ]

    set_metric("batches", len(batches))
    logger.info(f"Batches to create: {len(batches)} (size: {PHASE1_BATCH_SIZE})")

    for idx, batch in enumerate(tqdm(batches, desc="Phase 1 batching"), start=1):
        filename = os.path.join(PHASE1_OUTPUT_DIR, f"batch_{idx:04d}.json")
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(batch, f, indent=2, ensure_ascii=False)

    logger.info(f"Phase 1 complete. {len(batches)} batch files → {PHASE1_OUTPUT_DIR}/")
    mark_completed("phase1")

if __name__ == "__main__":
    run()

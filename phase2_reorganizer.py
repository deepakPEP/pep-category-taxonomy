import os
import json
import glob
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
from common.config import (
    PHASE1_OUTPUT_DIR, PHASE2_OUTPUT_DIR,
    MAX_WORKERS, PHASE2_BATCH_SIZE, TAXONOMY_PROMPT_FILE
)
from common.logger import get_logger
from common.checkpoint import is_completed, mark_completed
from common.ollama_client import call_ollama_json

logger = get_logger("phase2")

os.makedirs(PHASE2_OUTPUT_DIR, exist_ok=True)

def load_prompt() -> str:
    with open(TAXONOMY_PROMPT_FILE, "r", encoding="utf-8") as f:
        return f.read().strip()

def process_chunk(chunk: list, chunk_label: str, prompt_template: str) -> list:
    chunk_text = json.dumps(chunk, indent=2, ensure_ascii=False)
    prompt = f"{prompt_template}\n\nINPUT:\n{chunk_text}"

    logger.info(f"Processing {chunk_label} ({len(chunk)} items)")
    result = call_ollama_json(prompt, label=chunk_label)

    if not isinstance(result, list):
        logger.warning(f"{chunk_label} returned non-list — wrapping.")
        result = [result] if isinstance(result, dict) else []

    return result

def run():
    if is_completed("phase2"):
        return

    logger.info("Starting Phase 2 — Qwen Taxonomy Architect")

    prompt_template = load_prompt()
    batch_files = sorted(glob.glob(os.path.join(PHASE1_OUTPUT_DIR, "batch_*.json")))

    if not batch_files:
        raise FileNotFoundError(f"No batch files found in {PHASE1_OUTPUT_DIR}")

    # Load all rows and re-chunk into PHASE2_BATCH_SIZE
    all_rows = []
    for bf in batch_files:
        with open(bf, "r", encoding="utf-8") as f:
            all_rows.extend(json.load(f))

    chunks = [
        all_rows[i:i + PHASE2_BATCH_SIZE]
        for i in range(0, len(all_rows), PHASE2_BATCH_SIZE)
    ]

    logger.info(f"Total rows: {len(all_rows)} | Chunks: {len(chunks)} (size: {PHASE2_BATCH_SIZE})")

    all_results = []
    failed_chunks = []

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {
            executor.submit(
                process_chunk,
                chunk,
                f"chunk_{idx:04d}",
                prompt_template
            ): idx
            for idx, chunk in enumerate(chunks, start=1)
        }

        for future in tqdm(as_completed(futures), total=len(futures), desc="Phase 2"):
            idx = futures[future]
            try:
                result = future.result()
                all_results.extend(result)

                out_file = os.path.join(PHASE2_OUTPUT_DIR, f"reorganized_chunk_{idx:04d}.json")
                with open(out_file, "w", encoding="utf-8") as f:
                    json.dump(result, f, indent=2, ensure_ascii=False)

            except Exception as ex:
                logger.exception(f"Failed chunk_{idx:04d}: {ex}")
                failed_chunks.append(idx)

    if failed_chunks:
        logger.warning(f"Failed chunks: {failed_chunks}")

    df = pd.DataFrame(all_results)
    df = df.dropna()
    df = df.drop_duplicates()

    merged_path = os.path.join(PHASE2_OUTPUT_DIR, "merged_reorganized.csv")
    df.to_csv(merged_path, index=False, encoding="utf-8")
    logger.info(f"Phase 2 complete. {len(df)} rows → {merged_path}")

    mark_completed("phase2")

if __name__ == "__main__":
    run()

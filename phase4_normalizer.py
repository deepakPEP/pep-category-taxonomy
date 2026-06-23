import os
import json
import glob
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
from common.config import (
    PHASE2_OUTPUT_DIR, PHASE3_OUTPUT_DIR, PHASE4_OUTPUT_DIR,
    MAX_WORKERS, PHASE4_BATCH_SIZE, NORMALIZE_PROMPT_FILE
)
from common.logger import get_logger
from common.checkpoint import is_completed, mark_completed
from common.ollama_client import call_ollama_json
from common.metrics import set_metric

logger = get_logger("phase4")

os.makedirs(PHASE4_OUTPUT_DIR, exist_ok=True)

def load_prompt() -> str:
    with open(NORMALIZE_PROMPT_FILE, "r", encoding="utf-8") as f:
        return f.read().strip()

def normalize_cluster(cluster_id: str, members: list, prompt_template: str) -> dict:
    members_text = "\n".join(f"- {m}" for m in members)
    prompt = f"{prompt_template}\n\nInput cluster ({cluster_id}):\n{members_text}"

    result = call_ollama_json(prompt, label=cluster_id)

    if isinstance(result, dict) and "canonical_name" in result:
        return {
            "cluster_id": cluster_id,
            "canonical_name": result["canonical_name"],
            "merged": result.get("merged", members)
        }

    # Fallback: use first member as canonical
    logger.warning(f"Unexpected response for {cluster_id}, using first member as canonical.")
    return {
        "cluster_id": cluster_id,
        "canonical_name": members[0],
        "merged": members
    }

def run():
    if is_completed("phase4"):
        return

    logger.info("Starting Phase 4 — Qwen Synonym Merge")

    clusters_path = os.path.join(PHASE3_OUTPUT_DIR, "clusters.json")
    if not os.path.exists(clusters_path):
        raise FileNotFoundError(f"Phase 3 output not found: {clusters_path}")

    with open(clusters_path, "r", encoding="utf-8") as f:
        clusters = json.load(f)

    # Load the merged reorganized CSV from Phase 2
    merged_csv = os.path.join(PHASE2_OUTPUT_DIR, "merged_reorganized.csv")
    df_base = pd.read_csv(merged_csv)

    prompt_template = load_prompt()
    cluster_items = list(clusters.items())

    logger.info(f"Normalizing {len(cluster_items)} clusters with max_workers={MAX_WORKERS}")

    canonical_map = {}  # old_name → canonical_name

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {
            executor.submit(normalize_cluster, cid, members, prompt_template): cid
            for cid, members in cluster_items
        }

        for future in tqdm(as_completed(futures), total=len(futures), desc="Phase 4"):
            cluster_id = futures[future]
            try:
                result = future.result()
                canonical = result["canonical_name"]
                for member in result["merged"]:
                    canonical_map[member] = canonical
            except Exception as ex:
                logger.exception(f"Failed cluster {cluster_id}: {ex}")

    set_metric("duplicates_removed", sum(
        1 for k, v in canonical_map.items() if k != v
    ))

    # Apply canonical map to the base dataframe
    df_base["product_category"] = df_base["product_category"].apply(
        lambda x: canonical_map.get(x, x)
    )
    df_base = df_base.drop_duplicates()

    output_path = os.path.join(PHASE4_OUTPUT_DIR, "normalized.csv")
    df_base.to_csv(output_path, index=False, encoding="utf-8")

    logger.info(f"Phase 4 complete. Normalized CSV: {output_path} ({len(df_base)} rows)")
    mark_completed("phase4")

if __name__ == "__main__":
    run()

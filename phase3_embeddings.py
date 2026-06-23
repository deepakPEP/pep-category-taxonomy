import os
import json
import numpy as np
import pandas as pd
import faiss
from sentence_transformers import SentenceTransformer
from common.config import PHASE2_OUTPUT_DIR, PHASE3_OUTPUT_DIR, EMBEDDING_MODEL
from common.logger import get_logger
from common.checkpoint import is_completed, mark_completed
from common.metrics import set_metric

logger = get_logger("phase3")

os.makedirs(PHASE3_OUTPUT_DIR, exist_ok=True)

SIMILARITY_THRESHOLD = 0.92

def run():
    if is_completed("phase3"):
        return

    logger.info("Starting Phase 3 — BGE Embeddings + FAISS Clustering")

    input_csv = os.path.join(PHASE2_OUTPUT_DIR, "merged_reorganized.csv")
    if not os.path.exists(input_csv):
        raise FileNotFoundError(f"Phase 2 output not found: {input_csv}")

    df = pd.read_csv(input_csv)
    df = df.dropna(subset=["product_category"])
    product_names = df["product_category"].astype(str).tolist()

    logger.info(f"Generating embeddings for {len(product_names)} product categories...")

    model = SentenceTransformer(EMBEDDING_MODEL)
    embeddings = model.encode(
        product_names,
        batch_size=64,
        show_progress_bar=True,
        normalize_embeddings=True
    )

    embeddings_np = np.array(embeddings).astype("float32")

    # Build FAISS index using inner product (cosine similarity after normalization)
    dimension = embeddings_np.shape[1]
    index = faiss.IndexFlatIP(dimension)
    index.add(embeddings_np)

    logger.info("FAISS index built. Running similarity search...")

    # Search each vector for its top-10 neighbors
    k = min(10, len(product_names))
    similarities, indices = index.search(embeddings_np, k)

    # Build clusters using union-find / visited set approach
    visited = set()
    clusters = {}
    cluster_id = 0

    for i in range(len(product_names)):
        if i in visited:
            continue

        cluster_members = [product_names[i]]
        visited.add(i)

        for j_idx, sim in zip(indices[i], similarities[i]):
            if j_idx == i:
                continue
            if sim >= SIMILARITY_THRESHOLD and j_idx not in visited:
                cluster_members.append(product_names[j_idx])
                visited.add(j_idx)

        if len(cluster_members) > 1:
            clusters[f"cluster_{cluster_id:04d}"] = cluster_members
            cluster_id += 1

    set_metric("clusters_created", len(clusters))
    logger.info(f"Clusters found: {len(clusters)}")

    output_path = os.path.join(PHASE3_OUTPUT_DIR, "clusters.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(clusters, f, indent=2, ensure_ascii=False)

    logger.info(f"Phase 3 complete. Clusters saved to {output_path}")
    mark_completed("phase3")

if __name__ == "__main__":
    run()

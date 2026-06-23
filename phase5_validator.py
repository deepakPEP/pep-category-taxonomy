import os
import pandas as pd
from common.config import PHASE4_OUTPUT_DIR, PHASE5_OUTPUT_DIR
from common.logger import get_logger
from common.checkpoint import is_completed, mark_completed
from common.metrics import set_metric, save_metrics

logger = get_logger("phase5")

os.makedirs(PHASE5_OUTPUT_DIR, exist_ok=True)

# Categories that should NOT contain software products
NON_SOFTWARE_CATEGORIES = {
    "Apparel & Fashion",
    "Agriculture & Food Products",
    "Machinery & Equipment",
    "Chemicals",
    "Electrical & Electronics",
    "Construction & Real Estate",
    "Healthcare & Medical",
    "Automotive",
    "Furniture & Interiors",
    "Textiles & Fabrics"
}

SOFTWARE_KEYWORDS = [
    "software", "erp", "crm", "saas", "platform", "app", "application",
    "system", "management system", "tracking system", "automation"
]

def is_software(name: str) -> bool:
    lower = name.lower()
    return any(kw in lower for kw in SOFTWARE_KEYWORDS)

def run():
    if is_completed("phase5"):
        return

    logger.info("Starting Phase 5 — Validator")

    input_path = os.path.join(PHASE4_OUTPUT_DIR, "normalized.csv")
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Phase 4 output not found: {input_path}")

    df = pd.read_csv(input_path)
    initial_count = len(df)
    logger.info(f"Input rows: {initial_count}")

    issues = []

    # 1. Remove exact duplicates
    before = len(df)
    df = df.drop_duplicates()
    dupes_removed = before - len(df)
    logger.info(f"Exact duplicates removed: {dupes_removed}")

    # 2. Detect same product_category under multiple subcategories
    multi_sub = df.groupby("product_category")["subcategory"].nunique()
    multi_sub_products = multi_sub[multi_sub > 1].index.tolist()
    if multi_sub_products:
        logger.warning(f"Products in multiple subcategories: {len(multi_sub_products)}")
        for p in multi_sub_products[:10]:
            issues.append(f"MULTI_SUBCATEGORY: {p}")

    # 3. Detect software inside non-software categories
    misplaced_mask = df.apply(
        lambda row: (
            row["category"] in NON_SOFTWARE_CATEGORIES and
            is_software(str(row["product_category"]))
        ),
        axis=1
    )
    misplaced = df[misplaced_mask]
    if not misplaced.empty:
        logger.warning(f"Misplaced software products detected: {len(misplaced)}")
        for _, row in misplaced.iterrows():
            issues.append(
                f"MISPLACED_SOFTWARE: '{row['product_category']}' under '{row['category']}'"
            )
        # Auto-correct: move to Software & IT Solutions
        df.loc[misplaced_mask, "category"] = "Software & IT Solutions"
        logger.info(f"Auto-corrected {len(misplaced)} misplaced software products.")

    # 4. Drop rows with empty critical fields
    df = df.dropna(subset=["category", "subcategory", "product_category"])
    df = df[df["product_category"].str.strip() != ""]

    # 5. Sort hierarchy
    df = df.sort_values(
        by=["category", "subcategory", "product_category"]
    ).reset_index(drop=True)

    final_count = len(df)
    set_metric("final_products", final_count)
    set_metric("validation_issues", len(issues))

    # Write final taxonomy
    output_path = os.path.join(PHASE5_OUTPUT_DIR, "final_taxonomy.csv")
    df.to_csv(output_path, index=False, encoding="utf-8")
    logger.info(f"Final taxonomy written: {output_path} ({final_count} rows)")

    # Write issues log
    if issues:
        issues_path = os.path.join(PHASE5_OUTPUT_DIR, "validation_issues.txt")
        with open(issues_path, "w", encoding="utf-8") as f:
            f.write("\n".join(issues))
        logger.warning(f"Validation issues logged to {issues_path}")

    save_metrics()
    mark_completed("phase5")
    logger.info("Phase 5 complete.")

if __name__ == "__main__":
    run()

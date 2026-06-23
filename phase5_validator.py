import os
import pandas as pd
from common.config import PHASE4_OUTPUT_DIR, PHASE5_OUTPUT_DIR
from common.logger import get_logger
from common.checkpoint import is_completed, mark_completed
from common.metrics import set_metric, save_metrics

logger = get_logger("phase5")

os.makedirs(PHASE5_OUTPUT_DIR, exist_ok=True)

NON_SOFTWARE_CATEGORIES = {
    "Apparel & Fashion",
    "Agriculture & Food Products",
    "Machinery & Equipment",
    "Chemicals",
    "Electrical & Electronics",
    "Construction & Infrastructure",
    "Health & Personal Care",
    "Automotive & Transport",
    "Home & Lifestyle",
    "Tools & Hardware",
    "Packaging & Printing",
    "Office Supplies & Equipment",
}

# Genuine software keywords — standalone word match only
SOFTWARE_KEYWORDS = [
    'software', 'erp', 'crm', 'saas',
    'management system', 'tracking system',
    'automation system', 'information system',
    'ecommerce platform', 'marketplace platform',
    'management platform', 'analytics platform',
]

# Physical products that contain software-like words but are NOT software
PHYSICAL_PRODUCT_WHITELIST = [
    'platform bed', 'platform beds',
    'platform scale', 'platform scales',
    'platform ladder', 'platform ladders',
    'platform lift', 'platform lifts',
    'platform shoe', 'platform shoes',
    'platform rental', 'platform rentals',
    'scissor lift', 'scissor lifts',
    'dashboard cover', 'dashboard covers',
    'dashboard organizer', 'dashboard organizers',
    'dashboard polish', 'dashboard cleaner',
    'dashboard lighting', 'dashboard component',
    'dashboard components',
    'dashboard & instrument',
    'app control',
    'app sync',
    'smart bulb', 'smart bulbs',
    'smart thermometer', 'smart thermometers',
    'alarm system',
    'building management system',
    'grout filling',
    'sealant application',
    'organic dye',
    'home lift', 'home lifts',
    'mobile app monitoring',
    'music production',
    'ott platform',
    'fleet tracking',
    'fleet software',
]

def is_software(name: str) -> bool:
    lower = name.lower().strip()

    # Check whitelist first — if it's a physical product, skip
    for physical in PHYSICAL_PRODUCT_WHITELIST:
        if physical in lower:
            return False

    # Check for genuine software keywords
    padded = f" {lower} "
    for kw in SOFTWARE_KEYWORDS:
        if f" {kw} " in padded or padded.strip().endswith(kw):
            return True

    return False

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
    logger.info(f"Exact duplicates removed: {before - len(df)}")

    # 2. Resolve same product_category under multiple subcategories
    before = len(df)
    df['sub_len'] = df['subcategory'].str.len()
    df = df.sort_values('sub_len', ascending=False)
    df = df.drop_duplicates(subset=['category', 'product_category'], keep='first')
    df = df.drop(columns=['sub_len'])
    cross_dupes = before - len(df)
    logger.info(f"Cross-subcategory duplicates resolved: {cross_dupes}")

    # 3. Detect remaining multi-subcategory products (log only — do not auto move)
    multi_sub = df.groupby('product_category')['subcategory'].nunique()
    multi_sub_products = multi_sub[multi_sub > 1].index.tolist()
    if multi_sub_products:
        logger.warning(f"Products still in multiple subcategories: {len(multi_sub_products)}")
        for p in multi_sub_products[:20]:
            issues.append(f"MULTI_SUBCATEGORY: {p}")

    # 4. Detect genuinely misplaced software
    misplaced_mask = df.apply(
        lambda row: (
            row['category'] in NON_SOFTWARE_CATEGORIES and
            is_software(str(row['product_category']))
        ),
        axis=1
    )
    misplaced = df[misplaced_mask]
    if not misplaced.empty:
        logger.warning(f"Misplaced software products: {len(misplaced)}")
        for _, row in misplaced.iterrows():
            issues.append(
                f"MISPLACED_SOFTWARE: '{row['product_category']}' "
                f"under '{row['category']}'"
            )
        df.loc[misplaced_mask, 'category'] = 'Software & IT Solutions'
        logger.info(f"Auto-corrected {len(misplaced)} misplaced software products.")
    else:
        logger.info("No misplaced software products detected.")

    # 5. Drop empty rows
    df = df.dropna(subset=['category', 'subcategory', 'product_category'])
    df = df[df['product_category'].str.strip() != '']

    # 6. Sort
    df = df.sort_values(
        ['category', 'subcategory', 'product_category']
    ).reset_index(drop=True)

    final_count = len(df)
    set_metric('final_products', final_count)
    set_metric('validation_issues', len(issues))

    output_path = os.path.join(PHASE5_OUTPUT_DIR, 'final_taxonomy.csv')
    df.to_csv(output_path, index=False, encoding='utf-8')
    logger.info(f"Final taxonomy written: {output_path} ({final_count} rows)")

    if issues:
        issues_path = os.path.join(PHASE5_OUTPUT_DIR, 'validation_issues.txt')
        with open(issues_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(issues))
        logger.warning(f"Validation issues: {len(issues)} logged")
    else:
        logger.info("No validation issues found.")

    save_metrics()
    mark_completed('phase5')
    logger.info('Phase 5 complete.')

if __name__ == '__main__':
    run()
